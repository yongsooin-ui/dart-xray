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
        'keywords': ['단일판매ㆍ공급계약', '단일판매·공급계약', '공급계약체결'],
        'score': 5, 'category': 'good',
        'title': '대규모 수주·공급계약',
        'explain': '굵직한 매출처를 확보했다는 신호입니다. 계약 금액이 회사 최근 매출액 대비 크면 클수록 실적 기여도가 높아지는 호재. 공시 본문의 "매출액 대비 비율"을 꼭 확인하세요.',
    },
    {
        'keywords': ['영업(잠정)실적', '매출액또는손익구조30%', '영업실적등에대한전망'],
        'score': 4, 'category': 'good',
        'title': '실적 공시',
        'explain': '회사의 매출·영업이익 등을 발표하는 공시입니다. 전년 동기 대비 증감이 핵심이며, 30% 이상 변동 시 의무적으로 알리게 되어 있습니다. 숫자가 시장 예상치(컨센서스)보다 높으면 호재입니다.',
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