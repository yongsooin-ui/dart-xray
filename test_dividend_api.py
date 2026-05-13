"""
사업보고서의 배당 데이터를 직접 들여다보기 (검증용)
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get('DART_API_KEY', '')
BASE = 'https://opendart.fss.or.kr/api'

# 하이닉스 검증
corp_code = '00164779'

# 2024, 2025년 사업보고서 둘 다 시도
for year in ['2025', '2024', '2023']:
    print(f"\n{'='*70}")
    print(f"📋 SK하이닉스 {year}년 사업보고서 (reprt=11011)")
    print('='*70)

    r = requests.get(f'{BASE}/alotMatter.json', params={
        'crtfc_key': API_KEY,
        'corp_code': corp_code,
        'bsns_year': year,
        'reprt_code': '11011',
    }, timeout=10)

    data = r.json()
    print(f"status: {data.get('status')}, message: {data.get('message')}")

    items = data.get('list', [])
    if not items:
        continue

    print(f"\n📦 전체 항목 수: {len(items)}건")
    print(f"\n📊 배당 관련 항목 모두 표시:")
    for i, item in enumerate(items, 1):
        se = item.get('se', '')
        knd = item.get('stock_knd', '')
        thstrm = item.get('thstrm', '-')      # 당기
        frmtrm = item.get('frmtrm', '-')      # 전기
        lwfr = item.get('lwfr', '-')          # 전전기

        print(f"\n  [{i}] 구분: {se}")
        print(f"      주식종류: {knd}")
        print(f"      당기:   {thstrm}")
        print(f"      전기:   {frmtrm}")
        print(f"      전전기: {lwfr}")