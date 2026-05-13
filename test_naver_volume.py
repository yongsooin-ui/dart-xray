"""
DART X-RAY 주가 정보 모듈 (네이버 금융 스크래핑)
- 가격, 등락, 거래량, 시가총액, 업종 등을 네이버 금융에서 가져옴
- Railway 배포 환경에서도 안정적 (yfinance 같은 봇 차단 없음)
- 약 15~20분 지연 데이터
"""
import requests
from bs4 import BeautifulSoup
import re


# 브라우저처럼 보이는 헤더
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
}


def get_stock_info(stock_code, corp_code=None):
    """
    종목코드를 받아 네이버 금융에서 주가 정보를 가져옵니다.

    Args:
        stock_code: '005930' 같은 6자리 종목코드 (문자열)
        corp_code: 호환성을 위해 받지만 사용 안 함

    Returns:
        dict or None: 주가 정보 딕셔너리 (실패 시 None)
    """
    if not stock_code or not stock_code.isdigit() or len(stock_code) != 6:
        return None

    url = f'https://finance.naver.com/item/main.naver?code={stock_code}'

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.encoding = r.apparent_encoding

        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, 'lxml')

        # 회사명
        name_tag = soup.select_one('div.wrap_company h2 a')
        name = name_tag.text.strip() if name_tag else ''

        # 시장 구분 (코스피/코스닥)
        market = '한국거래소'
        market_tag = soup.select_one('div.description img')
        if market_tag:
            alt = market_tag.get('alt', '') or ''
            src = market_tag.get('src', '') or ''
            combined = (alt + ' ' + src).lower()
            if 'kospi' in combined or '코스피' in alt:
                market = '코스피'
            elif 'kosdaq' in combined or '코스닥' in alt:
                market = '코스닥'

        # 현재가
        price_tag = soup.select_one('p.no_today span.blind')
        if not price_tag:
            return None
        price = _to_int(price_tag.text)
        if not price:
            return None

        # 등락 정보 (전일 대비)
        change = 0
        change_pct = 0
        direction = 'flat'

        exday_tag = soup.select_one('p.no_exday')
        if exday_tag:
            blinds = exday_tag.select('span.blind')
            nums = []
            for b in blinds:
                txt = b.text.strip()
                if re.search(r'\d', txt):
                    nums.append(txt)

            if len(nums) >= 2:
                change = _to_int(nums[0])
                try:
                    change_pct = float(nums[1].replace('%', '').replace(',', ''))
                except (ValueError, TypeError):
                    change_pct = 0

            html_str = str(exday_tag)
            if 'ico_up' in html_str or 'point_up' in html_str:
                direction = 'up'
            elif 'ico_down' in html_str or 'point_dn' in html_str:
                direction = 'down'
                change = -abs(change)
                change_pct = -abs(change_pct)

        # 전일 종가
        prev_close = price - change if change else price

        # 거래량: 페이지 전체 텍스트에서 "거래량" 다음 숫자 찾기 (관대한 매칭)
        volume = 0
        # 우선 dl > dd 시도 (가장 안정적인 위치)
        for dd in soup.find_all('dd'):
            text = dd.get_text(separator=' ', strip=True)
            if '거래량' in text:
                # 거래량 뒤의 첫 번째 숫자 (콤마 포함)
                m = re.search(r'거래량[\s\S]*?([\d,]{3,})', text)
                if m:
                    candidate = _to_int(m.group(1))
                    if candidate > 0:
                        volume = candidate
                        break

        # 못 찾았으면 table.no_info에서 시도
        if not volume:
            for table in soup.select('table.no_info'):
                text = table.get_text(separator=' ', strip=True)
                m = re.search(r'거래량\s*([\d,]{3,})', text)
                if m:
                    volume = _to_int(m.group(1))
                    if volume:
                        break

        # 시가총액: id="_market_sum"
        market_cap_eok = 0
        cap_em = soup.select_one('#_market_sum')
        if cap_em:
            market_cap_eok = _parse_market_cap_to_eok(cap_em)

        return {
            'ticker': stock_code,
            'name': name,
            'price': price,
            'price_fmt': f"{price:,.0f}",
            'change': change,
            'change_fmt': f"{change:+,.0f}",
            'change_pct': round(change_pct, 2),
            'change_pct_fmt': f"{change_pct:+.2f}%",
            'direction': direction,
            'prev_close': prev_close,
            'volume': volume,
            'market_cap_eok': market_cap_eok,
            'market_cap_fmt': _format_market_cap(market_cap_eok),
            'sector': '',
            'industry': '',
            'market': market,
            'currency': 'KRW',
            'has_market_cap': market_cap_eok > 0,
            'data_completeness': 4 if market_cap_eok > 0 and volume > 0 else 2,
        }
    except Exception as e:
        print(f"[네이버 금융 조회 오류] {stock_code}: {e}")
        return None


def _to_int(text):
    """'1,234,500' → 1234500. 실패 시 0."""
    if not text:
        return 0
    try:
        cleaned = re.sub(r'[^\d]', '', str(text))
        return int(cleaned) if cleaned else 0
    except (ValueError, TypeError):
        return 0


def _parse_market_cap_to_eok(em_tag):
    """
    네이버 시가총액 em 태그에서 억 단위 숫자로 변환.
    "375조 8,265" → 3758265 (억)
    "1,234" → 1234 (억)
    """
    try:
        text = em_tag.get_text(separator=' ', strip=True)
        text = text.replace(',', '').replace('\t', '').replace('\n', ' ')

        if '조' in text:
            parts = text.split('조')
            jo = int(re.sub(r'[^\d]', '', parts[0]) or 0)
            eok_part = re.sub(r'[^\d]', '', parts[1]) if len(parts) > 1 else '0'
            eok = int(eok_part) if eok_part else 0
            return jo * 10000 + eok
        else:
            num = re.sub(r'[^\d]', '', text)
            return int(num) if num else 0
    except Exception:
        return 0


def _format_market_cap(eok):
    """억 원 단위를 보기 좋게 포맷 (1조 이상이면 '조' 단위로)"""
    if not eok or eok <= 0:
        return '-'
    if eok >= 10000:
        return f"{eok / 10000:,.1f}조"
    return f"{eok:,.0f}억"


# ===== 테스트 =====
if __name__ == '__main__':
    test_codes = [
        ('005930', '삼성전자 (코스피)'),
        ('000660', 'SK하이닉스 (코스피)'),
        ('035720', '카카오 (코스피)'),
        ('086520', '에코프로 (코스닥)'),
        ('247540', '에코프로비엠 (코스닥)'),
        ('288980', '모아데이타 (코스닥)'),
    ]
    print("=" * 60)
    print("🧪 네이버 금융 주가 조회 테스트")
    print("=" * 60)
    for code, desc in test_codes:
        info = get_stock_info(code)
        if info:
            print(f"\n📈 [{code}] {desc}")
            print(f"   이름:   {info['name']}")
            print(f"   시장:   {info['market']}")
            print(f"   현재가: {info['price_fmt']}원 ({info['change_pct_fmt']})")
            print(f"   시총:   {info['market_cap_fmt']}")
            print(f"   거래량: {info['volume']:,}")
        else:
            print(f"\n❌ [{code}] {desc} - 조회 실패")