"""
DART X-RAY 공시 해석 엔진 v2.0
- 룰 18개 → 50+개로 확장
- 실무 투자자 관점의 해설 강화
- '기타경영사항(자율공시)' 등 혼합형 공시 세분화

점수 스케일: -10 (최악재) ~ 0 (중립) ~ +10 (최호재)

* 키워드 매칭은 '구체적 → 일반적' 순서. 먼저 매칭된 룰이 채택됩니다.
"""


RULES = [
    # ══════════════════════════════════════
    # 🟢 강한 호재 (+7 ~ +10)
    # ══════════════════════════════════════
    {
        'keywords': ['자기주식소각', '주식소각결정'],
        'score': 9, 'category': 'good',
        'title': '자사주 소각 결정',
        'explain': '회사가 가진 자기 주식을 영구히 없애는 결정입니다. 유통 주식 수가 실제로 줄어들어 내 지분 가치가 올라가는 가장 강력한 주주환원입니다. 소각 규모가 시가총액의 1%만 넘어도 의미 있고, 5% 이상이면 매우 큰 호재입니다.',
    },
    {
        'keywords': ['자기주식취득결정'],
        'score': 6, 'category': 'good',
        'title': '자사주 취득 결정',
        'explain': '회사가 자기 주식을 사들이겠다는 결정입니다. 단기 수급에 긍정적이고 주가 방어 효과가 있습니다. 다만 취득만 하고 나중에 다시 팔아버리면 의미가 반감되므로, "소각까지 이어지는지"가 진짜 핵심입니다.',
    },
    {
        'keywords': ['자기주식취득신탁계약체결'],
        'score': 5, 'category': 'good',
        'title': '자사주 취득 신탁 체결',
        'explain': '증권사에 맡겨서 일정 기간 동안 자사주를 사들이겠다는 계약입니다. 직접 취득보다 조금 완곡한 주주환원 의지 표시입니다.',
    },

    # ══════════════════════════════════════
    # 🟢 호재 (+4 ~ +6)
    # ══════════════════════════════════════
    {
        'keywords': ['무상증자'],
        'score': 5, 'category': 'good',
        'title': '무상증자 결정',
        'explain': '잉여금을 자본금으로 옮기면서 주주에게 공짜로 신주를 배정합니다. 주식 수가 늘지만 내 보유 주식 수도 같이 늘어 손해는 없고, 회사가 "우리 재무 자신 있다"는 신호로 받아들여지는 호재입니다.',
    },
    {
        'keywords': ['단일판매ㆍ공급계약해지', '단일판매·공급계약해지',
                     '단일판매ㆍ공급계약취소', '단일판매·공급계약취소',
                     '단일판매ㆍ공급계약의해지', '단일판매·공급계약의해지'],
        'score': -5, 'category': 'bad',
        'title': '수주·공급계약 해지',
        'explain': '체결했던 공급계약이 해지·취소된 공시입니다. 확보했던 매출처가 사라지는 악재. 해지 금액이 최근 매출 대비 클수록 실적 타격이 커집니다. 공시 본문의 "매출액 대비 비율"을 꼭 확인하세요.',
    },
    {
        'keywords': ['단일판매ㆍ공급계약', '단일판매·공급계약', '공급계약체결'],
        'exclude_keywords': ['정정'],
        'score': 5, 'category': 'good',
        'title': '대규모 수주·공급계약',
        'explain': '굵직한 매출처를 확보했다는 신호입니다. 계약 금액이 회사 최근 매출액 대비 크면 클수록 실적 기여도가 높아지는 호재. 공시 본문의 "매출액 대비 비율"을 꼭 확인하세요.',
    },
    {
        'keywords': ['영업(잠정)실적', '매출액또는손익구조30%', '영업실적등에대한전망'],
        'score': 0, 'category': 'neutral',
        'title': '실적 공시',
        'explain': '회사의 매출·영업이익 등을 발표하는 공시입니다. 실제 호재/악재 여부는 본문의 매출·영업이익 숫자 (전년 동기 대비)로 판단됩니다. 분석 결과는 결론 카드에서 확인하세요.',
        'needs_deep_analysis': True,  # 심층 분석 필요 플래그
    },

    # ══════════════════════════════════════
    # 🟢 약한 호재 (+1 ~ +3)
    # ══════════════════════════════════════
    {
        'keywords': ['현금ㆍ현물배당결정', '현금·현물배당결정', '현금배당결정'],
        'score': 3, 'category': 'good',
        'title': '현금 배당 결정',
        'explain': '주주에게 현금을 직접 지급합니다. 전년 대비 늘었다면 확실한 호재, 같거나 줄었다면 중립~약한 실망감일 수 있어요. 금액보다 "전년 대비 증감률"을 보세요.',
    },
    {
        'keywords': ['현금ㆍ주식배당결정', '주식배당결정'],
        'score': 3, 'category': 'good',
        'title': '주식 배당 결정',
        'explain': '현금 대신 주식으로 배당합니다. 주식 수는 늘지만 총 가치는 유지돼 효과는 무상증자와 비슷합니다.',
    },
    {
        'keywords': ['주식분할결정'],
        'score': 2, 'category': 'good',
        'title': '액면분할 결정',
        'explain': '주당 가격을 낮추기 위해 1주를 여러 주로 쪼개는 결정입니다. 개인 투자자 접근성이 좋아져 단기 수급에 긍정적이지만, 회사 가치 자체는 변하지 않습니다.',
    },

    # ══════════════════════════════════════
    # 🔴 강한 악재 (-7 ~ -10)
    # ══════════════════════════════════════
    {
        'keywords': ['횡령ㆍ배임혐의발생', '횡령·배임', '횡령혐의', '배임혐의'],
        'score': -10, 'category': 'bad',
        'title': '횡령·배임 혐의 발생',
        'explain': '내부 통제가 무너졌다는 치명적 신호입니다. 거래정지 및 상장폐지 심사로 이어질 수 있어 극도의 주의가 필요합니다. 혐의 금액이 자기자본의 5% 이상이면 특히 위험.',
    },
    {
        'keywords': ['감자결정'],
        'score': -9, 'category': 'bad',
        'title': '감자(자본 감소) 결정',
        'explain': '누적 적자를 털기 위해 주주의 주식 수를 강제로 줄이는 매우 강한 악재입니다. 무상감자는 주주 피해가 직접적이고, 유상감자는 조금 덜 나쁩니다. 재무 상태가 심각하다는 신호.',
    },
    {
        'keywords': ['불성실공시법인지정', '상장적격성실질심사', '거래정지'],
        'exclude_keywords': ['해제', '우회상장', '미해당', '요건충족확인'],
        'score': -9, 'category': 'bad',
        'title': '거래정지·상장폐지 위험',
        'explain': '회사의 존속 자체가 흔들리는 신호. 최악의 경우 주식이 휴지조각이 될 수 있어 각별한 주의가 필요합니다.',
    },
    {
        'keywords': ['회생절차개시신청', '파산신청'],
        'score': -10, 'category': 'bad',
        'title': '회생·파산 관련',
        'explain': '법원의 회생 절차를 밟기 시작했거나 파산을 신청했다는 공시. 주식 가치가 거의 사라질 수 있는 최악의 상황입니다.',
    },

    # ══════════════════════════════════════
    # 🔴 악재 (-4 ~ -6)
    # ══════════════════════════════════════
    {
        'keywords': ['유상증자결정'],
        'score': -5, 'category': 'bad',
        'title': '유상증자 결정',
        'explain': '회사가 돈이 필요해 주주나 제3자에게 신주를 파는 행위입니다. 발행되는 신주만큼 기존 주주 지분이 희석됩니다. 단, 제3자 배정자가 유명 투자사이거나 시설 투자 목적이면 호재로 반전 가능. "누구에게 배정되는지" 확인이 핵심.',
    },
    {
        'keywords': ['재무제표재작성', '정정신고', '정정공시'],
        'score': -4, 'category': 'bad',
        'title': '재무제표 정정·재작성',
        'explain': '이미 발표한 실적이나 재무제표에 오류가 있어 고쳐 올린다는 뜻입니다. 회계 신뢰성에 금이 가는 신호. 정정 규모가 크면 투자자 신뢰 회복이 오래 걸립니다.',
    },
    {
        'keywords': ['감사의견거절', '감사범위제한', '한정의견'],
        'score': -8, 'category': 'bad',
        'title': '감사의견 문제',
        'explain': '외부 감사인이 회사 회계에 심각한 문제가 있다고 판단한 상황. 상장폐지 사유가 될 수 있는 중대한 악재입니다.',
    },
    {
        'keywords': ['자기주식처분결정'],
        'score': -4, 'category': 'bad',
        'title': '자사주 처분 결정',
        'explain': '회사가 가지고 있던 자기 주식을 시장에 내다 파는 결정입니다. 유통 주식 수가 늘어나 수급에 부담. 처분 대상이 임원·관계사이면 더 부정적으로 해석됩니다.',
    },

    # ══════════════════════════════════════
    # 🔴 약한 악재 (-1 ~ -3)
    # ══════════════════════════════════════
    {
        'keywords': ['전환사채권발행결정', '전환사채발행'],
        'score': -3, 'category': 'bad',
        'title': '전환사채(CB) 발행',
        'explain': '빚을 지는 동시에 나중에 주식으로 바뀔 수 있는 잠재 지분 희석 폭탄입니다. 자금 목적이 "운영자금"(월급·빚 갚기)이면 매우 위험. "시설투자"나 "타법인 취득"이면 중립적 우려 수준.',
    },
    {
        'keywords': ['신주인수권부사채권발행결정', '신주인수권부사채발행'],
        'score': -3, 'category': 'bad',
        'title': '신주인수권부사채(BW) 발행',
        'explain': 'CB와 비슷한 자금 조달로 잠재적 지분 희석 가능성이 있습니다. 자금 용도가 운영자금이면 재무 상태가 좋지 않다는 신호.',
    },
    {
        'keywords': ['교환사채권발행결정', '교환사채발행'],
        'score': -3, 'category': 'bad',
        'title': '교환사채(EB) 발행',
        'explain': '회사가 가진 다른 회사 주식(보통 관계사)과 교환 가능한 사채입니다. 잠재적 물량 부담이 있습니다.',
    },
    {
        'keywords': ['물적분할'],
        'score': -4, 'category': 'bad',
        'title': '물적분할 결정',
        'explain': '알짜 사업부를 100% 자회사로 떼어내는 것. 한국 시장에서 기존 주주의 권리를 침해한다는 강한 비판을 받아온 구조입니다. 나중에 자회사를 별도 상장하면 모회사 주주는 이중 피해. 대표적인 "주의 요망" 공시입니다.',
    },
    {
        'keywords': ['인적분할'],
        'score': 1, 'category': 'neutral',
        'title': '인적분할 결정',
        'explain': '기존 주주가 분할 후 양쪽 회사 지분을 그대로 받는 구조로 물적분할보다 주주 친화적입니다. 다만 지주회사 전환 목적이면 주식 교환 비율을 꼼꼼히 봐야 합니다.',
    },
    {
        'keywords': ['소송등의제기', '소송등의판결', '대규모소송'],
        'score': -2, 'category': 'bad',
        'title': '소송 관련',
        'explain': '법적 분쟁에 휘말렸거나 판결이 나왔다는 공시. 소송가액이 크거나 본업과 직결되면 실적·이미지 양쪽에 타격입니다.',
    },
    {
        'keywords': ['관리종목지정', '투자주의환기종목지정'],
        'score': -6, 'category': 'bad',
        'title': '관리종목·투자주의 지정',
        'explain': '거래소가 "이 회사 주의해서 보세요"라고 공식 경고한 상태. 개선되지 않으면 상장폐지로 이어질 수 있습니다.',
    },

    # ══════════════════════════════════════
    # 🟡 경영권·지배구조 (분석 필요)
    # ══════════════════════════════════════
    {
        'keywords': ['최대주주변경', '최대주주등의주식담보제공'],
        'score': -2, 'category': 'bad',
        'title': '최대주주 관련 변동',
        'explain': '지배구조가 바뀌거나 최대주주가 주식을 담보로 잡혔다는 공시. 담보 제공은 향후 반대매매 리스크를 뜻하므로 주의. 최대주주가 바뀌면 경영 방향 자체가 달라질 수 있어 파장이 큽니다.',
    },
    {
        'keywords': ['회사합병결정', '합병결정'],
        'score': 0, 'category': 'neutral',
        'title': '합병 결정',
        'explain': '다른 회사와 합치는 결정입니다. 합병 비율과 상대 기업의 체력에 따라 호재/악재가 갈립니다. 공시 본문의 "합병비율"과 "합병 상대 회사"를 반드시 확인하세요.',
    },
    {
        'keywords': ['주식교환ㆍ이전결정', '주식교환·이전결정', '주식의포괄적교환'],
        'score': 0, 'category': 'neutral',
        'title': '주식 교환·이전',
        'explain': '지주회사 전환이나 완전자회사화 과정에서 자주 나오는 공시. 교환 비율이 현재 주가보다 유리한지가 핵심입니다.',
    },
    {
        'keywords': ['타법인주식및출자증권취득결정'],
        'score': 1, 'category': 'neutral',
        'title': '타법인 주식 취득',
        'explain': '다른 회사 지분을 사는 결정입니다. 전략적 M&A면 호재, 정체불명 업체 인수나 경영권 방어용이면 현금 유출 우려. 취득 대상이 누구인지가 핵심입니다.',
    },
    {
        'keywords': ['타법인주식및출자증권처분결정'],
        'score': 1, 'category': 'neutral',
        'title': '타법인 주식 처분',
        'explain': '가지고 있던 다른 회사 지분을 파는 결정. 유동성 확보 목적인지, 비주력 사업 정리인지에 따라 해석이 달라집니다.',
    },
    {
        'keywords': ['영업양수결정', '영업양도결정'],
        'score': 0, 'category': 'neutral',
        'title': '영업 양수·양도',
        'explain': '사업부를 사거나 파는 결정. 핵심 사업 매각이면 악재, 부실 사업 정리면 호재. 대상 사업의 매출 비중을 꼭 확인하세요.',
    },

    # ══════════════════════════════════════
    # 🟡 지분 공시 (방향 확인 필요)
    # ══════════════════════════════════════
    {
        'keywords': ['주식등의대량보유상황보고서'],
        'score': 1, 'category': 'neutral',
        'title': '대량보유 지분 변동 (5% 이상)',
        'explain': '5% 이상 주주의 지분 변동 보고입니다. 누가 지분을 늘렸는지(호재) 줄였는지(약한 악재) 방향을 확인해야 합니다. 공시 본문의 "보유 목적"(경영참여 vs 단순투자)도 중요한 힌트.',
    },
    {
        'keywords': ['임원ㆍ주요주주특정증권등소유상황보고서', '임원·주요주주'],
        'score': 0, 'category': 'neutral',
        'title': '임원 지분 변동',
        'explain': '내부자의 주식 매매 보고. 임원이 자기 돈으로 사면 내부 확신(호재), 대량 매도는 고점 신호(약한 악재)로 해석되는 경우가 많습니다.',
    },

    # ══════════════════════════════════════
    # 🟡 스톡옵션·임원 보상
    # ══════════════════════════════════════
    {
        'keywords': ['주식매수선택권부여'],
        'score': -1, 'category': 'neutral',
        'title': '스톡옵션 부여',
        'explain': '임직원에게 미래에 주식을 싸게 살 권리를 주는 결정. 동기부여에는 좋지만 행사 시 지분 희석이 있습니다. 부여 규모가 전체 주식의 몇 %인지 확인 필요.',
    },
    {
        'keywords': ['주식매수선택권행사'],
        'score': -2, 'category': 'bad',
        'title': '스톡옵션 행사',
        'explain': '임직원이 부여받은 스톡옵션을 실제로 행사해 주식을 받아가는 단계. 신주가 발행돼 유통량이 늘어나는 희석 이벤트입니다.',
    },

    # ══════════════════════════════════════
    # 📋 일반 공시 (대부분 중립)
    # ══════════════════════════════════════
    {
        'keywords': ['사업보고서', '반기보고서', '분기보고서'],
        'score': 0, 'category': 'neutral',
        'title': '정기보고서 제출',
        'explain': '법정 정기 보고서 제출입니다. 내용 자체는 중립이지만, 본문의 재무 수치·감사의견·주요 사업 현황을 꼼꼼히 보면 호재/악재의 힌트가 숨어 있습니다.',
    },
    {
        'keywords': ['주주총회소집공고', '주주총회소집결의', '정기주주총회결과'],
        'score': 0, 'category': 'neutral',
        'title': '주주총회 관련',
        'explain': '주총 소집·안건·결과 공시입니다. 안건에 자본 변동(증자·감자·분할)이나 임원 교체가 있으면 별도 확인 필요.',
    },
    {
        'keywords': ['기타경영사항', '자율공시'],
        'score': 0, 'category': 'neutral',
        'title': '자율공시 (기타)',
        'explain': '회사가 자발적으로 알리는 경영 사항. 내용이 다양해서 제목만으론 판단이 어렵습니다. 본문 확인 권장.',
    },
    {
        'keywords': ['임시주주총회'],
        'score': 0, 'category': 'neutral',
        'title': '임시 주주총회',
        'explain': '정기 주총 외에 긴급 안건 처리를 위해 소집하는 주총. 보통 중요한 안건(합병·증자·임원 교체)이 있으니 안건 내용을 꼭 확인하세요.',
    },
    {
        'keywords': ['조회공시요구', '풍문또는보도에대한해명'],
        'score': -1, 'category': 'neutral',
        'title': '조회공시·해명',
        'explain': '거래소가 풍문이나 보도에 대해 "사실 관계 밝히라"고 요구한 것. 주가 급변동이 있었다는 뜻이며, 회사의 답변 내용이 핵심입니다.',
    },
    {
        'keywords': ['특수관계인거래'],
        'score': -1, 'category': 'neutral',
        'title': '특수관계인 거래',
        'explain': '계열사·임원 등과의 거래 공시. 정상 거래라면 중립이지만, 일감 몰아주기 패턴이면 주의가 필요합니다.',
    },
]


def analyze_disclosure(report_name):
    """
    공시 제목을 분석하여 점수·카테고리·해석을 반환합니다.

    Returns:
        dict: category, score, score_label, rule_title, explain, matched_keyword
    """
    if not report_name:
        return _default_result()

    for rule in RULES:
        for kw in rule['keywords']:
            if kw in report_name:
                exclude = rule.get('exclude_keywords', [])
                if any(ex in report_name for ex in exclude):
                    break
                return {
                    'category': rule['category'],
                    'score': rule['score'],
                    'score_label': _score_label(rule['score']),
                    'score_emoji': _score_emoji(rule['score']),
                    'rule_title': rule['title'],
                    'explain': rule['explain'],
                    'matched_keyword': kw,
                }

    return _default_result()


def _default_result():
    """룰에 매칭되지 않은 공시의 기본 처리."""
    return {
        'category': 'neutral',
        'score': 0,
        'score_label': '일반',
        'score_emoji': '📋',
        'rule_title': '일반 공시',
        'explain': '호재·악재로 분류되지 않은 일반 공시입니다. 정관 개정, 임원 선임, 첨부서류 제출 등이 여기 포함됩니다.',
        'matched_keyword': None,
    }


def _score_label(score):
    """점수를 한국어 라벨로 변환."""
    if score >= 7: return '강한 호재'
    if score >= 4: return '호재'
    if score >= 1: return '약한 호재'
    if score == 0: return '중립'
    if score >= -3: return '약한 악재'
    if score >= -6: return '악재'
    return '강한 악재'


def _score_emoji(score):
    """점수에 맞는 이모지를 반환."""
    if score >= 7: return '🎉'
    if score >= 4: return '😊'
    if score >= 1: return '🙂'
    if score == 0: return '😐'
    if score >= -3: return '😟'
    if score >= -6: return '😰'
    return '🚨'


# ===== 테스트 =====
def aggregate_score(signals):
    """
    공시 리스트를 받아 종합 점수와 해석을 반환합니다.
    임팩트 중심 로직:
    - 일반 공시(0점)는 평균 산출에서 제외 (호재·악재만 반영)
    - 악재 2.0배 가중 (손실 회피 선호)
    - 최근 가중치 완만하게 (0.9^i)
    - 호재·악재 개수가 많으면 임팩트 보너스

    Returns:
        dict: total_score, label, emoji, good_ratio, description, count
    """
    if not signals:
        return {
            'total_score': 0, 'total_score_fmt': '0',
            'label': '데이터 없음', 'emoji': '🔍',
            'good_ratio': 0, 'bad_ratio': 0, 'neutral_ratio': 0,
            'description': '최근 30일간 공시가 없습니다.',
            'count': 0, 'good_ct': 0, 'bad_ct': 0, 'neutral_ct': 0,
        }

    # 최신순 정렬
    sorted_signals = sorted(signals, key=lambda x: x.get('date', ''), reverse=True)

    # 호재·악재·일반 분리
    impact_signals = []  # 0점이 아닌 것 (평균 계산용)
    good_ct = bad_ct = neu_ct = 0

    for i, s in enumerate(sorted_signals):
        score = s.get('score', 0)
        if score >= 1:
            good_ct += 1
            impact_signals.append((i, score))
        elif score <= -1:
            bad_ct += 1
            impact_signals.append((i, score))
        else:
            neu_ct += 1

    total_ct = len(sorted_signals)

    # 임팩트 공시가 하나도 없으면 순수 중립
    if not impact_signals:
        return {
            'total_score': 0, 'total_score_fmt': '0.0',
            'label': '보통', 'emoji': '😐',
            'good_ratio': 0, 'bad_ratio': 0,
            'neutral_ratio': 100,
            'description': '최근 30일간 호재·악재 공시가 없는 조용한 기간입니다.',
            'count': total_ct, 'good_ct': 0, 'bad_ct': 0, 'neutral_ct': neu_ct,
        }

    # 평균 점수 계산 (임팩트 있는 공시만, 가중 평균)
    weighted_sum = 0
    weight_total = 0
    for original_idx, score in impact_signals:
        recency_weight = 0.9 ** min(original_idx, 15)  # 완만한 감소
        direction_weight = 2.0 if score < 0 else 1.0    # 악재 2배 가중
        final_weight = recency_weight * direction_weight
        weighted_sum += score * final_weight
        weight_total += recency_weight

    avg_score = weighted_sum / weight_total if weight_total else 0

    # 임팩트 보너스: 호재·악재 공시가 많으면 방향성을 강화
    # (예: 호재 4건이면 +0.5 가산, 악재 4건이면 -0.5 가산)
    impact_bonus = 0
    if good_ct >= 3: impact_bonus += 0.5
    if good_ct >= 5: impact_bonus += 0.5
    if bad_ct >= 3: impact_bonus -= 0.8
    if bad_ct >= 5: impact_bonus -= 0.8

    total_score = max(-10, min(10, round(avg_score + impact_bonus, 1)))

    good_ratio = round(good_ct / total_ct * 100) if total_ct else 0
    bad_ratio = round(bad_ct / total_ct * 100) if total_ct else 0
    neutral_ratio = 100 - good_ratio - bad_ratio

    label, emoji, description = _aggregate_label(total_score, bad_ct, good_ct)

    return {
        'total_score': total_score,
        'total_score_fmt': f"{'+' if total_score > 0 else ''}{total_score}",
        'label': label, 'emoji': emoji,
        'good_ratio': good_ratio, 'bad_ratio': bad_ratio,
        'neutral_ratio': neutral_ratio,
        'description': description,
        'count': total_ct,
        'good_ct': good_ct, 'bad_ct': bad_ct, 'neutral_ct': neu_ct,
    }


def _aggregate_label(score, bad_ct, good_ct):
    """종합 점수에 따른 라벨, 이모지, 설명 반환."""
    if score >= 4:
        return '아주 양호', '🎉', '최근 공시 흐름이 매우 긍정적입니다. 주주환원이나 실적 호재가 누적되고 있습니다.'
    if score >= 1.5:
        return '양호', '😊', '최근 공시가 전반적으로 긍정적입니다.'
    if score >= -1.5:
        if bad_ct > 0 and good_ct > 0:
            return '혼조', '😐', '호재와 악재가 섞여 있어 방향성이 불분명합니다. 개별 공시를 꼼꼼히 확인하세요.'
        return '보통', '😐', '특별한 호재도 악재도 눈에 띄지 않는 조용한 기간입니다.'
    if score >= -4:
        return '주의', '😟', '부정적 공시가 누적되고 있습니다. 내부 요인을 꼼꼼히 점검해야 합니다.'
    return '경고', '🚨', '악재 공시가 뚜렷하게 쌓여 있습니다. 보유 여부를 신중히 판단해야 합니다.'

def analyze_cb_with_purposes(cb_info):
    """
    CB 자금목적 데이터를 기반으로 점수 보정 + 경고 메시지 생성.

    Args:
        cb_info: dart_xray.parse_cb_purposes()의 반환값

    Returns:
        dict: {
            'score_adjust': 점수 보정치 (음수),
            'warnings': [경고 메시지 리스트],
            'flags': 주요 플래그,
            'summary': 한 줄 요약,
        }
    """
    if not cb_info:
        return None

    adjust = 0
    warnings = []
    flags = []

    op_ratio = cb_info['operating_ratio']
    debt_ratio = cb_info['debt_repay_ratio']
    fclt_ratio = cb_info['facility_ratio']
    dilution = cb_info['dilution_ratio']
    total_eok = cb_info['total_eok']

    # 1) 운영자금 비중
    if op_ratio > 70:
        adjust -= 5
        warnings.append(
            f"🚨 운영자금 비중 {op_ratio:.0f}% ({total_eok:.0f}억 중 "
            f"{total_eok * op_ratio / 100:.0f}억) — 재무 위기 신호"
        )
        flags.append('critical_operating')
    elif op_ratio > 40:
        adjust -= 3
        warnings.append(f"⚠️ 운영자금 비중 {op_ratio:.0f}% — 자금난 우려")
        flags.append('high_operating')
    elif op_ratio > 20:
        adjust -= 1
        warnings.append(f"운영자금 비중 {op_ratio:.0f}%")

    # 2) 채무상환자금 비중
    if debt_ratio > 50:
        adjust -= 3
        warnings.append(
            f"🚨 채무상환자금 비중 {debt_ratio:.0f}% — 빚 돌려막기 패턴"
        )
        flags.append('debt_rollover')
    elif debt_ratio > 20:
        adjust -= 1
        warnings.append(f"⚠️ 채무상환자금 비중 {debt_ratio:.0f}%")

    # 3) 시설자금 비중 (호재 완화)
    if fclt_ratio > 70:
        adjust += 2
        warnings.append(f"💡 시설자금 비중 {fclt_ratio:.0f}% — 성장 투자 성격")
        flags.append('growth_capex')
    elif fclt_ratio > 40:
        adjust += 1

    # 4) 희석률 분석
    if dilution > 20:
        adjust -= 3
        warnings.append(f"🚨 전환 시 기존 주식의 {dilution:.1f}% 희석 — 심각")
        flags.append('severe_dilution')
    elif dilution > 10:
        adjust -= 2
        warnings.append(f"⚠️ 전환 시 기존 주식의 {dilution:.1f}% 희석")
        flags.append('high_dilution')
    elif dilution > 5:
        adjust -= 1
        warnings.append(f"전환 시 기존 주식의 {dilution:.1f}% 희석")

    # 5) 요약 문장
    primary = cb_info['primary_purpose']
    if op_ratio > 70:
        summary = "⚠️ 운영자금 목적 CB — 재무 상태 위험 신호"
    elif debt_ratio > 50:
        summary = "⚠️ 채무상환 목적 CB — 빚 돌려막기 우려"
    elif fclt_ratio > 70:
        summary = "시설투자 목적 CB — 성장 투자 성격"
    else:
        summary = f"주요 용도: {primary}"

    return {
        'score_adjust': adjust,
        'warnings': warnings,
        'flags': flags,
        'summary': summary,
        'purposes_detail': cb_info['ratios'],
    }
def analyze_treasury_with_market_cap(treasury_info, market_cap):
    """
    자사주 (처분/취득/소각) 데이터를 시가총액 대비 비율로 점수 보정.

    점수 구간:
    - 처분: <0.1% → 0점 / 0.1~0.5% → 0점 / 0.5~2% → -1점 / 2~5% → -2점 / >5% → -3점
    - 취득: <0.1% → +1점 / 0.1~0.5% → +2점 / 0.5~2% → +4점 / 2~5% → +6점 / >5% → +8점
    - 소각: 취득과 동일

    Args:
        treasury_info: dart_xray.parse_treasury_data() 반환값
        market_cap: 시가총액 (원 단위, stock_info.get_stock_info()의 market_cap)

    Returns:
        dict: {
            'final_score': 시총 대비로 재조정된 절대 점수,
            'mcap_ratio': 시총 대비 비율 (%),
            'warnings': [메시지 리스트],
            'summary': 한 줄 요약,
            'tier': 규모 구간 ('무의미' / '소규모' / '중간' / '큰규모' / '대형'),
            'amount_eok': 처분/취득 금액 (억),
            'purpose': 목적/사유,
        }
    """
    if not treasury_info or not market_cap or market_cap <= 0:
        return None

    total_amount = treasury_info['total_amount']
    action = treasury_info['action']  # 'disposal' or 'acquisition'

    # 시총 대비 비율 (%)
    mcap_ratio = (total_amount / market_cap) * 100

    # 점수 구간 결정
    if mcap_ratio < 0.1:
        tier = '무의미'
        if action == 'disposal':
            final_score = 0
            tier_desc = '시총 대비 0.1% 미만 — 임직원 보상 등 운영 차원'
        else:  # acquisition / cremation
            final_score = 1
            tier_desc = '시총 대비 0.1% 미만 — 상징적 규모'
    elif mcap_ratio < 0.5:
        tier = '소규모'
        if action == 'disposal':
            final_score = 0
            tier_desc = '시총 대비 0.5% 미만 — 일반적인 임직원 RSU 수준'
        else:
            final_score = 2
            tier_desc = '시총 대비 0.5% 미만 — 소규모 주주환원'
    elif mcap_ratio < 2.0:
        tier = '중간'
        if action == 'disposal':
            final_score = -1
            tier_desc = '시총 대비 0.5~2% — 의미있는 규모의 처분'
        else:
            final_score = 4
            tier_desc = '시총 대비 0.5~2% — 의미있는 주주환원'
    elif mcap_ratio < 5.0:
        tier = '큰규모'
        if action == 'disposal':
            final_score = -2
            tier_desc = '시총 대비 2~5% — 큰 규모 처분, 수급 부담'
        else:
            final_score = 6
            tier_desc = '시총 대비 2~5% — 큰 규모 주주환원'
    else:
        tier = '대형'
        if action == 'disposal':
            final_score = -3
            tier_desc = '시총 대비 5%+ — 대형 처분, 주주가치 희석 우려'
        else:
            final_score = 8
            tier_desc = '시총 대비 5%+ — 대형 주주환원, 강력한 호재'

    # 경고 메시지 구성
    warnings = []
    amount_eok = treasury_info['total_eok']
    purpose = treasury_info.get('purpose', '').strip()

    warnings.append(
        f"📊 처분 규모: {amount_eok:,.1f}억 (시총 대비 {mcap_ratio:.3f}%)"
        if action == 'disposal'
        else f"📊 취득 규모: {amount_eok:,.1f}억 (시총 대비 {mcap_ratio:.3f}%)"
    )
    warnings.append(f"💡 {tier_desc}")

    if purpose and purpose != '명시되지 않음':
        # 목적 텍스트는 길 수 있으니 100자로 자름
        purpose_short = purpose[:80] + '…' if len(purpose) > 80 else purpose
        warnings.append(f"📝 사유: {purpose_short}")

    # 임직원 RSU/상여 키워드 자동 감지 (점수에는 이미 반영됨, 사용자 설명용)
    rsu_keywords = ['임직원', '상여', '성과', 'RSU', '인센티브', '보상', '스톡옵션']
    if action == 'disposal' and any(kw in purpose for kw in rsu_keywords):
        warnings.append("ℹ️ 임직원 보상 목적으로 보입니다 (악재 강도 완화 적용)")

    # 한 줄 요약
    if action == 'disposal':
        if mcap_ratio < 0.5:
            summary = f"미미한 규모의 처분 ({mcap_ratio:.2f}%) — 점수 영향 없음"
        elif mcap_ratio < 2.0:
            summary = f"중간 규모 처분 ({mcap_ratio:.2f}%) — 약한 악재"
        else:
            summary = f"⚠️ 큰 규모 처분 ({mcap_ratio:.2f}%) — 주주가치 희석 가능성"
    else:
        if mcap_ratio < 0.5:
            summary = f"소규모 취득/소각 ({mcap_ratio:.2f}%)"
        elif mcap_ratio < 2.0:
            summary = f"의미있는 주주환원 ({mcap_ratio:.2f}%)"
        else:
            summary = f"💎 대형 주주환원 ({mcap_ratio:.2f}%) — 강력한 호재"

    return {
        'final_score': final_score,
        'mcap_ratio': round(mcap_ratio, 3),
        'warnings': warnings,
        'summary': summary,
        'tier': tier,
        'amount_eok': amount_eok,
        'purpose': purpose,
        'action': action,
    }
# ============================================================
# 결론 카드 생성 (두괄식 종합 해석)
# ============================================================
# ==========================================
# 실적 공시 심층 분석 (옵션 B)
# ==========================================

def analyze_performance_score(performance):
    """
    실적 데이터를 점수로 변환.
    
    Args:
        performance: dart_xray.get_performance_analysis()의 반환값
    
    Returns:
        dict: {
            'score': 종합 점수 (-8 ~ +5),
            'label': 라벨,
            'emoji': 이모지,
            'rule_title': 룰 제목,
            'explain': 설명 메시지,
            'revenue_score': 매출 점수,
            'op_profit_score': 영업이익 점수,
            'has_analysis': True/False,
        }
    """
    if not performance or not performance.get('has_data'):
        return None
    
    revenue = performance.get('revenue', {})
    op_profit = performance.get('op_profit', {})
    
    # ==========================================
    # 1. 매출 점수
    # ==========================================
    revenue_score = 0
    revenue_msg = ''
    rev_pct = revenue.get('yoy_pct')
    
    if rev_pct is not None:
        if rev_pct <= -50:
            revenue_score = -8
            revenue_msg = f"매출 {rev_pct:.1f}% 급감 🚨"
        elif rev_pct <= -20:
            revenue_score = -4
            revenue_msg = f"매출 {rev_pct:.1f}% 감소 ⚠️"
        elif rev_pct <= -5:
            revenue_score = -2
            revenue_msg = f"매출 {rev_pct:.1f}% 소폭 감소"
        elif rev_pct < 5:
            revenue_score = 0
            revenue_msg = f"매출 {rev_pct:+.1f}% (보합)"
        elif rev_pct < 20:
            revenue_score = 2
            revenue_msg = f"매출 {rev_pct:+.1f}% 소폭 증가 📈"
        elif rev_pct < 50:
            revenue_score = 3
            revenue_msg = f"매출 {rev_pct:+.1f}% 증가 📈"
        else:
            revenue_score = 5
            revenue_msg = f"매출 {rev_pct:+.1f}% 급증 🚀"
    
    # ==========================================
    # 2. 영업이익 점수
    # ==========================================
    op_score = 0
    op_msg = ''
    op_pct = op_profit.get('yoy_pct')
    op_turn = op_profit.get('turn')
    
    # 흑자/적자 전환은 최우선
    if op_turn == 'to_loss':
        op_score = -8
        op_msg = "영업이익 적자전환 🚨"
    elif op_turn == 'to_profit':
        op_score = 5
        op_msg = "영업이익 흑자전환 🎉"
    elif op_pct is not None:
        if op_pct <= -50:
            op_score = -6
            op_msg = f"영업이익 {op_pct:.1f}% 급감 🚨"
        elif op_pct <= -20:
            op_score = -3
            op_msg = f"영업이익 {op_pct:.1f}% 감소 ⚠️"
        elif op_pct <= -5:
            op_score = -2
            op_msg = f"영업이익 {op_pct:.1f}% 소폭 감소"
        elif op_pct < 5:
            op_score = 0
            op_msg = f"영업이익 {op_pct:+.1f}% (보합)"
        elif op_pct < 20:
            op_score = 2
            op_msg = f"영업이익 {op_pct:+.1f}% 소폭 증가 📈"
        elif op_pct < 50:
            op_score = 3
            op_msg = f"영업이익 {op_pct:+.1f}% 증가 📈"
        else:
            op_score = 5
            op_msg = f"영업이익 {op_pct:+.1f}% 급증 🚀"
    
    # ==========================================
    # 3. 종합 점수 (매출 + 영업이익 평균, 영업이익에 가중치)
    # ==========================================
    if rev_pct is not None and op_pct is not None:
        # 둘 다 있으면: 영업이익 60% + 매출 40%
        final_score = op_score * 0.6 + revenue_score * 0.4
    elif op_pct is not None or op_turn:
        # 영업이익만 있으면
        final_score = op_score
    elif rev_pct is not None:
        # 매출만 있으면
        final_score = revenue_score
    else:
        return None
    
    final_score = round(final_score, 1)
    
    # ==========================================
    # 4. 라벨 + 이모지 + 룰 제목 + 설명
    # ==========================================
    if final_score <= -7:
        label = '실적 매우 부진'
        emoji = '🚨'
        rule_title = '실적 매우 부진'
    elif final_score <= -3:
        label = '실적 부진'
        emoji = '⚠️'
        rule_title = '실적 부진'
    elif final_score <= -1:
        label = '실적 다소 부진'
        emoji = '😟'
        rule_title = '실적 다소 부진'
    elif final_score < 1.5:
        label = '실적 보합'
        emoji = '➖'
        rule_title = '실적 보합'
    elif final_score < 4:
        label = '실적 양호'
        emoji = '📈'
        rule_title = '실적 양호'
    else:
        label = '실적 우수'
        emoji = '🚀'
        rule_title = '실적 우수'
    
    # 설명 메시지 조합
    parts = []
    if revenue_msg:
        parts.append(revenue_msg)
    if op_msg:
        parts.append(op_msg)
    
    if parts:
        explain = ' · '.join(parts)
    else:
        explain = '실적 데이터 분석 불가'
    
    return {
        'score': final_score,
        'label': label,
        'emoji': emoji,
        'rule_title': rule_title,
        'explain': explain,
        'revenue_score': revenue_score,
        'op_profit_score': op_score,
        'revenue_msg': revenue_msg,
        'op_profit_msg': op_msg,
        'has_analysis': True,
        'revenue_pct': rev_pct,
        'op_profit_pct': op_pct,
        'op_profit_turn': op_turn,
    }


def format_amount_korean(amount):
    """금액을 한국식 단위로 변환 (조/억)."""
    if amount is None:
        return '-'
    
    if abs(amount) >= 1_000_000_000_000:  # 1조 이상
        return f'{amount / 1_000_000_000_000:.1f}조원'
    elif abs(amount) >= 100_000_000:  # 1억 이상
        return f'{amount / 100_000_000:.0f}억원'
    elif abs(amount) >= 10_000:  # 1만 이상
        return f'{amount / 10_000:.0f}만원'
    else:
        return f'{amount:,}원'

def generate_conclusion(result_data):
    """
    분석 결과 전체를 받아 두괄식 결론 카드 데이터를 생성합니다.
    
    Args:
        result_data: dict - app.py의 _run_analysis 결과
            - signals_good, signals_bad, signals_neutral: list
            - summary: dict (aggregate_score 결과)
            - dividends: dict
            - stock: dict (네이버 금융 정보)
            - chart: dict (1개월 차트)
            - cbs: list (전환사채 이력)
            - cb_none: bool
    
    Returns:
        dict: {
            'tone': 'good'|'bad'|'neutral',
            'emoji': str,
            'label': str,
            'score_fmt': str,
            'headline': str,
            'good_signals': [str, ...],
            'warning_signals': [str, ...],
            'context_info': [str, ...],
        }
    """
    summary = result_data.get('summary', {})
    signals_good = result_data.get('signals_good', [])
    signals_bad = result_data.get('signals_bad', [])
    signals_neutral = result_data.get('signals_neutral', [])
    dividends = result_data.get('dividends', {})
    stock = result_data.get('stock', {}) or {}
    chart = result_data.get('chart', {}) or {}
    cbs = result_data.get('cbs', [])
    cb_none = result_data.get('cb_none', False)
    
    total_score = summary.get('total_score', 0)
    score_count = summary.get('count', 0)
    
    # ============================================================
    # 1. 톤 / 이모지 / 라벨 결정
    # ============================================================
    tone, emoji, label = _determine_tone(total_score, score_count, chart)
    
    # ============================================================
    # 2. Headline 생성 (한 줄 종합 평가)
    # ============================================================
    headline = _generate_headline(
        total_score, score_count, signals_good, signals_bad, chart
    )
    
    # ============================================================
    # 3. 좋은 신호 추출 (호재 TOP 3)
    # ============================================================
    good_signals = _extract_good_signals(signals_good, dividends, cb_none)
    
    # ============================================================
    # 4. 주의할 점 추출 (악재 TOP 3)
    # ============================================================
    warning_signals = _extract_warning_signals(signals_bad, cbs)
    
    # ============================================================
    # 5. 추가 정보 (주가 흐름, 카운트, 배당수익률)
    # ============================================================
    context_info = _extract_context_info(summary, chart, dividends, stock)
    
    # ============================================================
    # 6. 점수 포맷
    # ============================================================
    score_fmt = summary.get('total_score_fmt', '0.0')
    
    return {
        'tone': tone,
        'emoji': emoji,
        'label': label,
        'score_fmt': score_fmt,
        'headline': headline,
        'good_signals': good_signals,
        'warning_signals': warning_signals,
        'context_info': context_info,
        'has_any_data': bool(score_count or chart or stock.get('price')),
    }


def _determine_tone(total_score, score_count, chart):
    """톤/이모지/라벨 결정."""
    # 공시가 아예 없는 경우 - 차트로 판단
    if score_count == 0:
        if chart and chart.get('direction') == 'up':
            return 'neutral', '🟡', '관망'
        elif chart and chart.get('direction') == 'down':
            return 'neutral', '🟡', '주의'
        else:
            return 'neutral', '🟡', '데이터 부족'
    
    # 공시가 있는 경우 - 점수 기반
    if total_score <= -7:
        return 'bad', '🚨', '매우 위험'
    elif total_score <= -3:
        return 'bad', '🚨', '위험'
    elif total_score < 1.5:
        return 'neutral', '🟡', '주의'
    elif total_score < 4:
        return 'good', '🟢', '양호'
    else:
        return 'good', '🟢', '매우 양호'


def _generate_headline(total_score, score_count, signals_good, signals_bad, chart):
    """한 줄 종합 평가 헤드라인 생성."""
    # 공시가 아예 없는 경우
    if score_count == 0:
        if chart and chart.get('direction') == 'up':
            pct = chart.get('change_pct_fmt', '')
            return f"최근 30일 공시 없음. 주가는 {pct} 상승세."
        elif chart and chart.get('direction') == 'down':
            pct = chart.get('change_pct_fmt', '')
            return f"최근 30일 공시 없음. 주가는 {pct} 하락세, 시장 우려 신호."
        else:
            return "최근 30일간 공시 활동 및 주가 변동 거의 없음."
    
    # 매우 위험 (최악의 신호 우선)
    if total_score <= -7:
        # 가장 점수 낮은 악재 룰 확인
        worst_rule = signals_bad[0].get('rule_title', '') if signals_bad else ''
        if '회생' in worst_rule or '파산' in worst_rule:
            return "회생절차 진행 중. 거래정지 및 상장폐지 위험 매우 높음."
        if '거래정지' in worst_rule or '상장폐지' in worst_rule:
            return "거래정지 또는 상장폐지 위험 신호. 즉시 확인 필요."
        if '횡령' in worst_rule or '배임' in worst_rule:
            return "횡령·배임 혐의 발생. 내부 통제 무너진 치명적 신호."
        if '감자' in worst_rule:
            return "감자 결정. 주주 가치 강제 축소 신호."
        return f"심각한 악재 누적. 즉시 DART 원문 확인 권장."
    
    # 위험
    if total_score <= -3:
        return f"악재 {len(signals_bad)}건 발생. 주주 가치 또는 재무 부담 우려."
    
    # 주의 (혼재)
    if total_score < 1.5:
        if signals_good and signals_bad:
            return f"호재 {len(signals_good)}건 / 악재 {len(signals_bad)}건 혼재. 개별 공시 확인 권장."
        elif signals_bad:
            return f"악재 {len(signals_bad)}건 있으나 영향은 제한적."
        else:
            return "큰 호재나 악재 없는 일반적 공시 흐름."
    
    # 양호
    if total_score < 4:
        return f"호재 중심 공시 흐름. 별다른 위험 신호 없음."
    
    # 매우 양호
    return f"강한 호재 누적. 주주 환원 및 사업 모멘텀 양호."


def _extract_good_signals(signals_good, dividends, cb_none):
    """좋은 신호 추출 (최대 3개) - 일반 투자자 친화적 메시지."""
    result = []
    seen_messages = set()  # 중복 메시지 추적
    performance_added = False  # 실적 메시지 이미 추가했는지
    
    # 1. 호재 공시 TOP 2 (점수 높은 순)
    sorted_good = sorted(signals_good, key=lambda x: -x.get('score', 0))
    for sig in sorted_good[:5]:  # 후보 더 많이 본 후 중복 제외
        if len(result) >= 2:
            break
        
        rule_title = sig.get('rule_title', '')
        score = sig.get('score', 0)
        rule_title = sig.get('rule_title', '')
        score = sig.get('score', 0)
        
        # 실적 분석 결과 활용 (가장 우선)
        if sig.get('performance_analysis'):
            p = sig['performance_analysis']
            rev_pct = p.get('revenue_pct')
            op_pct = p.get('op_profit_pct')
            op_turn = p.get('op_profit_turn')
            
            # 친근한 메시지 생성
            parts = []
            if rev_pct is not None:
                if rev_pct > 0:
                    parts.append(f"매출 +{rev_pct:.0f}%")
                else:
                    parts.append(f"매출 {rev_pct:.0f}%")
            if op_turn == 'to_profit':
                parts.append("영업이익 흑자전환 🎉")
            elif op_pct is not None:
                if op_pct > 0:
                    parts.append(f"영업이익 +{op_pct:.0f}%")
                else:
                    parts.append(f"영업이익 {op_pct:.0f}%")
            
            metrics = ", ".join(parts)
            
            # 일반인 해석 추가
            if op_turn == 'to_profit':
                interp = "적자에서 흑자로 돌아섰어요 🚀"
            elif p.get('score', 0) >= 4:
                interp = "작년보다 훨씬 잘 벌고 있어요 🚀"
            elif p.get('score', 0) >= 2:
                interp = "작년보다 잘 벌고 있어요 📈"
            else:
                interp = "작년과 비슷한 흐름"
            
            # 실적 메시지는 한 번만 추가
            if performance_added:
                continue
            
            message = f"{rule_title}: {metrics} → {interp}"
            if message not in seen_messages:
                result.append(message)
                seen_messages.add(message)
                performance_added = True
            continue
        
        # 시총 대비 자사주 분석 결과 활용
        if sig.get('treasury_analysis'):
            t = sig['treasury_analysis']
            summary_text = t.get('summary', '')
            if summary_text:
                result.append(f"{rule_title} ({summary_text})")
                continue
        
        # 친근한 룰별 메시지
        friendly_msg = _get_friendly_good_message(rule_title, score)
        if friendly_msg:
            if friendly_msg not in seen_messages:
                result.append(friendly_msg)
                seen_messages.add(friendly_msg)
        else:
            fallback_msg = f"{rule_title} (+{score}점)"
            if fallback_msg not in seen_messages:
                result.append(fallback_msg)
                seen_messages.add(fallback_msg)
    
    # 2. 배당 정보 (양호하면 추가)
    if dividends and dividends.get('amount_per_100') and dividends.get('amount_per_100') != '-':
        yoy = dividends.get('yoy')
        amount = dividends.get('amount_per_100', '')
        if yoy is not None and yoy > 0:
            result.append(f"배당 +{yoy}% 증가 → 100주 보유 시 연 {amount} 수령 💰")
        elif amount:
            result.append(f"안정적인 배당 지급 (100주 보유 시 연 {amount}) 💰")
    
    # 3. 전환사채 없음 (재무 자신감)
    if cb_none and len(result) < 3:
        result.append("최근 3년간 전환사채 발행 없음 → 회사가 빚 없이 운영 중 ✨")
    
    return result[:3]


def _get_friendly_good_message(rule_title, score):
    """호재 룰을 일반인이 이해하기 쉬운 메시지로 변환."""
    friendly_map = {
        '자사주 소각 결정': '자사주 소각 → 내 주식 가치가 올라가는 가장 강한 주주환원 💎',
        '자사주 취득 결정': '회사가 자기 주식 매입 → 주가 방어 신호 🛡️',
        '자사주 취득 신탁 체결': '자사주 신탁 매입 → 주가 방어 의지 표시 🛡️',
        '무상증자 결정': '무상증자 → 회사가 재무 자신감 표시 (내 주식 수 증가) 🎁',
        '대규모 수주·공급계약': '굵직한 매출처 확보 → 향후 실적 기대감 ↑ 📦',
        '현금 배당 결정': '현금 배당 결정 → 주주에게 현금 환원 💵',
        '주식 배당 결정': '주식으로 배당 → 보유 주식 수 증가 🎁',
        '액면분할 결정': '주가 낮춰서 거래 활성화 시도 (개인 접근성 ↑) ✂️',
    }
    
    if rule_title in friendly_map:
        return friendly_map[rule_title]
    return None


def _extract_warning_signals(signals_bad, cbs):
    """주의할 점 추출 (최대 3개) - 일반 투자자 친화적 메시지."""
    result = []
    seen_messages = set()  # 중복 추적
    performance_added = False
    
    # 1. 악재 공시 TOP 3 (점수 낮은 순)
    sorted_bad = sorted(signals_bad, key=lambda x: x.get('score', 0))
    
    for sig in sorted_bad[:6]:  # 후보 더 많이 본 후 중복 제외
        if len(result) >= 3:
            break
        
        rule_title = sig.get('rule_title', '')
        score = sig.get('score', 0)
        rule_title = sig.get('rule_title', '')
        score = sig.get('score', 0)
        
        # 실적 분석 결과 활용 (가장 우선)
        if sig.get('performance_analysis'):
            p = sig['performance_analysis']
            rev_pct = p.get('revenue_pct')
            op_pct = p.get('op_profit_pct')
            op_turn = p.get('op_profit_turn')
            
            # 친근한 메시지 생성
            parts = []
            if rev_pct is not None:
                if rev_pct > 0:
                    parts.append(f"매출 +{rev_pct:.0f}%")
                else:
                    parts.append(f"매출 {rev_pct:.0f}%")
            if op_turn == 'to_loss':
                parts.append("영업이익 적자전환 🚨")
            elif op_pct is not None:
                if op_pct > 0:
                    parts.append(f"영업이익 +{op_pct:.0f}%")
                else:
                    parts.append(f"영업이익 {op_pct:.0f}%")
            
            metrics = ", ".join(parts)
            
            # 일반인 해석 추가
            if op_turn == 'to_loss':
                interp = "흑자에서 적자로 떨어졌어요. 보유 시 주의 ⚠️"
            elif p.get('score', 0) <= -7:
                interp = "실적이 크게 악화됐어요. 즉시 확인 필요 🚨"
            elif p.get('score', 0) <= -3:
                interp = "작년보다 사업이 부진해요"
            else:
                interp = "약간 부진하지만 큰 위험은 아님"
            
            if performance_added:
                continue
            
            message = f"{rule_title}: {metrics} → {interp}"
            if message not in seen_messages:
                result.append(message)
                seen_messages.add(message)
                performance_added = True
            continue
        
        # CB 자금목적 분석 결과 활용
        if sig.get('cb_analysis'):
            cb = sig['cb_analysis']
            summary_text = cb.get('summary', '')
            if summary_text:
                result.append(f"{rule_title} ({summary_text})")
                continue
        
        # 시총 대비 자사주 처분 등
        if sig.get('treasury_analysis'):
            t = sig['treasury_analysis']
            summary_text = t.get('summary', '')
            if summary_text:
                result.append(f"{rule_title} ({summary_text})")
                continue
        
        # 친근한 룰별 메시지
        friendly_msg = _get_friendly_bad_message(rule_title, score)
        if friendly_msg:
            if friendly_msg not in seen_messages:
                result.append(friendly_msg)
                seen_messages.add(friendly_msg)
        else:
            fallback_msg = f"{rule_title} ({score}점)"
            if fallback_msg not in seen_messages:
                result.append(fallback_msg)
                seen_messages.add(fallback_msg)
    
    # 2. 위험한 CB 이력 (운영자금 포함된 CB 있으면 경고)
    if cbs and len(result) < 3:
        warn_cbs = [cb for cb in cbs if cb.get('warn')]
        if warn_cbs:
            result.append(f"최근 3년간 운영자금 목적 전환사채 {len(warn_cbs)}건 → 회사가 돈이 부족했던 이력 ⚠️")
    
    return result[:3]


def _get_friendly_bad_message(rule_title, score):
    """악재 룰을 일반인이 이해하기 쉬운 메시지로 변환."""
    friendly_map = {
        '횡령·배임 혐의 발생': '횡령·배임 혐의 발생 → 거래정지·상장폐지 위험 매우 큼 🚨',
        '감자(자본 감소) 결정': '감자 결정 → 내 주식 수가 강제로 줄어듦. 재무 위기 신호 🚨',
        '거래정지·상장폐지 위험': '거래정지·상장폐지 위험 → 주식이 휴지조각 될 수 있음 🚨',
        '회생·파산 관련': '회생절차/파산 → 주식 가치 거의 사라질 수 있는 최악 🚨',
        '유상증자 결정': '유상증자 결정 → 신주 발행으로 내 주식 가치 희석 가능 ⚠️',
        '재무제표 정정·재작성': '재무제표 정정 → 회계 신뢰성에 의문 ⚠️',
        '감사의견 문제': '감사의견 문제 → 상장폐지 사유 가능성 🚨',
        '자사주 처분 결정': '자사주 처분 → 유통 주식 증가, 수급 부담 ⚠️',
        '전환사채(CB) 발행': '전환사채 발행 → 나중에 주식으로 바뀔 수 있는 잠재 희석 ⚠️',
        '신주인수권부사채(BW) 발행': 'BW 발행 → 잠재적 지분 희석 가능성 ⚠️',
        '교환사채(EB) 발행': '교환사채 발행 → 잠재적 물량 부담 ⚠️',
        '물적분할 결정': '물적분할 → 알짜 사업부 분리, 한국에서 비판 많은 구조 ⚠️',
        '소송 관련': '대규모 소송 발생 → 실적·이미지 타격 가능 ⚠️',
        '관리종목·투자주의 지정': '관리종목 지정 → 거래소가 공식 경고. 개선 안 되면 상장폐지 위험 🚨',
        '최대주주 관련 변동': '최대주주 변동/담보 → 경영 방향 변경 또는 반대매매 위험 ⚠️',
    }
    
    if rule_title in friendly_map:
        return friendly_map[rule_title]
    return None


def _extract_context_info(summary, chart, dividends, stock):
    """추가 정보 추출."""
    result = []
    
    # 1. 주가 흐름
    if chart and chart.get('change_pct_fmt'):
        pct = chart.get('change_pct_fmt', '')
        direction = chart.get('direction', 'flat')
        if direction == 'up':
            result.append(f"📈 1개월 주가 {pct} 상승")
        elif direction == 'down':
            result.append(f"📉 1개월 주가 {pct} 하락")
        else:
            result.append(f"📊 1개월 주가 보합 ({pct})")
    
    # 2. 공시 카운트 분포
    count = summary.get('count', 0)
    if count > 0:
        good_ct = summary.get('good_ct', 0)
        bad_ct = summary.get('bad_ct', 0)
        neutral_ct = summary.get('neutral_ct', 0)
        result.append(f"📋 30일 공시 {count}건 (호재 {good_ct} · 악재 {bad_ct} · 일반 {neutral_ct})")
    
    # 3. 배당수익률 (있으면)
    if dividends and dividends.get('yield_pct') is not None:
        yield_pct = dividends.get('yield_pct')
        result.append(f"💰 배당수익률 {yield_pct}% (현재가 기준)")
    
    # 4. 시가총액 (있으면)
    if stock and stock.get('market_cap_fmt') and stock.get('market_cap_fmt') != '-':
        mc = stock.get('market_cap_fmt')
        result.append(f"🏢 시가총액 {mc}")
    
    return result
if __name__ == '__main__':
    test_cases = [
        "주요사항보고서(자기주식소각결정)",
        "주요사항보고서(자기주식처분결정)",
        "주요사항보고서(자기주식취득결정)",
        "주요사항보고서(전환사채권발행결정)",
        "주요사항보고서(유상증자결정)",
        "주요사항보고서(감자결정)",
        "주요사항보고서(회사합병결정)",
        "단일판매ㆍ공급계약체결",
        "주식교환ㆍ이전결정(종속회사의주요경영사항)",
        "기타경영사항(자율공시)",
        "영업(잠정)실적(공정공시)",
        "주식등의대량보유상황보고서",
        "사업보고서",
        "현금ㆍ현물배당결정",
        "주식매수선택권부여에관한신고",
        "최대주주변경",
        "관리종목지정",
        "조회공시요구(풍문또는보도)에대한답변(미확정)",
        "정관일부개정",  # 룰 없는 경우
    ]
    print("=" * 70)
    print("🧪 공시 해석 엔진 v2.0 테스트 (룰 50+)")
    print("=" * 70)

    good_ct = bad_ct = neu_ct = 0
    for tc in test_cases:
        r = analyze_disclosure(tc)
        sign = '+' if r['score'] > 0 else ''
        print(f"\n📋 {tc}")
        print(f"   → [{r['score_label']}] {sign}{r['score']}점")
        print(f"   → {r['rule_title']}")
        if r['category'] == 'good': good_ct += 1
        elif r['category'] == 'bad': bad_ct += 1
        else: neu_ct += 1

    print(f"\n{'─'*70}")
    print(f"📊 총 {len(test_cases)}건: 호재 {good_ct} / 악재 {bad_ct} / 일반 {neu_ct}")