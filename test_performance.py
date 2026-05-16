from dart_xray import get_financial_statements, get_performance_analysis, parse_performance_numbers

print('=' * 60)
print('단계별 디버깅')
print('=' * 60)

# 1단계: 직접 OFS로 호출
print("\n[1단계] OFS 직접 호출")
fin_data = get_financial_statements('00598198', '2026', '11013', fs_div='OFS')
print(f"결과: {len(fin_data) if fin_data else 0}개 항목")

# 2단계: parse_performance_numbers 직접 호출
print("\n[2단계] parse_performance_numbers 직접 호출")
parsed = parse_performance_numbers(fin_data)
if parsed:
    print(f"✅ 파싱 성공")
    print(f"  매출 항목명: {parsed['revenue']['item_name']}")
    print(f"  매출 (당기): {parsed['revenue']['curr']}")
    print(f"  매출 (전년동기): {parsed['revenue']['prev']}")
    print(f"  매출 증감률: {parsed['revenue']['yoy_pct']}%")
    print(f"  영업이익 항목명: {parsed['op_profit']['item_name']}")
    print(f"  영업이익 (당기): {parsed['op_profit']['curr']}")
    print(f"  영업이익 (전년동기): {parsed['op_profit']['prev']}")
    print(f"  영업이익 증감률: {parsed['op_profit']['yoy_pct']}%")
else:
    print("❌ 파싱 실패 (None 반환)")
    print("\n[디버그] 손익계산서 항목 전체:")
    for item in fin_data:
        sj = item.get('sj_div', '')
        if sj in ['IS', 'CIS']:
            nm = item.get('account_nm', '').strip()
            curr = item.get('thstrm_amount', '-')
            print(f"  [{sj}] '{nm}': {curr}")

# 3단계: get_performance_analysis 호출
print("\n[3단계] get_performance_analysis 호출")
result = get_performance_analysis('00598198', '20260513')
if result:
    print(f"✅ 분석 성공")
    print(f"  보고서: {result.get('report_label')}")
else:
    print("❌ 분석 실패 (None 반환)")