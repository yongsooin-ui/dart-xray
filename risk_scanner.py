"""
DART X-RAY 위험/호재 공시 스캐너
- 최근 24시간 전체 공시를 분석해 위험/호재 TOP N 추출
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
    'risk_data': None,
    'good_data': None,
    'all_signals': None,
    'expires_at': 0,
}
_CACHE_TTL_SECONDS = 600  # 10분


def get_top_risk_disclosures(companies_listed, limit=5):
    """최근 24시간 위험 공시 TOP N 반환 (점수 낮은 순)."""
    _ensure_cache_fresh(companies_listed)
    return (_cache['risk_data'] or [])[:limit]


def get_top_good_disclosures(companies_listed, limit=5):
    """최근 24시간 호재 공시 TOP N 반환 (점수 높은 순)."""
    _ensure_cache_fresh(companies_listed)
    return (_cache['good_data'] or [])[:limit]


def _ensure_cache_fresh(companies_listed):
    """캐시가 만료됐으면 다시 분석."""
    now = time.time()
    if _cache['all_signals'] is not None and now < _cache['expires_at']:
        return
    
    print("🔍 [공시 스캐너] 분석 시작...")
    start_time = time.time()
    
    try:
        all_signals = _fetch_and_analyze(companies_listed)
        
        # 위험 공시: 점수 ≤ -2, 점수 낮은 순
        risk_signals = [s for s in all_signals if s['score'] <= -2]
        risk_signals.sort(key=lambda x: x['score'])
        
        # 호재 공시: 점수 ≥ 2, 점수 높은 순
        good_signals = [s for s in all_signals if s['score'] >= 2]
        good_signals.sort(key=lambda x: -x['score'])
        
        _cache['risk_data'] = risk_signals
        _cache['good_data'] = good_signals
        _cache['all_signals'] = all_signals
        _cache['expires_at'] = now + _CACHE_TTL_SECONDS
        
        elapsed = time.time() - start_time
        print(f"   ✅ 위험 {len(risk_signals)}건 / 호재 {len(good_signals)}건 ({elapsed:.1f}초)")
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        _cache['risk_data'] = []
        _cache['good_data'] = []
        _cache['all_signals'] = []


def _fetch_and_analyze(companies_listed):
    """DART API에서 최근 24시간 공시 가져와서 분석."""
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    corp_lookup = {c['corp_code']: c for c in companies_listed}
    
    all_disclosures = []
    for page in range(1, 6):
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
            
            total_page = response.get('total_page', 1)
            if page >= total_page:
                break
        except Exception as e:
            print(f"   [페이지 {page} 오류] {e}")
            break
    
    # 분석
    signals = []
    
    for item in all_disclosures:
        nm = item.get('report_nm', '')
        corp_code = item.get('corp_code', '')
        corp_name = item.get('corp_name', '') or '-'
        rcept_no = item.get('rcept_no', '')
        rcept_dt = item.get('rcept_dt', '')
        
        corp_info = corp_lookup.get(corp_code)
        if not corp_info or not corp_info.get('stock_code'):
            continue
        
        analysis = analyze_disclosure(nm)
        score = analysis['score']
        
        # 점수가 의미 있는 것만
        if -2 < score < 2:
            continue
        
        time_ago = _calculate_time_ago(rcept_dt)
        
        signals.append({
            'corp_name': corp_name,
            'corp_code': corp_code,
            'stock_code': corp_info.get('stock_code', ''),
            'title': nm,
            'rule_title': analysis['rule_title'],
            'score': score,
            'score_label': analysis['score_label'],
            'score_emoji': analysis['score_emoji'],
            'explain': analysis['explain'],
            'rcept_dt': rcept_dt,
            'time_ago': time_ago,
            'dart_url': f'https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}' if rcept_no else '',
            'category': analysis.get('category', 'neutral'),
        })
    
    return signals


def _calculate_time_ago(rcept_dt):
    """공시 접수일로 'N시간 전' 계산."""
    try:
        if not rcept_dt or len(rcept_dt) != 8:
            return ''
        
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
    _cache['risk_data'] = None
    _cache['good_data'] = None
    _cache['all_signals'] = None
    _cache['expires_at'] = 0
    print("🔄 공시 캐시 초기화됨")


# ============================================================
# 직접 실행 시 테스트
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("🚨 공시 스캐너 테스트 (위험 + 호재)")
    print("=" * 60)
    
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
    
    risks = get_top_risk_disclosures(companies_listed, limit=5)
    goods = get_top_good_disclosures(companies_listed, limit=5)
    
    print(f"\n🚨 위험 공시 TOP {len(risks)}:")
    print("-" * 60)
    for i, r in enumerate(risks, 1):
        print(f"{i}. {r['score_emoji']} {r['score']}점 [{r['score_label']}]")
        print(f"   {r['corp_name']} ({r['stock_code']}) - {r['rule_title']}")
        print(f"   {r['time_ago']}")
    
    print(f"\n💰 호재 공시 TOP {len(goods)}:")
    print("-" * 60)
    for i, g in enumerate(goods, 1):
        print(f"{i}. {g['score_emoji']} +{g['score']}점 [{g['score_label']}]")
        print(f"   {g['corp_name']} ({g['stock_code']}) - {g['rule_title']}")
        print(f"   {g['time_ago']}")