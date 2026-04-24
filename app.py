from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import requests, zipfile, io, json, os
import xml.etree.ElementTree as ET
import dart_xray as engine
from disclosure_analyzer import analyze_disclosure, aggregate_score, analyze_cb_with_purposes, _score_label, _score_emoji
from stock_info import get_stock_info
app = Flask(__name__)
CACHE_FILE = 'corp_list.json'


def load_corp_list():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    print("📥 DART 전체 기업 목록 다운로드 중...")
    url = 'https://opendart.fss.or.kr/api/corpCode.xml'
    r = requests.get(url, params={'crtfc_key': engine.API_KEY}, timeout=30)

    z = zipfile.ZipFile(io.BytesIO(r.content))
    xml_data = z.read('CORPCODE.xml').decode('utf-8')

    root = ET.fromstring(xml_data)
    companies = []
    for item in root.findall('list'):
        corp_code = (item.findtext('corp_code') or '').strip()
        corp_name = (item.findtext('corp_name') or '').strip()
        stock_code = (item.findtext('stock_code') or '').strip()
        if corp_code and corp_name:
            companies.append({
                'corp_code': corp_code,
                'corp_name': corp_name,
                'stock_code': stock_code,
            })

    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(companies, f, ensure_ascii=False)
    return companies


print("📚 기업 목록 초기화 중...")
COMPANIES_ALL = load_corp_list()
COMPANIES_LISTED = [c for c in COMPANIES_ALL if c['stock_code']]
print(f"   전체 {len(COMPANIES_ALL):,}개 / 상장 {len(COMPANIES_LISTED):,}개")

# 한글 → 영문/공식명 별칭 매핑 (사용자 편의)
ALIASES = {
    '네이버': 'NAVER',
    '엘지전자': 'LG전자',
    '엘지화학': 'LG화학',
    '엘지에너지솔루션': 'LG에너지솔루션',
    '엘지디스플레이': 'LG디스플레이',
    '엘지생활건강': 'LG생활건강',
    '엘지이노텍': 'LG이노텍',
    '엘지유플러스': 'LG유플러스',
    '에스케이': 'SK',
    '에스케이하이닉스': 'SK하이닉스',
    '에스케이텔레콤': 'SK텔레콤',
    '에스케이이노베이션': 'SK이노베이션',
    '에스케이바이오팜': 'SK바이오팜',
    '에스케이아이이테크놀로지': 'SKIET',
    '케이티': 'KT',
    '케이티앤지': 'KT&G',
    '케이비금융': 'KB금융',
    '에이치디한국조선해양': 'HD한국조선해양',
    '에이치디현대': 'HD현대',
    '현대차': '현대자동차',
    '기아차': '기아',
    '디비금융': 'DB금융투자',
    '씨제이': 'CJ',
    '씨제이제일제당': 'CJ제일제당',
    '씨제이대한통운': 'CJ대한통운',
    '씨제이이엔엠': 'CJ ENM',
    '한국전력': '한국전력공사',
    '한전': '한국전력공사',
    '포스코': 'POSCO',
    '포스코홀딩스': 'POSCO홀딩스',
    '포스코퓨처엠': 'POSCO퓨처엠',
    '지에스': 'GS',
    '지에스건설': 'GS건설',
    '지에스리테일': 'GS리테일',
    '지에스칼텍스': 'GS칼텍스',
    '엔씨': '엔씨소프트',
    '카카오뱅크': '카카오뱅크',
    '크래프톤': '크래프톤',
    '하이브': '하이브',
    '에이치엘비': 'HLB',
    '에이치엠엠': 'HMM',
    '두산밥캣': '두산밥캣',
    '한미약품': '한미약품',
}

def search_companies(query, limit=15):
    q = query.strip()
    if not q:
        return []

    # 별칭 치환: 사용자 입력이 별칭이면 실제 기업명으로 변환
    if q in ALIASES:
        q = ALIASES[q]

    q_lower = q.lower()
    exact, prefix, contains = [], [], []

    for c in COMPANIES_LISTED:
        name_lower = c['corp_name'].lower()

        if q.isdigit() and (c['stock_code'] == q or c['corp_code'] == q):
            exact.append(c)
            continue
        if name_lower == q_lower:
            exact.append(c)
            continue
        if name_lower.startswith(q_lower):
            prefix.append(c)
            continue
        if q_lower in name_lower:
            contains.append(c)
            continue
        if q.isdigit() and c['stock_code'].startswith(q):
            prefix.append(c)

    return (exact + prefix + contains)[:limit]


def resolve_corp_code(query):
    results = search_companies(query, limit=1)
    if results:
        return results[0]['corp_code'], results[0]['corp_name'], results[0].get('stock_code', '')
    return None, None, None


def collect_analysis(corp_code, display_name):
    today = datetime.now()
    start = today - timedelta(days=30)

    disc = engine._get('list.json', {
        'corp_code': corp_code,
        'bgn_de': start.strftime('%Y%m%d'),
        'end_de': today.strftime('%Y%m%d'),
        'page_count': '100',
    })
    signals = []
    signals_good, signals_bad, signals_neutral = [], [], []
    if disc.get('status') == '000':
        for item in disc.get('list', []):
            nm = item['report_nm']
            analysis = analyze_disclosure(nm)
            rcept_no = item.get('rcept_no', '')

            # CB(전환사채) 공시인 경우 자금목적 심층 분석
            cb_analysis = None
            if '전환사채' in nm or 'CB' in nm.upper():
                try:
                    cb_data = engine.get_cb_details_data(corp_code, item['rcept_dt'])
                    if cb_data:
                        cb_info = engine.parse_cb_purposes(cb_data)
                        if cb_info:
                            cb_analysis = analyze_cb_with_purposes(cb_info)
                            # 기본 CB 점수에 자금목적 보정 반영
                            analysis['score'] += cb_analysis['score_adjust']
                            analysis['score'] = max(-10, min(10, analysis['score']))
                            # 라벨·이모지 재계산
                            analysis['score_label'] = _score_label(analysis['score'])
                            analysis['score_emoji'] = _score_emoji(analysis['score'])
                            # 카테고리 재결정 (강한 악재로 떨어질 수 있음)
                            if analysis['score'] <= -4:
                                analysis['category'] = 'bad'
                except Exception as e:
                    print(f"[CB 심층분석 오류] {e}")

            signal_data = {
                'date': item['rcept_dt'],
                'title': nm,
                'rule_title': analysis['rule_title'],
                'score': analysis['score'],
                'score_label': analysis['score_label'],
                'score_emoji': analysis['score_emoji'],
                'explain': analysis['explain'],
                'tag': '💰 호재' if analysis['category'] == 'good' else ('⚠️ 주의' if analysis['category'] == 'bad' else '📋 일반'),
                'dart_url': f'https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}' if rcept_no else '',
                'cb_analysis': cb_analysis,
            }

            if analysis['category'] in ('good', 'bad'):
                signals.append(signal_data)

            if analysis['category'] == 'good':
                signals_good.append(signal_data)
            elif analysis['category'] == 'bad':
                signals_bad.append(signal_data)
            else:
                signals_neutral.append(signal_data)

    div = engine._get('alotMatter.json', {
        'corp_code': corp_code, 'bsns_year': '2024', 'reprt_code': '11011',
    })
    dividends = {'per_share_now': '-', 'per_share_prev': '-',
                 'payout_now': '-', 'payout_prev': '-', 'yoy': None}
    if div.get('status') == '000':
        for item in div.get('list', []):
            cat = item.get('se', '')
            if '주당 현금배당금' in cat and '보통주' in item.get('stock_knd', ''):
                dividends['per_share_now'] = item.get('thstrm', '-')
                dividends['per_share_prev'] = item.get('frmtrm', '-')
                try:
                    n = float(str(dividends['per_share_now']).replace(',', ''))
                    p = float(str(dividends['per_share_prev']).replace(',', ''))
                    if p > 0:
                        dividends['yoy'] = round((n - p) / p * 100, 1)
                except:
                    pass
            if '현금배당성향' in cat:
                dividends['payout_now'] = item.get('thstrm', '-')
                dividends['payout_prev'] = item.get('frmtrm', '-')

    pay = engine._get('indvdlByPay.json', {
        'corp_code': corp_code, 'bsns_year': '2024', 'reprt_code': '11011',
    })
    executives = []
    if pay.get('status') == '000':
        for item in pay.get('list', []):
            pos = item.get('ofcps', '')
            if any(k in pos for k in engine.EXCLUDE_POSITIONS):
                continue
            try:
                total_fmt = f"{int(str(item.get('mendng_totamt', '0')).replace(',', '')):,}"
            except:
                total_fmt = item.get('mendng_totamt', '-')
            executives.append({
                'name': item.get('nm', ''),
                'position': pos,
                'total': total_fmt,
                'excluded': item.get('mendng_totamt_ct_incls_mendng', '-'),
            })

    cb_start = today.replace(year=today.year - 3)
    cb = engine._get('cvbdIsDecsn.json', {
        'corp_code': corp_code,
        'bgn_de': cb_start.strftime('%Y%m%d'),
        'end_de': today.strftime('%Y%m%d'),
    })
    cbs, cb_none = [], False
    if cb.get('status') == '000':
        items = cb.get('list', [])
        

        for item in items:
            # 접수번호 앞 8자 = 접수일 (YYYYMMDD → YYYY.MM.DD)
            rcept_no = item.get('rcept_no', '')
            date = rcept_no[:8] if len(rcept_no) >= 8 else ''
            if len(date) == 8:
                date = f"{date[:4]}.{date[4:6]}.{date[6:8]}"

            # 숫자 깔끔하게 (억/만 단위)
            def fmt_won(v):
                try:
                    s = str(v).replace(',', '').strip()
                    if not s or s in ['-', 'N/A']:
                        return '0'
                    n = int(s)
                    if n == 0: return '0'
                    if n >= 100_000_000: return f"{n/100_000_000:.1f}억"
                    if n >= 10_000: return f"{n/10_000:,.0f}만"
                    return f"{n:,}"
                except:
                    return '0'

            oprt_raw = str(item.get('fdpp_op', '0')).strip().replace(',', '')
            warn = False
            try:
                if oprt_raw and oprt_raw not in ['0', '-'] and int(oprt_raw) > 0:
                    warn = True
            except:
                pass

            cbs.append({
                'date': date,
                'amount': fmt_won(item.get('bd_fta', '0')),
                'facil': fmt_won(item.get('fdpp_fclt', '0')),
                'oprt': fmt_won(oprt_raw),
                'warn': warn,
            })
        if not cbs:
            cb_none = True
        elif cb.get('status') == '013':
            cb_none = True

    # 종합 점수 계산
        all_signals = signals_good + signals_bad + signals_neutral
        summary = aggregate_score(all_signals)

        return {
            'company': display_name,
            'signals': signals,
            'signals_good': signals_good,
            'signals_bad': signals_bad,
            'signals_neutral': signals_neutral,
            'summary': summary,
            'dividends': dividends,
            'executives': executives,
            'cbs': cbs,
            'cb_none': cb_none,
        }


@app.route('/')
def home():
    return render_template('index.html', result=None)


@app.route('/search')
def search():
    q = request.args.get('q', '')
    results = search_companies(q)
    return jsonify(results)


@app.route('/analyze', methods=['POST'])
def analyze():
    query = request.form.get('company', '').strip()
    if not query:
        return render_template('index.html', result=None)

    corp_code, display_name, stock_code = resolve_corp_code(query)
    if not corp_code:
        return render_template('index.html', result={
            'error': f"'{query}'에 해당하는 상장기업을 찾을 수 없습니다."
        })

    # Yahoo Finance에서 주가 정보 조회 (실패해도 분석은 계속 진행)
    stock = get_stock_info(stock_code) if stock_code else None

    result = collect_analysis(corp_code, display_name)
    result['stock'] = stock
    result['stock_code'] = stock_code

    return render_template('index.html', result=result)


if __name__ == '__main__':
    app.run(debug=True, port=5001)