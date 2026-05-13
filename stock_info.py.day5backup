"""
DART X-RAY 주가 정보 모듈 (네이버 금융 스크래핑)
- 가격, 등락, 시가총액, 시장구분 등을 네이버 금융에서 가져옴
- Railway 배포 환경에서도 안정적 (yfinance 같은 봇 차단 없음)
- 약 15~20분 지연 데이터
- ※ 거래량은 네이버 페이지 동적 로드 이슈로 미지원
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

            # 한글 텍스트로 방향 판정 (네이버는 ico up/down 클래스 + 상승/하락 텍스트 사용)
            html_str = str(exday_tag)
            if '상승' in html_str:
                direction = 'up'
            elif '하락' in html_str:
                direction = 'down'
                change = -abs(change)
                change_pct = -abs(change_pct)
            elif '보합' in html_str:
                direction = 'flat'

        # 전일 종가
        prev_close = price - change if change else price

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
            'volume': 0,  # 거래량 미지원
            'market_cap_eok': market_cap_eok,
            'market_cap_fmt': _format_market_cap(market_cap_eok),
            'sector': '',
            'industry': '',
            'market': market,
            'currency': 'KRW',
            'has_market_cap': market_cap_eok > 0,
            'data_completeness': 3 if market_cap_eok > 0 else 1,
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
        else:
            print(f"\n❌ [{code}] {desc} - 조회 실패")

# ============================================================
# 주가 차트 데이터 수집 (네이버 금융 일별 시세 스크래핑)
# ============================================================

def get_chart_data(stock_code, days=20):
    """
    네이버 금융에서 최근 N거래일 일별 종가 데이터 수집.
    반환: SVG 차트 그리기에 바로 쓸 수 있는 dict.
    실패 시 None 반환.

    Args:
        stock_code: '005930' 같은 6자리 종목코드
        days: 거래일 수 (기본 20일 = 약 1개월)
    """
    if not stock_code or len(stock_code) != 6:
        return None

    try:
        prices = []
        dates = []
        pages_needed = (days // 10) + 1

        for page in range(1, pages_needed + 1):
            url = f'https://finance.naver.com/item/sise_day.naver?code={stock_code}&page={page}'
            r = requests.get(url, headers=HEADERS, timeout=5)
            r.encoding = 'euc-kr'

            if r.status_code != 200:
                continue

            soup = BeautifulSoup(r.text, 'lxml')
            rows = soup.select('table.type2 tr')

            for row in rows:
                cells = row.select('td')
                if len(cells) < 2:
                    continue
                date_text = cells[0].get_text(strip=True)
                close_text = cells[1].get_text(strip=True)

                if not date_text or not close_text or '.' not in date_text:
                    continue

                try:
                    close_price = int(close_text.replace(',', ''))
                    if close_price <= 0:
                        continue
                    dates.append(date_text)
                    prices.append(close_price)
                except ValueError:
                    continue

            if len(prices) >= days:
                break

        if len(prices) < 2:
            return None

        # 오래된 → 최신 순서로 정렬 (네이버는 최신이 위)
        prices = list(reversed(prices[:days]))
        dates = list(reversed(dates[:days]))

        return _build_chart_svg_data(prices, dates)

    except Exception as e:
        print(f"[차트 데이터 오류] {stock_code}: {e}")
        return None


def _build_chart_svg_data(prices, dates):
    """가격 배열을 받아 SVG path 문자열로 변환. viewBox는 300 x 60."""
    if len(prices) < 2:
        return None

    width = 300
    height = 60
    padding_y = 4

    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price if max_price > min_price else 1

    n = len(prices)
    points = []

    for i, price in enumerate(prices):
        x = (i / (n - 1)) * width
        y_normalized = (price - min_price) / price_range
        y = height - padding_y - y_normalized * (height - 2 * padding_y)
        points.append((x, y))

    # 라인 path
    line_path = f"M {points[0][0]:.2f} {points[0][1]:.2f}"
    for x, y in points[1:]:
        line_path += f" L {x:.2f} {y:.2f}"

    # 면적 path
    area_path = line_path + f" L {points[-1][0]:.2f} {height} L {points[0][0]:.2f} {height} Z"

    # 등락 방향 및 색상
    first_price = prices[0]
    last_price = prices[-1]
    change = last_price - first_price
    change_pct = (change / first_price * 100) if first_price else 0

    if change > 0:
        direction = 'up'
        color = '#f87171'  # 한국 관례: 상승 = 빨강
        change_pct_fmt = f"+{change_pct:.1f}%"
    elif change < 0:
        direction = 'down'
        color = '#60a5fa'  # 하락 = 파랑
        change_pct_fmt = f"{change_pct:.1f}%"
    else:
        direction = 'flat'
        color = '#9ca3af'
        change_pct_fmt = "0.0%"

    return {
        'points': prices,
        'line_path': line_path,
        'area_path': area_path,
        'color': color,
        'direction': direction,
        'change_pct_fmt': change_pct_fmt,
        'last_x': points[-1][0],
        'last_y': points[-1][1],
        'start_date': dates[0],
        'end_date': dates[-1],
    }