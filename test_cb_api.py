"""
CB(전환사채) 발행결정 API 탐색 v3
- 최근 공시는 상세 API에 지연 반영되므로 기간 확장
- 기업당 더 넓은 기간으로 조회
"""
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

API_KEY = os.environ.get('DART_API_KEY', '')
BASE = 'https://opendart.fss.or.kr/api'


def find_recent_cb_issuers(days=90):
    """최근 N일간 CB 발행한 기업 리스트."""
    end = datetime.now().strftime('%Y%m%d')
    start = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

    url = f"{BASE}/list.json"
    params = {
        'crtfc_key': API_KEY,
        'bgn_de': start,
        'end_de': end,
        'pblntf_detail_ty': 'B001',
        'page_count': 50,  # 더 많이 가져옴
    }
    r = requests.get(url, params=params, timeout=10)
    return r.json().get('list', [])


def get_cb_details(corp_code, bgn_de, end_de):
    """특정 기업의 CB 상세 정보."""
    url = f"{BASE}/cvbdIsDecsn.json"
    params = {
        'crtfc_key': API_KEY,
        'corp_code': corp_code,
        'bgn_de': bgn_de,
        'end_de': end_de,
    }
    r = requests.get(url, params=params, timeout=10)
    return r.json()


def format_money(val):
    if not val or val == '-' or val == '':
        return '해당 없음'
    try:
        amount = int(str(val).replace(',', ''))
        if amount == 0:
            return '해당 없음'
        if amount >= 100_000_000:
            return f"{amount:,}원 ({amount/100_000_000:,.1f}억)"
        return f"{amount:,}원"
    except (ValueError, TypeError):
        return str(val)


def print_cb_info(cb):
    """CB 상세 정보를 보기 좋게 출력."""
    print(f"\n📋 핵심 정보:")
    print(f"   회사명      : {cb.get('corp_name')}")
    print(f"   사채 회차   : {cb.get('bd_tm')}")
    print(f"   발행총액    : {format_money(cb.get('bd_fta'))}")

    # 자금 목적별 금액을 딕셔너리로 정리
    purposes = {
        '시설자금': cb.get('fdpp_fclt'),
        '영업양수자금': cb.get('fdpp_bsninh'),
        '운영자금': cb.get('fdpp_op'),
        '채무상환자금': cb.get('fdpp_dtrp'),
        '타법인증권취득': cb.get('fdpp_ocsa'),
        '기타자금': cb.get('fdpp_etc'),
    }

    print(f"\n💰 자금조달 목적 (★핵심★):")
    total = 0
    for name, val in purposes.items():
        formatted = format_money(val)
        print(f"   {name:15s}: {formatted}")
        try:
            total += int(str(val).replace(',', '')) if val and val != '-' else 0
        except (ValueError, TypeError):
            pass

    if total > 0:
        print(f"\n   📊 합계: {total:,}원 ({total/100_000_000:,.1f}억)")
        # 운영자금 비중
        try:
            op = int(str(cb.get('fdpp_op', 0)).replace(',', '') or 0)
            if op > 0:
                op_ratio = (op / total) * 100
                print(f"   ⚠️ 운영자금 비중: {op_ratio:.1f}%")
        except:
            pass

    print(f"\n📊 전환 조건:")
    print(f"   표면이자율      : {cb.get('bd_intr_ex')}%")
    print(f"   만기이자율      : {cb.get('bd_intr_sf')}%")
    print(f"   전환가액        : {cb.get('cv_prc')}")
    print(f"   주식총수대비    : {cb.get('cvisstk_tisstk_vs')}%")


if __name__ == '__main__':
    print("=" * 70)
    print("🔍 최근 90일 CB 발행 기업 20건 조회")
    print("=" * 70)

    issuers = find_recent_cb_issuers(days=90)
    print(f"찾은 공시: {len(issuers)}건")

    # 가장 오래된 공시부터 (DART 상세 API 데이터가 있을 가능성 높음)
    issuers_reversed = list(reversed(issuers))

    print(f"\n오래된 순서로 테스트 시작 (최근 공시는 상세 API 지연 반영됨):\n")

    success = 0
    fail = 0

    for test in issuers_reversed[:10]:  # 10개까지 시도
        corp_name = test['corp_name']
        corp_code = test['corp_code']
        rcept_dt = test['rcept_dt']

        # 해당 공시 날짜 기준으로 앞뒤 30일씩 넓게
        d = datetime.strptime(rcept_dt, '%Y%m%d')
        start = (d - timedelta(days=30)).strftime('%Y%m%d')
        end = (d + timedelta(days=30)).strftime('%Y%m%d')

        details = get_cb_details(corp_code, start, end)
        status = details.get('status')

        if status == '000' and details.get('list'):
            success += 1
            print(f"\n{'=' * 70}")
            print(f"✅ [{success}] {corp_name} ({test['stock_code']}) — 접수 {rcept_dt}")
            print("=" * 70)
            print_cb_info(details['list'][0])

            if success >= 3:  # 3건 성공하면 중단
                break
        else:
            fail += 1
            print(f"❌ {corp_name} - {status}: {details.get('message', '')}")

    print(f"\n\n{'=' * 70}")
    print(f"최종: 성공 {success}건 / 실패 {fail}건 / 총 시도 {success + fail}건")
    print("=" * 70)