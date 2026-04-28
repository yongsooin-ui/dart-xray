"""
DART X-RAY 주가 정보 모듈
- 가격/거래량/등락률: Yahoo Finance (yfinance)
- 시가총액: DART API에서 발행주식수 → 종가 × 주식수로 계산 (안정적)

이렇게 하이브리드로 가는 이유:
- yfinance는 가격은 잘 가져오지만 한국 시총은 종종 누락됨
- DART의 발행주식수는 항상 안정적
- Railway 배포 환경에서도 시총이 깨지지 않음
"""
import yfinance as yf
import dart_xray as engine


def get_stock_info(stock_code, corp_code=None):
    """
    종목코드를 받아 주가 정보를 반환합니다.

    Args:
        stock_code: '005930' 같은 6자리 종목코드 (문자열)
        corp_code: '00126380' 같은 DART 8자리 고유번호 (시총 계산용)

    Returns:
        dict or None: 주가 정보 딕셔너리 (실패 시 None)
    """
    if not stock_code or not stock_code.isdigit() or len(stock_code) != 6:
        return None

    # 1) yfinance에서 가격, 거래량, 등락률 등 가져오기
    candidates = []
    for suffix, market in [('.KS', '코스피'), ('.KQ', '코스닥')]:
        result = _fetch_yfinance(stock_code, suffix, market)
        if result:
            candidates.append(result)

    if not candidates:
        # yfinance가 완전히 실패한 경우에도, DART로 회사명만 채워서 빈 결과라도 보냄
        return _fallback_dart_only(stock_code, corp_code)

    # 가장 데이터가 풍부한 후보 선택
    candidates.sort(key=lambda x: x['data_completeness'], reverse=True)
    info = candidates[0]

    # 2) DART에서 발행주식수 조회해서 시총 직접 계산
    if corp_code:
        dart_cap = _calculate_market_cap_from_dart(corp_code, info['price'])
        if dart_cap > 0:
            info['market_cap_eok'] = dart_cap / 100_000_000
            info['market_cap_fmt'] = _format_market_cap(info['market_cap_eok'])
            info['has_market_cap'] = True

    return info


def _fetch_yfinance(stock_code, suffix, market):
    """yfinance에서 가격·거래량 정보 조회."""
    ticker_symbol = f"{stock_code}{suffix}"
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        price = info.get('regularMarketPrice') or info.get('currentPrice')
        if not price:
            return None

        # 거래소 명시 정보로 시장 보정
        exchange = info.get('exchange', '')
        if exchange == 'KSC':
            market = '코스피'
        elif exchange == 'KOE':
            market = '코스닥'

        prev_close = info.get('regularMarketPreviousClose') or info.get('previousClose') or 0
        change = price - prev_close if prev_close else 0
        change_pct = (change / prev_close * 100) if prev_close else 0

        # yfinance의 시총 (참고용, DART로 덮어쓸 예정)
        market_cap = info.get('marketCap', 0) or 0
        market_cap_eok = market_cap / 100_000_000 if market_cap else 0

        volume = info.get('regularMarketVolume') or info.get('volume') or 0

        # 데이터 완성도 점수
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


def _calculate_market_cap_from_dart(corp_code, price):
    """
    DART의 발행주식수와 현재 종가를 곱해 시가총액을 계산.

    Args:
        corp_code: 8자리 DART 고유번호
        price: 현재 종가 (yfinance에서 가져온 값)

    Returns:
        int: 시가총액 (원 단위), 실패 시 0
    """
    if not corp_code or not price:
        return 0

    # 사업보고서 우선, 안 되면 분기보고서들 차례대로 시도
    for reprt in ['11011', '11014', '11012', '11013']:
        share_data = engine.get_share_count(corp_code, year='2024', reprt=reprt)
        if share_data and share_data['total_shares'] > 0:
            return int(price * share_data['total_shares'])

    # 2024년이 안 되면 2023년도 시도
    for reprt in ['11011']:
        share_data = engine.get_share_count(corp_code, year='2023', reprt=reprt)
        if share_data and share_data['total_shares'] > 0:
            return int(price * share_data['total_shares'])

    return 0


def _fallback_dart_only(stock_code, corp_code):
    """yfinance 완전 실패 시 DART 정보만이라도 채워서 반환."""
    if not corp_code:
        return None

    share_data = engine.get_share_count(corp_code)
    if not share_data:
        return None

    # 가격 정보가 없으니 시총도 계산 불가, 일단 구조만 반환
    return {
        'ticker': stock_code,
        'name': '',
        'price': 0,
        'price_fmt': '-',
        'change': 0,
        'change_fmt': '-',
        'change_pct': 0,
        'change_pct_fmt': '-',
        'direction': 'flat',
        'prev_close': 0,
        'volume': 0,
        'market_cap_eok': 0,
        'market_cap_fmt': '-',
        'sector': '',
        'industry': '',
        'market': '한국거래소',
        'currency': 'KRW',
        'has_market_cap': False,
        'data_completeness': 0,
    }


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
        ('005930', '00126380', '삼성전자 (코스피)'),
        ('000660', '00164779', 'SK하이닉스 (코스피)'),
        ('035720', '00401731', '카카오 (코스피)'),
    ]
    print("=" * 60)
    print("🧪 yfinance + DART 시총 계산 테스트")
    print("=" * 60)
    for code, corp, desc in test_codes:
        info = get_stock_info(code, corp_code=corp)
        if info:
            print(f"\n📈 [{code}] {desc}")
            print(f"   이름:   {info['name']}")
            print(f"   시장:   {info['market']}")
            print(f"   현재가: {info['price_fmt']}원 ({info['change_pct_fmt']})")
            print(f"   시총:   {info['market_cap_fmt']}")
            print(f"   거래량: {info['volume']:,}")
        else:
            print(f"\n❌ [{code}] {desc} - 조회 실패")