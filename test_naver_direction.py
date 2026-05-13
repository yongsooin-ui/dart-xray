"""
네이버 금융 등락 방향 판정 검증
- 상승/하락/보합 종목을 다 테스트해서 어디서 잘못 됐는지 확인
"""
import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
}

# 다양한 종목 (상승/하락 섞어서)
test_codes = [
    ('088280', '쏘닉스 (방금 본 것)'),
    ('125020', '티씨머티리얼즈 (방금 본 것)'),
    ('005930', '삼성전자'),
    ('000660', 'SK하이닉스'),
    ('035720', '카카오'),
    ('086520', '에코프로'),
]

for code, desc in test_codes:
    url = f'https://finance.naver.com/item/main.naver?code={code}'
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, 'lxml')

    print(f"\n{'='*70}")
    print(f"📊 [{code}] {desc}")
    print('='*70)

    # 현재가
    price_tag = soup.select_one('p.no_today span.blind')
    price_text = price_tag.text.strip() if price_tag else '???'
    print(f"현재가 (span.blind): {price_text}")

    # 등락 부분 — 통째로 HTML 출력
    exday_tag = soup.select_one('p.no_exday')
    if exday_tag:
        print(f"\n🔍 p.no_exday 전체 HTML:")
        print(str(exday_tag)[:1500])  # 처음 1500자만

        # blind 태그들 모두
        print(f"\n🔍 span.blind 텍스트 모음:")
        for i, b in enumerate(exday_tag.select('span.blind'), 1):
            print(f"   [{i}] '{b.text.strip()}'")

        # 클래스명 검색
        html_str = str(exday_tag)
        print(f"\n🔍 클래스명 매칭:")
        print(f"   'ico_up'   in HTML: {'ico_up' in html_str}")
        print(f"   'ico_down' in HTML: {'ico_down' in html_str}")
        print(f"   'point_up' in HTML: {'point_up' in html_str}")
        print(f"   'point_dn' in HTML: {'point_dn' in html_str}")
        print(f"   '상승'      in HTML: {'상승' in html_str}")
        print(f"   '하락'      in HTML: {'하락' in html_str}")
        print(f"   '보합'      in HTML: {'보합' in html_str}")