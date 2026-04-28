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


# ==========================================
# 웹앱용 CB 상세 조회 & 자금목적 분석 함수
# (analyze_cb_history와 달리 값을 반환함)
# ==========================================

def get_cb_details_data(corp_code, around_date, days_buffer=15):
    """
    특정 기업의 CB(전환사채) 상세 정보를 조회합니다.

    Args:
        corp_code: 8자리 기업 고유번호
        around_date: 공시 접수일 (YYYYMMDD 문자열)
        days_buffer: 접수일 기준 앞뒤 며칠 범위로 조회할지

    Returns:
        dict or None: CB 상세 정보 (없으면 None)
    """
    try:
        d = datetime.strptime(around_date, '%Y%m%d')
        bgn = (d - timedelta(days=days_buffer)).strftime('%Y%m%d')
        end = (d + timedelta(days=days_buffer)).strftime('%Y%m%d')

        data = _get('cvbdIsDecsn.json', {
            'corp_code': corp_code,
            'bgn_de': bgn,
            'end_de': end,
        })

        if data.get('status') == '000' and data.get('list'):
            return data['list'][0]  # 가장 최근 것
        return None
    except Exception as e:
        print(f"[CB API 오류] {e}")
        return None


def parse_cb_purposes(cb_data):
    """
    CB 상세 정보에서 자금목적을 추출·분석합니다.

    Returns:
        dict: {
            'total_eok': 총액(억),
            'purposes': {'시설자금': 금액, ...},
            'ratios': {'시설자금': 비율%, ...},
            'primary_purpose': 가장 비중 큰 목적,
            'operating_ratio': 운영자금 비중(%),
            'debt_repay_ratio': 채무상환 비중(%),
            'facility_ratio': 시설자금 비중(%),
            'dilution_ratio': 주식총수 대비 희석률(%),
            'interest_face': 표면이자율,
            'interest_mature': 만기이자율,
        }
    """
    if not cb_data:
        return None

    def to_int(val):
        if not val or val == '-':
            return 0
        try:
            return int(str(val).replace(',', ''))
        except (ValueError, TypeError):
            return 0

    purposes = {
        '시설자금': to_int(cb_data.get('fdpp_fclt')),
        '영업양수자금': to_int(cb_data.get('fdpp_bsninh')),
        '운영자금': to_int(cb_data.get('fdpp_op')),
        '채무상환자금': to_int(cb_data.get('fdpp_dtrp')),
        '타법인증권취득': to_int(cb_data.get('fdpp_ocsa')),
        '기타자금': to_int(cb_data.get('fdpp_etc')),
    }

    total = sum(purposes.values())
    if total == 0:
        return None  # 데이터 이상

    ratios = {k: round(v / total * 100, 1) for k, v in purposes.items()}
    primary = max(purposes.items(), key=lambda x: x[1])[0]

    # 희석률 (주식총수 대비 전환 비율)
    dilution_str = cb_data.get('cvisstk_tisstk_vs', '0')
    try:
        dilution = float(str(dilution_str).replace(',', '').replace('%', ''))
    except (ValueError, TypeError):
        dilution = 0.0

    return {
        'total': total,
        'total_eok': round(total / 100_000_000, 1),
        'purposes': purposes,
        'ratios': ratios,
        'primary_purpose': primary,
        'operating_ratio': ratios['운영자금'],
        'debt_repay_ratio': ratios['채무상환자금'],
        'facility_ratio': ratios['시설자금'],
        'dilution_ratio': dilution,
        'interest_face': cb_data.get('bd_intr_ex', ''),
        'interest_mature': cb_data.get('bd_intr_sf', ''),
    }

# ==========================================
# 웹앱용 자사주 (처분/취득) 상세 조회 & 시총 대비 분석
# ==========================================

def get_treasury_disposal_data(corp_code, around_date, days_buffer=15):
    """
    자기주식 처분결정 상세 정보 조회.

    Args:
        corp_code: 8자리 기업 고유번호
        around_date: 공시 접수일 (YYYYMMDD 문자열)
        days_buffer: 접수일 기준 앞뒤 며칠 범위로 조회

    Returns:
        dict or None: 처분 상세 정보
    """
    try:
        d = datetime.strptime(around_date, '%Y%m%d')
        bgn = (d - timedelta(days=days_buffer)).strftime('%Y%m%d')
        end = (d + timedelta(days=days_buffer)).strftime('%Y%m%d')

        data = _get('tsstkDpDecsn.json', {
            'corp_code': corp_code,
            'bgn_de': bgn,
            'end_de': end,
        })

        if data.get('status') == '000' and data.get('list'):
            return data['list'][0]
        return None
    except Exception as e:
        print(f"[자사주 처분 API 오류] {e}")
        return None


def get_treasury_acquisition_data(corp_code, around_date, days_buffer=15):
    """
    자기주식 취득결정 상세 정보 조회.

    Returns:
        dict or None: 취득 상세 정보
    """
    try:
        d = datetime.strptime(around_date, '%Y%m%d')
        bgn = (d - timedelta(days=days_buffer)).strftime('%Y%m%d')
        end = (d + timedelta(days=days_buffer)).strftime('%Y%m%d')

        data = _get('tsstkAqDecsn.json', {
            'corp_code': corp_code,
            'bgn_de': bgn,
            'end_de': end,
        })

        if data.get('status') == '000' and data.get('list'):
            return data['list'][0]
        return None
    except Exception as e:
        print(f"[자사주 취득 API 오류] {e}")
        return None


def parse_treasury_data(treasury_data, action='disposal'):
    """
    자사주 공시 데이터에서 핵심 정보 추출.

    Args:
        treasury_data: get_treasury_disposal_data / get_treasury_acquisition_data 반환값
        action: 'disposal'(처분) 또는 'acquisition'(취득)

    Returns:
        dict: {
            'shares': 대상 주식 수,
            'price_per_share': 주당 단가,
            'total_amount': 총액(원),
            'total_eok': 총액(억원),
            'purpose': 목적/사유 텍스트,
            'period_start': 시작일,
            'period_end': 종료일,
            'action': 'disposal' 또는 'acquisition',
        }
    """
    if not treasury_data:
        return None

    def to_int(val):
        if not val or val == '-':
            return 0
        try:
            return int(str(val).replace(',', ''))
        except (ValueError, TypeError):
            return 0

    if action == 'disposal':
        # 자사주 처분 필드
        shares = to_int(treasury_data.get('dppln_stk_ostk'))
        price_per_share = to_int(treasury_data.get('dpstk_prc_ostk'))
        total_amount = to_int(treasury_data.get('dppln_prc_ostk'))
        purpose = treasury_data.get('dp_pp', '').strip() or '명시되지 않음'
        period_start = treasury_data.get('dpprpd_bgd', '')
        period_end = treasury_data.get('dpprpd_edd', '')
    else:
        # 자사주 취득 필드 (취득은 보통 aqpln_stk_ostk, aqpln_prc_ostk 같은 패턴)
        shares = to_int(treasury_data.get('aqpln_stk_ostk'))
        price_per_share = to_int(treasury_data.get('aqstk_prc_ostk'))
        total_amount = to_int(treasury_data.get('aqpln_prc_ostk'))
        purpose = treasury_data.get('aq_pp', '').strip() or '명시되지 않음'
        period_start = treasury_data.get('aqprpd_bgd', '')
        period_end = treasury_data.get('aqprpd_edd', '')

    if total_amount == 0:
        return None

    return {
        'shares': shares,
        'price_per_share': price_per_share,
        'total_amount': total_amount,
        'total_eok': round(total_amount / 100_000_000, 1),
        'purpose': purpose,
        'period_start': period_start,
        'period_end': period_end,
        'action': action,
    }
def get_share_count(corp_code, year='2024', reprt='11011'):
    """
    DART에서 발행주식 총수를 조회합니다.
    시가총액 계산용 (yfinance 시총 데이터가 불안정한 경우 대체).

    Args:
        corp_code: 8자리 기업 고유번호
        year: 사업연도 (기본 2024)
        reprt: 보고서 코드 (11011=사업보고서, 11013=1분기, 11012=반기, 11014=3분기)

    Returns:
        dict or None: {
            'total_shares': 발행주식 총수 (보통주),
            'treasury_shares': 자기주식 수,
            'circulating_shares': 유통주식수,
            'report_date': 기준일 (YYYY-MM-DD),
        }
    """
    try:
        data = _get('stkrtbskDecsn.json' if False else 'stockTotqySttus.json', {
            'corp_code': corp_code,
            'bsns_year': year,
            'reprt_code': reprt,
        })

        if data.get('status') != '000':
            return None

        items = data.get('list', [])
        if not items:
            return None

        # 보통주 항목 찾기
        common_stock = None
        for item in items:
            se = item.get('se', '')
            if '보통주' in se:
                common_stock = item
                break

        if not common_stock:
            return None

        def to_int(v):
            if not v or v == '-':
                return 0
            try:
                return int(str(v).replace(',', ''))
            except (ValueError, TypeError):
                return 0

        total = to_int(common_stock.get('istc_totqy'))
        treasury = to_int(common_stock.get('tesstk_co'))
        circulating = to_int(common_stock.get('distb_stock_co'))

        if total == 0:
            return None

        return {
            'total_shares': total,
            'treasury_shares': treasury,
            'circulating_shares': circulating,
            'report_date': common_stock.get('stlm_dt', ''),
        }
    except Exception as e:
        print(f"[발행주식수 조회 오류] {e}")
        return None
if __name__ == "__main__":
    run_xray('삼성전자')