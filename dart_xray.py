"""
DART X-RAY v1.0 — 한국 주식 공시 통합 분석 엔진
기업명 하나 넣으면 4가지 X-RAY가 한 번에 돌아갑니다.
"""
import requests
from datetime import datetime, timedelta

import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일 읽어들이기

API_KEY = os.environ.get('DART_API_KEY', '')
if not API_KEY:
    raise ValueError("DART_API_KEY 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
BASE = 'https://opendart.fss.or.kr/api'

# 작동 검증된 기업만 등록. 추가하려면 https://opendart.fss.or.kr 에서 corp_code 검색.
COMPANIES = {
    '삼성전자': '00126380',
    # 예시 추가: 'SK하이닉스': '00164779',
}

GOOD_KW = ['무상증자', '주식소각', '자기주식취득', '자사주취득',
           '현금ㆍ현물배당', '현금배당', '주식배당']
BAD_KW  = ['유상증자', '감자결정', '전환사채권', '신주인수권부사채',
           '횡령', '배임', '관리종목', '상장폐지', '거래정지']
EXCLUDE_POSITIONS = ['고문', '퇴임', '前', '미등기', '자문', '상담역', '상임고문', '비상근']


def _get(endpoint, params):
    params['crtfc_key'] = API_KEY
    try:
        r = requests.get(f'{BASE}/{endpoint}', params=params, timeout=10)
        return r.json()
    except Exception as e:
        return {'status': 'ERR', 'message': str(e)}


def _check_status(data):
    """DART 응답 상태를 사람이 읽을 수 있는 메시지로 변환"""
    s, m = data.get('status'), data.get('message', '')
    if s == '000':
        return None
    if s == '013':
        return "📭 해당 기간·조건에 데이터가 없습니다 (서버 변환 지연 가능, 1~2일 후 재시도)."
    if s == '020':
        return "🚫 일일 API 호출 한도 초과."
    return f"⚠️ DART 응답 오류 ({s}): {m}"


# ===== 모듈 1: 공시 스캔 =====
def scan_disclosures(corp_code, days=30):
    today = datetime.now()
    start = today - timedelta(days=days)
    data = _get('list.json', {
        'corp_code': corp_code,
        'bgn_de': start.strftime('%Y%m%d'),
        'end_de': today.strftime('%Y%m%d'),
        'page_count': '100',
    })

    print(f"\n🔍 [공시 스캔] 최근 {days}일")
    print("-" * 70)
    err = _check_status(data)
    if err:
        print(f"  {err}"); return

    total = len(data.get('list', []))
    hits = []
    for item in data['list']:
        nm = item['report_nm']
        tag = None
        for kw in BAD_KW:
            if kw in nm: tag = ('⚠️ 주의', kw); break
        if not tag:
            for kw in GOOD_KW:
                if kw in nm: tag = ('💰 호재', kw); break
        if tag:
            hits.append((item['rcept_dt'], tag[0], nm))

    print(f"  전체 {total}건 중 시그널 {len(hits)}건 포착")
    if not hits:
        print("  (조용한 기간이거나 days 값을 늘려보세요)")
    for dt, tag, title in hits[:20]:
        print(f"  {tag} [{dt}] {title}")


# ===== 모듈 2: 배당 분석 =====
def analyze_dividend(corp_code, year='2024', reprt='11011'):
    data = _get('alotMatter.json', {
        'corp_code': corp_code, 'bsns_year': year, 'reprt_code': reprt,
    })
    print(f"\n💰 [배당 분석] {year}년 사업보고서")
    print("-" * 70)
    err = _check_status(data)
    if err:
        print(f"  {err}"); return

    for item in data.get('list', []):
        cat = item.get('se', '')
        if '주당 현금배당금' in cat and '보통주' in item.get('stock_knd', ''):
            now, prev = item.get('thstrm', '-'), item.get('frmtrm', '-')
            print(f"  주당 현금배당금: 당기 {now}원 / 전기 {prev}원")
            try:
                n = float(str(now).replace(',', ''))
                p = float(str(prev).replace(',', ''))
                if p > 0:
                    yoy = (n - p) / p * 100
                    arrow = "📈" if yoy > 0 else ("📉" if yoy < 0 else "➖")
                    print(f"    └ 전년 대비: {arrow} {yoy:+.1f}%")
            except: pass
        if '현금배당성향' in cat:
            now, prev = item.get('thstrm', '-'), item.get('frmtrm', '-')
            print(f"  현금배당성향:   당기 {now}% / 전기 {prev}%")


# ===== 모듈 3: 임원 연봉 =====
def analyze_executive_pay(corp_code, year='2024', reprt='11011'):
    data = _get('indvdlByPay.json', {
        'corp_code': corp_code, 'bsns_year': year, 'reprt_code': reprt,
    })
    print(f"\n👔 [임원 보수] {year}년 · 5억원 이상 상위 5인")
    print("-" * 70)
    err = _check_status(data)
    if err:
        print(f"  {err}"); return

    rows = [x for x in data.get('list', [])
            if not any(k in x.get('ofcps', '') for k in EXCLUDE_POSITIONS)]
    if not rows:
        print("  현직 등기임원 데이터 없음 (고문·퇴임자만 공시됨).")
        return

    print(f"  ⚠️ '보수총액'에 퇴직금·스톡옵션 행사이익이 섞여있을 수 있습니다.")
    print(f"     정확한 내역은 사업보고서 원문 확인 필요.\n")
    for item in rows:
        nm, pos = item.get('nm', ''), item.get('ofcps', '')
        total = item.get('mendng_totamt', '0')
        excl = item.get('mendng_totamt_ct_incls_mendng', '-')
        try:
            total_fmt = f"{int(str(total).replace(',', '')):,}원"
        except:
            total_fmt = f"{total}원"
        print(f"  {nm} ({pos})")
        print(f"    보수총액:    {total_fmt}")
        if excl not in ['-', '0', '', None]:
            print(f"    총액 외 보수: {excl}원  ← 퇴직금 의심")


# ===== 모듈 4: 전환사채 이력 =====
def analyze_cb_history(corp_code, years=3):
    today = datetime.now()
    start = today.replace(year=today.year - years)
    data = _get('cvbdIsDecsn.json', {
        'corp_code': corp_code,
        'bgn_de': start.strftime('%Y%m%d'),
        'end_de': today.strftime('%Y%m%d'),
    })
    print(f"\n📜 [전환사채 이력] 최근 {years}년")
    print("-" * 70)
    err = _check_status(data)
    if err:
        print(f"  {err}"); return

    items = data.get('list', [])
    if not items:
        print("  발행 이력 없음 — 재무 자신감의 신호일 수 있습니다. ✨")
        return

    for item in items:
        oprt = str(item.get('oprt_fnd', '0')).strip().replace(',', '')
        facil = item.get('facil_fnd', '0')
        amt = item.get('chrtc_bnd_prncpl', '0')
        dt = item.get('rcept_dt', '')

        warn = ''
        try:
            if oprt and oprt not in ['0', '-'] and int(oprt) > 0:
                warn = '  🚨 운영자금 포함 (빚 갚기·급여 가능성)'
        except: pass

        print(f"  [{dt}] 발행액 {amt}원{warn}")
        print(f"    └ 시설자금 {facil}원 / 운영자금 {oprt}원")
        print(f"    └ 표면이자 {item.get('srfc_ir', '-')}% / 만기이자 {item.get('mrt_ir', '-')}%")


# ===== 통합 실행 =====
def run_xray(company_name):
    corp_code = COMPANIES.get(company_name)
    if not corp_code:
        print(f"❌ '{company_name}'은 등록되지 않았습니다.")
        print(f"   현재: {list(COMPANIES.keys())}")
        print(f"   추가하려면: opendart.fss.or.kr 에서 corp_code 검색 후 COMPANIES 딕셔너리에 추가")
        return

    print("=" * 70)
    print(f"🩻  DART X-RAY: [{company_name}] 통합 스캔")
    print("=" * 70)

    scan_disclosures(corp_code)
    analyze_dividend(corp_code)
    analyze_executive_pay(corp_code)
    analyze_cb_history(corp_code)

    print("\n" + "=" * 70)
    print("✅ 스캔 완료")
    print("=" * 70)


if __name__ == "__main__":
    run_xray('삼성전자')