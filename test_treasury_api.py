"""
자사주 (취득/처분/소각) DART API 응답 탐색 스크립트
- 어떤 필드명이 들어있는지 확인용
- 결과 보고 dart_xray.py 에 정식 함수 추가할 예정
"""
import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
API_KEY = os.environ.get('DART_API_KEY', '')
BASE = 'https://opendart.fss.or.kr/api'

# SK하이닉스 corp_code
HYNIX = '00164779'

# 최근 1년치
today = datetime.now()
start = today - timedelta(days=365)

# DART의 자사주 관련 endpoint 후보 3가지
ENDPOINTS = {
    '자기주식취득결정': 'tsstkAqDecsn.json',
    '자기주식처분결정': 'tsstkDpDecsn.json',
    '자기주식취득신탁계약체결결정': 'tsstkAqTrctrCcDecsn.json',
}

for label, endpoint in ENDPOINTS.items():
    print(f"\n{'='*70}")
    print(f"📋 {label}  ({endpoint})")
    print('='*70)

    r = requests.get(f'{BASE}/{endpoint}', params={
        'crtfc_key': API_KEY,
        'corp_code': HYNIX,
        'bgn_de': start.strftime('%Y%m%d'),
        'end_de': today.strftime('%Y%m%d'),
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
    else:
        print("❌ 데이터 없음")