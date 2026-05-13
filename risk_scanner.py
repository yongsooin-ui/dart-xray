"""
DART X-RAY 위험 공시 스캐너
- 최근 24시간 전체 공시를 분석해 가장 위험한 TOP 5 추출
- 메모리 캐싱으로 부하 최소화 (10분 TTL)
"""
from datetime import datetime, timedelta
import time
import dart_xray as engine
from disclosure_analyzer import analyze_disclosure


# ============================================================
# 메모리 캐시 (10분 TTL)
# ============================================================
_cache = {
    'data': None,
    'expires_at': 0,
}
_CACHE_TTL_SECONDS = 600  # 10분


def get_top_risk_disclosures(companies_listed, limit=5):
    """
    최근 24시간 위험 공시 TOP N 반환.
    
    Args:
        companies_listed: 상장사 리스트 (corp_code → corp_name 매핑용)
        limit: 반환할 개수 (기본 5개)
    
    Returns:
        list: 위험 공시 dict 리스트 (점수 낮은 순)
    """
    # 캐시 확인
    now = time.time()
    if _cache['data'] is not None and now < _cache['expires_at']:
        return _cache['data'][:limit]
    
    # 캐시 만료 또는 첫 호출 → 새로 분석
    print("🚨 [위험 공시 스캐너] 분석 시작...")
    start_time = time.time()
    
    try:
        results = _fetch_and_analyze(companies_listed)
        _cache['data'] = results
        _cache['expires_at'] = now + _CACHE_TTL_SECONDS
        
        elapsed = time.time() - start_time
        print(f"   ✅ 완료: {len(results)}건 발견 ({elapsed:.1f}초)")
        
        return results[:limit]
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        # 실패해도 빈 리스트 반환 (메인 페이지는 계속 작동해야 함)
        return []


def _fetch_and_analyze(companies_listed):
    """DART API에서 최근 24시간 공시 가져와서 분석."""
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    # corp_code → 회사 정보 빠른 조회용 dict
    corp_lookup = {c['corp_code']: c for c in companies_listed}
    
    # DART API 호출: corp_code 없이 호출하면 전체 공시 가능
    all_disclosures = []
    
    # 페이지네이션으로 모든 공시 수집 (page_count=100, 여러 페이지)
    for page in range(1, 6):  # 최대 5페이지 (500건)
        try:
            response = engine._get('list.json', {
                'bgn_de': yesterday.strftime('%Y%m%d'),
                'end_de': today.strftime('%Y%m%d'),
                'page_count': '100',
                'page_no': str(page),
            })
            
            if response.get('status') != '000':
                break
            
            items = response.get('list', [])
            if not items:
                break
            
            all_disclosures.extend(items)
            
            # 마지막 페이지면 중단
            total_page = response.get('total_page', 1)
            if page >= total_page:
                break
                
        except Exception as e:
            print(f"   [페이지 {page} 오류] {e}")
            break
    
    # 분석 및 필터링
    risk_signals = []
    
    for item in all_disclosures:
        nm = item.get('report_nm', '')
        corp_code = item.get('corp_code', '')
        corp_name = item.get('corp_name', '') or '-'
        rcept_no = item.get('rcept_no', '')
        rcept_dt = item.get('rcept_dt', '')
        
        # 상장사 여부 확인 (corp_lookup에 있어야 함)
        corp_info = corp_lookup.get(corp_code)
        if not corp_info or not corp_info.get('stock_code'):
            continue  # 비상장 또는 상장폐지된 종목 제외
        
        # 공시 분석
        analysis = analyze_disclosure(nm)
        
        # 악재만 필터 (점수 ≤ -2)
        if analysis['score'] > -2:
            continue
        
        # 시간 정보 (몇 시간 전)
        time_ago = _calculate_time_ago(rcept_dt, item.get('rcept_no', ''))
        
        risk_signals.append({
            'corp_name': corp_name,
            'corp_code': corp_code,
            'stock_code': corp_info.get('stock_code', ''),
            'title': nm,
            'rule_title': analysis['rule_title'],
            'score': analysis['score'],
            'score_label': analysis['score_label'],
            'score_emoji': analysis['score_emoji'],
            'explain': analysis['explain'],
            'rcept_dt': rcept_dt,
            'time_ago': time_ago,
            'dart_url': f'https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}' if rcept_no else '',
        })
    
    # 점수 낮은 순으로 정렬 (가장 위험한 것이 앞)
    risk_signals.sort(key=lambda x: x['score'])
    
    return risk_signals


def _calculate_time_ago(rcept_dt, rcept_no):
    """공시 접수일 + 접수번호로 대략적 'N시간 전' 계산."""
    try:
        if not rcept_dt or len(rcept_dt) != 8:
            return ''
        
        # rcept_dt: 'YYYYMMDD'
        year = int(rcept_dt[:4])
        month = int(rcept_dt[4:6])
        day = int(rcept_dt[6:8])
        disclosure_date = datetime(year, month, day)
        
        now = datetime.now()
        diff = now - disclosure_date
        
        hours = int(diff.total_seconds() / 3600)
        
        if hours < 1:
            return '방금 전'
        elif hours < 24:
            return f'{hours}시간 전'
        elif hours < 48:
            return '어제'
        else:
            days = hours // 24
            return f'{days}일 전'
    except Exception:
        return ''


def clear_cache():
    """캐시 강제 초기화 (디버깅용)."""
    _cache['data'] = None
    _cache['expires_at'] = 0
    print("🔄 위험 공시 캐시 초기화됨")


# ============================================================
# 직접 실행 시 테스트
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("🚨 위험 공시 스캐너 테스트")
    print("=" * 60)
    
    # app.py와 동일한 방식으로 corp_list 로드
    import json
    import os
    
    CACHE_FILE = 'corp_list.json'
    if not os.path.exists(CACHE_FILE):
        print(f"❌ {CACHE_FILE} 없음. 먼저 app.py를 한 번 실행하세요.")
        exit()
    
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        companies_all = json.load(f)
    
    companies_listed = [c for c in companies_all if c['stock_code']]
    print(f"📚 상장사 {len(companies_listed):,}개 로드됨")
    
    # 위험 공시 TOP 5 가져오기
    risks = get_top_risk_disclosures(companies_listed, limit=5)
    
    print(f"\n📊 TOP {len(risks)} 위험 공시:")
    print("=" * 60)
    
    for i, r in enumerate(risks, 1):
        print(f"\n{i}. {r['score_emoji']} {r['score']}점 [{r['score_label']}]")
        print(f"   {r['corp_name']} ({r['stock_code']})")
        print(f"   {r['rule_title']}")
        print(f"   원본: {r['title']}")
        print(f"   {r['time_ago']}")
        print(f"   💡 {r['explain']}")