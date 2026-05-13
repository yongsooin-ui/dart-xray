"""
DART 주식 총수 API 응답 탐색
- 발행주식수, 자사주 등 주식 관련 필드 확인용
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get('DART_API_KEY', '')
BASE = 'https://opendart.fss.or.kr/api'

# 테스트 종목들
TEST_CORPS = [
    ('00126380', '삼성전자'),
    ('00164779', 'SK하이닉스'),
    ('00401731', '카카오'),
]

# 가장 최근 사업보고서 (2024년 사업보고서, 11011)
for corp_code, name in TEST_CORPS:
    print(f"\n{'='*70}")
    print(f"📋 {name} ({corp_code})")
    print('='*70)

    r = requests.get(f'{BASE}/stockTotqySttus.json', params={
        'crtfc_key': API_KEY,
        'corp_code': corp_code,
        'bsns_year': '2024',
        'reprt_code': '11011',  # 사업보고서
    }, timeout=10)

    data = r.json()
    print(f"status: {data.get('status')}")
    print(f"message: {data.get('message')}")

    items = data.get('list', [])
    if items:
        print(f"\n✅ {len(items)}건 발견")
        print(f"\n📦 첫 항목의 모든 키:")
        for k, v in items[0].items():
            print(f"  {k:30s} : {v}")

        # 보통주 관련 항목만 따로 확인
        print(f"\n🔍 보통주 관련 항목들:")
        for item in items:
            se = item.get('se', '')
            if '보통주' in se or '주식' in se:
                print(f"  - {se}: {item.get('istc_totqy', '-')}주 (발행), {item.get('now_to_isstk_totqy', '-')}주 (현재)")
    else:
        print("❌ 데이터 없음")