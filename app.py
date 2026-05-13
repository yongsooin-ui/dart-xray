from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
from urllib.parse import quote
import requests, zipfile, io, json, os
import xml.etree.ElementTree as ET
import dart_xray as engine
from disclosure_analyzer import analyze_disclosure, aggregate_score, analyze_cb_with_purposes, analyze_treasury_with_market_cap, _score_label, _score_emoji
from stock_info import get_stock_info, get_chart_data
from risk_scanner import get_top_risk_disclosures
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


def collect_analysis(corp_code, display_name, stock=None):
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

            cb_analysis = None
            if '전환사채' in nm or 'CB' in nm.upper():
                try:
                    cb_data = engine.get_cb_details_data(corp_code, item['rcept_dt'])
                    if cb_data:
                        cb_info = engine.parse_cb_purposes(cb_data)
                        if cb_info:
                            cb_analysis = analyze_cb_with_purposes(cb_info)
                            analysis['score'] += cb_analysis['score_adjust']
                            analysis['score'] = max(-10, min(10, analysis['score']))
                            analysis['score_label'] = _score_label(analysis['score'])
                            analysis['score_emoji'] = _score_emoji(analysis['score'])
                            if analysis['score'] <= -4:
                                analysis['category'] = 'bad'
                except Exception as e:
                    print(f"[CB 심층분석 오류] {e}")

            treasury_analysis = None
            is_disposal = '자기주식처분' in nm or '자사주처분' in nm
            is_acquisition = '자기주식취득' in nm or '자사주취득' in nm

            if (is_disposal or is_acquisition) and stock and stock.get('market_cap_eok'):
                try:
                    if is_disposal:
                        t_data = engine.get_treasury_disposal_data(corp_code, item['rcept_dt'])
                        t_info = engine.parse_treasury_data(t_data, action='disposal') if t_data else None
                    else:
                        t_data = engine.get_treasury_acquisition_data(corp_code, item['rcept_dt'])
                        t_info = engine.parse_treasury_data(t_data, action='acquisition') if t_data else None

                    if t_info:
                        treasury_analysis = analyze_treasury_with_market_cap(
                            t_info, stock['market_cap_eok'] * 100_000_000
                        )
                        if treasury_analysis:
                            analysis['score'] = treasury_analysis['final_score']
                            analysis['score_label'] = _score_label(analysis['score'])
                            analysis['score_emoji'] = _score_emoji(analysis['score'])
                            if analysis['score'] >= 1:
                                analysis['category'] = 'good'
                            elif analysis['score'] <= -1:
                                analysis['category'] = 'bad'
                            else:
                                analysis['category'] = 'neutral'
                except Exception as e:
                    print(f"[자사주 시총분석 오류] {e}")

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
                'treasury_analysis': treasury_analysis,
            }

            if analysis['category'] in ('good', 'bad'):
                signals.append(signal_data)

            if analysis['category'] == 'good':
                signals_good.append(signal_data)
            elif analysis['category'] == 'bad':
                signals_bad.append(signal_data)
            else:
                signals_neutral.append(signal_data)

    dividends = {
        'year': '-',
        'per_share_now': '-',
        'per_share_prev': '-',
        'payout_now': '-',
        'payout_prev': '-',
        'yoy': None,
        'per_share_now_int': 0,
        'amount_per_100': '-',
        'yield_pct': None,
    }

    latest_year = engine.get_latest_dividend_year(corp_code)
    if latest_year:
        dividends['year'] = latest_year
        div = engine._get('alotMatter.json', {
            'corp_code': corp_code, 'bsns_year': latest_year, 'reprt_code': '11011',
        })
        if div.get('status') == '000':
            for item in div.get('list', []):
                cat = item.get('se', '')
                if '주당 현금배당금' in cat and '보통주' in item.get('stock_knd', ''):
                    dividends['per_share_now'] = item.get('thstrm', '-')
                    dividends['per_share_prev'] = item.get('frmtrm', '-')
                    try:
                        n = float(str(dividends['per_share_now']).replace(',', ''))
                        p = float(str(dividends['per_share_prev']).replace(',', ''))
                        dividends['per_share_now_int'] = int(n)
                        if p > 0:
                            dividends['yoy'] = round((n - p) / p * 100, 1)

                        if n > 0:
                            amount = int(n * 100)
                            dividends['amount_per_100'] = f"{amount:,}원"

                        if n > 0 and stock and stock.get('price'):
                            yield_pct = round(n / stock['price'] * 100, 2)
                            dividends['yield_pct'] = yield_pct
                    except (ValueError, TypeError):
                        pass
                if '현금배당성향' in cat:
                    dividends['payout_now'] = item.get('thstrm', '-')
                    dividends['payout_prev'] = item.get('frmtrm', '-')

    pay = engine._get('indvdlByPay.json', {
        'corp_code': corp_code, 'bsns_year': latest_year or '2024', 'reprt_code': '11011',
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
            rcept_no = item.get('rcept_no', '')
            date = rcept_no[:8] if len(rcept_no) >= 8 else ''
            if len(date) == 8:
                date = f"{date[:4]}.{date[4:6]}.{date[6:8]}"

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


def _run_analysis(query):
    """공통 분석 실행 함수 (POST/GET 둘 다에서 사용)"""
    query = (query or '').strip()
    if not query:
        return None

    corp_code, display_name, stock_code = resolve_corp_code(query)
    if not corp_code:
        return {
            'error': f"'{query}'에 해당하는 상장기업을 찾을 수 없습니다.",
            'query': query,
        }

    stock = get_stock_info(stock_code) if stock_code else None

    result = collect_analysis(corp_code, display_name, stock=stock)
    result['stock'] = stock
    result['stock_code'] = stock_code
    result['query'] = query
    result['share_url_param'] = quote(display_name)

    # 주가 차트 데이터 (실패해도 계속)
    if stock_code:
        try:
            result['chart'] = get_chart_data(stock_code, days=20)
        except Exception as e:
            print(f"[차트 수집 오류] {e}")
            result['chart'] = None
    else:
        result['chart'] = None

    return result


@app.route('/')
def home():
    q = request.args.get('q', '').strip()
    if q:
        result = _run_analysis(q)
        return render_template('index.html', result=result, prefill_query=q)
    
    # 메인 페이지: 위험 공시 TOP 5 (캐싱됨, 10분 TTL)
    try:
        risk_disclosures = get_top_risk_disclosures(COMPANIES_LISTED, limit=5)
    except Exception as e:
        print(f"[메인 페이지 위험 공시 로딩 오류] {e}")
        risk_disclosures = []
    
    # 공유용 OG 카드 정보 (메인 페이지)
    share_info = {
        'is_home': True,
        'top_companies': [r['corp_name'] for r in risk_disclosures[:3]] if risk_disclosures else [],
        'total_count': len(risk_disclosures),
    }
    
    return render_template('index.html', result=None, risk_disclosures=risk_disclosures, share_info=share_info)


@app.route('/search')
def search():
    q = request.args.get('q', '')
    results = search_companies(q)
    return jsonify(results)


@app.route('/analyze', methods=['POST'])
def analyze():
    """폼 제출 시: GET 방식의 공유 URL로 리다이렉트 (POST → GET)"""
    query = request.form.get('company', '').strip()
    if not query:
        return redirect(url_for('home'))
    return redirect(url_for('home', q=query))


if __name__ == '__main__':
    app.run(debug=True, port=5001)