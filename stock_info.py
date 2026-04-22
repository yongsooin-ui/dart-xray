"""
DART X-RAY 주가 정보 모듈 (Yahoo Finance)
종목코드로 현재가·등락률·업종 등을 조회합니다.
15분 내외 지연 데이터입니다.
"""
import yfinance as yf


def get_stock_info(stock_code):
    """
    종목코드(6자리)를 받아 주가 정보를 반환합니다.
    코스피(.KS)와 코스닥(.KQ) 둘 다 시도해서 '더 완전한' 결과를 고릅니다.

    Args:
        stock_code: '005930' 같은 6자리 종목코드 (문자열)

    Returns:
        dict or None: 주가 정보 딕셔너리 (실패 시 None)
    """
    if not stock_code or not stock_code.isdigit() or len(stock_code) != 6:
        return None

    # 코스피 & 코스닥 둘 다 시도한 뒤, 가장 데이터가 풍부한 쪽을 선택
    candidates = []
    for suffix, market in [('.KS', '코스피'), ('.KQ', '코스닥')]:
        result = _fetch_single(stock_code, suffix, market)
        if result:
            candidates.append(result)

    if not candidates:
        return None

    # 시가총액이 있는 결과를 우선 (진짜 그 시장에 상장된 종목)
    candidates.sort(key=lambda x: (x['has_market_cap'], x['data_completeness']), reverse=True)
    return candidates[0]


def _fetch_single(stock_code, suffix, market):
    """특정 접미사로 Yahoo Finance 조회 시도."""
    ticker_symbol = f"{stock_code}{suffix}"
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        # 기본 유효성: 가격이 반드시 있어야 함
        price = info.get('regularMarketPrice') or info.get('currentPrice')
        if not price:
            return None

        # Yahoo가 명시적으로 거래소를 알려주면 그걸 우선
        exchange = info.get('exchange', '')  # 'KSC' = KOSPI, 'KOE' = KOSDAQ
        if exchange == 'KSC':
            market = '코스피'
        elif exchange == 'KOE':
            market = '코스닥'

        # 등락 계산
        prev_close = info.get('regularMarketPreviousClose') or info.get('previousClose') or 0
        change = price - prev_close if prev_close else 0
        change_pct = (change / prev_close * 100) if prev_close else 0

        # 시총
        market_cap = info.get('marketCap', 0) or 0
        market_cap_eok = market_cap / 100_000_000 if market_cap else 0

        # 거래량
        volume = info.get('regularMarketVolume') or info.get('volume') or 0

        # 데이터 완성도 점수 (시총·거래량·전일종가가 다 있으면 진짜 해당 시장의 종목)
        completeness = 0
        if market_cap > 0: completeness += 2
        if volume > 0: completeness += 1
        if prev_close > 0: completeness += 1

        return {
            'ticker': ticker_symbol,
            'name': info.get('longName') or info.get('shortName') or '',
            'price': price,
            'price_fmt': f"{price:,.0f}",
            'change': change,
            'change_fmt': f"{change:+,.0f}",
            'change_pct': round(change_pct, 2),
            'change_pct_fmt': f"{change_pct:+.2f}%",
            'direction': 'up' if change > 0 else ('down' if change < 0 else 'flat'),
            'prev_close': prev_close,
            'volume': volume,
            'market_cap_eok': market_cap_eok,
            'market_cap_fmt': _format_market_cap(market_cap_eok),
            'sector': info.get('sector', ''),
            'industry': info.get('industry', ''),
            'market': market,
            'currency': info.get('currency', 'KRW'),
            'has_market_cap': market_cap > 0,
            'data_completeness': completeness,
        }
    except Exception:
        return None


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
        ('030530', '원익홀딩스 (코스닥)'),
        ('086520', '에코프로 (코스닥)'),
        ('247540', '에코프로비엠 (코스닥)'),
    ]
    print("=" * 60)
    print("🧪 Yahoo Finance 주가 조회 테스트 (코스닥 포함)")
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
            print(f"   업종:   {info['industry']}")
        else:
            print(f"\n❌ [{code}] {desc} - 조회 실패")