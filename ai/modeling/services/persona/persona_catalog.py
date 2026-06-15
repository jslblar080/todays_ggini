from itertools import combinations, product


HOUSEHOLD_TYPES = [
    "1인 가구",
    "다인 가구",
]

FAMILY_COUNT_GROUPS = [
    "1",
    "2",
    "3",
    "4+",
]

MEALS_PER_DAY_OPTIONS = [
    1,
    2,
    3,
    4,
    5,
]

PURPOSE_OPTIONS = [
    "식비 절약",
    "영양 균형",
    "다이어트",
    "고단백",
    "간편식",
    "맛 중심",
]

ACTIVITY_LEVEL_OPTIONS = [
    1,
    2,
    3,
    4,
]

MEAL_BUDGET_BANDS = [
    "very_low",
    "low",
    "medium",
    "high",
]


PURPOSE_LABELS = {
    "식비 절약": "절약",
    "영양 균형": "균형",
    "다이어트": "관리",
    "고단백": "단백",
    "간편식": "간편",
    "맛 중심": "맛",
}

BUDGET_LABELS = {
    "very_low": "초절약",
    "low": "절약",
    "medium": "표준",
    "high": "여유",
}

HOUSEHOLD_LABELS = {
    "1인 가구": "1인가구",
    "다인 가구": "가족",
}

ACTIVITY_LABELS = {
    1: "저활동",
    2: "가벼운활동",
    3: "보통활동",
    4: "높은활동",
}


def build_purpose_combinations() -> list[tuple[str, ...]]:
    """
    요리 목적은 1~3개 선택 가능하므로 가능한 모든 목적 조합을 만든다.
    """

    purpose_combinations = []

    for count in range(1, 4):
        purpose_combinations.extend(
            combinations(PURPOSE_OPTIONS, count)
        )

    return purpose_combinations


def build_description(
    household_type: str,
    meal_budget_band: str,
    purposes: tuple[str, ...],
) -> str:
    """
    프론트 카드에 노출할 짧은 페르소나 유형명을 생성한다.

    목적 조합이 많은 경우 더 구체적인 조합명을 우선 적용해
    rank 1~4 후보의 description이 최대한 다르게 보이도록 한다.
    """

    purpose_set = set(purposes)

    if household_type == "다인 가구":
        if {"식비 절약", "영양 균형", "간편식"}.issubset(purpose_set):
            return "가족알뜰 균형러형"
        if {"식비 절약", "고단백", "간편식"}.issubset(purpose_set):
            return "가족단백 예산러형"
        if {"영양 균형", "맛 중심", "간편식"}.issubset(purpose_set):
            return "가족입맛 해결사형"
        if {"다이어트", "고단백", "간편식"}.issubset(purpose_set):
            return "가족건강 루틴러형"

        if "식비 절약" in purpose_set and "영양 균형" in purpose_set:
            return "가족예산 수비대형"
        if "간편식" in purpose_set:
            return "가족식단 해결사형"
        if "맛 중심" in purpose_set:
            return "가족입맛 조율형"
        if "고단백" in purpose_set:
            return "가족단백 충전형"
        if "다이어트" in purpose_set:
            return "가족건강 관리형"
        return "가족균형 식단형"

    # 1인 가구 3개 목적 조합
    if {"다이어트", "간편식", "맛 중심"}.issubset(purpose_set):
        return "맛챙긴 실속관리형"

    if {"다이어트", "고단백", "간편식"}.issubset(purpose_set):
        return "단백관리 속전속결형"

    if {"영양 균형", "다이어트", "간편식"}.issubset(purpose_set):
        return "균형관리 루틴형"

    if {"식비 절약", "다이어트", "간편식"}.issubset(purpose_set):
        return "절약관리 생존형"

    if {"식비 절약", "고단백", "간편식"}.issubset(purpose_set):
        return "알뜰단백 생존형"

    if {"영양 균형", "간편식", "맛 중심"}.issubset(purpose_set):
        return "맛균형 간편러형"

    # 1인 가구 2개 목적 조합
    if "식비 절약" in purpose_set and "간편식" in purpose_set:
        return "알뜰간편 생존형"

    if "식비 절약" in purpose_set and "고단백" in purpose_set:
        return "가성비 단백질형"

    if "식비 절약" in purpose_set:
        return "가성비 절약형"

    if "다이어트" in purpose_set and "간편식" in purpose_set and meal_budget_band in ["very_low", "low"]:
        return "실속관리 루틴형"

    if "다이어트" in purpose_set and "간편식" in purpose_set:
        return "간편관리 루틴형"

    if "다이어트" in purpose_set and "고단백" in purpose_set:
        return "탄탄관리 단백형"

    if "고단백" in purpose_set and "간편식" in purpose_set:
        return "단백질 속전속결형"

    if "고단백" in purpose_set:
        return "단백질 충전형"

    if "영양 균형" in purpose_set and "간편식" in purpose_set:
        return "간편균형 루틴형"

    if "영양 균형" in purpose_set and "맛 중심" in purpose_set:
        return "맛있는 균형형"

    if "영양 균형" in purpose_set:
        return "균형식단 루틴형"

    if "간편식" in purpose_set and "맛 중심" in purpose_set:
        return "맛있는 간편형"

    if "간편식" in purpose_set:
        return "초간단 해결형"

    if "맛 중심" in purpose_set:
        return "입맛만족 추구형"

    return "맞춤식단 탐색형"


def build_persona_id(
    household_type: str,
    family_count_group: str,
    meal_budget_band: str,
    meals_per_day: int,
    purposes: tuple[str, ...],
    activity_level: int,
) -> str:
    """
    페르소나 조건 조합을 안정적인 persona_id로 변환한다.
    """

    household_key = "single" if household_type == "1인 가구" else "multi"

    purpose_key_map = {
        "식비 절약": "절약",
        "영양 균형": "균형",
        "다이어트": "관리",
        "고단백": "단백",
        "간편식": "간편",
        "맛 중심": "맛",
    }

    purpose_key = "_".join(
        purpose_key_map.get(purpose, purpose)
        for purpose in purposes
    )

    return (
        f"persona_{household_key}"
        f"_family{family_count_group}"
        f"_meal{meals_per_day}"
        f"_{meal_budget_band}"
        f"_act{activity_level}"
        f"_{purpose_key}"
    )



def build_persona_name(
    household_type: str,
    meal_budget_band: str,
    purposes: tuple[str, ...],
    activity_level: int,
) -> str:
    purpose_text = "·".join(
        PURPOSE_LABELS[purpose]
        for purpose in purposes
    )

    return (
        f"{HOUSEHOLD_LABELS[household_type]} "
        f"{BUDGET_LABELS[meal_budget_band]} "
        f"{purpose_text} "
        f"{ACTIVITY_LABELS[activity_level]}"
    )


def build_persona_summary(
    household_type: str,
    family_count_group: str,
    meal_budget_band: str,
    meals_per_day: int,
    purposes: tuple[str, ...],
    activity_level: int,
) -> str:
    """
    프론트에 노출할 사용자 친화형 페르소나 summary를 생성한다.

    목적뿐 아니라 예산 구간, 하루 끼니 수, 가구 형태를 함께 반영해
    페르소나의 특징이 드러나는 약 50~70자 문장으로 구성한다.
    """

    purpose_set = set(purposes)

    if household_type == "1인 가구":
        user_label = "자취생"
    elif family_count_group == "2":
        user_label = "소가구 식단 관리자"
    else:
        user_label = "가족 식단 관리자"

    if meals_per_day >= 4:
        meal_phrase = "하루 여러 끼를 든든히 챙기지만"
    elif meals_per_day == 3:
        meal_phrase = "삼시세끼 루틴을 챙기면서"
    elif meals_per_day == 2:
        meal_phrase = "하루 두 끼를 알차게 챙기며"
    else:
        meal_phrase = "하루 한 끼를 집중해서 챙기며"

    if meal_budget_band in ["very_low", "low"]:
        budget_phrase = "예산 방어도 놓치지 않는"
        action_phrase = "부담 적은 식단으로 실천을 도와드릴게요!"
    elif meal_budget_band == "medium":
        budget_phrase = "예산과 만족도의 균형을 찾는"
        action_phrase = "꾸준히 이어갈 수 있는 식단을 추천할게요!"
    else:
        budget_phrase = "먹는 만족도에 조금 더 투자하는"
        action_phrase = "만족도 높은 식단으로 구성해드릴게요!"

    if {"다이어트", "간편식", "맛 중심"}.issubset(purpose_set):
        focus_phrase = "관리식도 맛있어야 오래 간다고 믿는"
    elif {"다이어트", "고단백", "간편식"}.issubset(purpose_set):
        focus_phrase = "간단히 먹어도 단백질과 관리는 챙기려는"
    elif {"영양 균형", "다이어트", "간편식"}.issubset(purpose_set):
        focus_phrase = "쉽게 만들면서 균형 잡힌 관리식을 원하는"
    elif {"식비 절약", "다이어트", "간편식"}.issubset(purpose_set):
        focus_phrase = "예산을 지키며 가벼운 한 끼를 챙기려는"
    elif {"식비 절약", "고단백", "간편식"}.issubset(purpose_set):
        focus_phrase = "돈은 아끼고 단백질은 빠르게 챙기려는"
    elif {"영양 균형", "간편식", "맛 중심"}.issubset(purpose_set):
        focus_phrase = "맛과 균형을 간편하게 챙기고 싶은"
    elif "식비 절약" in purpose_set and "간편식" in purpose_set:
        focus_phrase = "빠르고 알뜰한 한 끼를 원하는"
    elif "식비 절약" in purpose_set and "고단백" in purpose_set:
        focus_phrase = "돈은 아끼고 단백질은 챙기려는"
    elif "식비 절약" in purpose_set:
        focus_phrase = "가성비를 최우선으로 보는"
    elif "다이어트" in purpose_set and "간편식" in purpose_set and meals_per_day >= 4:
        focus_phrase = "많이 먹어도 관리 루틴은 지키고 싶은"
    elif "다이어트" in purpose_set and "간편식" in purpose_set:
        focus_phrase = "관리와 간편함을 동시에 원하는"
    elif "다이어트" in purpose_set and "고단백" in purpose_set:
        focus_phrase = "탄탄한 관리식을 챙기고 싶은"
    elif "고단백" in purpose_set and "간편식" in purpose_set:
        focus_phrase = "간단하지만 단백질은 포기 못 하는"
    elif "고단백" in purpose_set:
        focus_phrase = "단백질 충전을 중요하게 보는"
    elif "영양 균형" in purpose_set and "간편식" in purpose_set:
        focus_phrase = "쉽게 만들면서 균형도 챙기려는"
    elif "영양 균형" in purpose_set and "맛 중심" in purpose_set:
        focus_phrase = "맛과 균형을 함께 원하는"
    elif "영양 균형" in purpose_set:
        focus_phrase = "영양 밸런스를 중요하게 보는"
    elif "간편식" in purpose_set and "맛 중심" in purpose_set:
        focus_phrase = "맛있고 간단한 한 끼를 찾는"
    elif "간편식" in purpose_set:
        focus_phrase = "복잡한 조리 없이 해결하고 싶은"
    elif "맛 중심" in purpose_set:
        focus_phrase = "식사의 즐거움을 중요하게 보는"
    else:
        focus_phrase = "내 조건에 맞는 식단을 찾는"

    return (
        f"{meal_phrase} {budget_phrase} {focus_phrase} "
        f"{user_label}이에요. {action_phrase}"
    )


def build_persona_catalog() -> list[dict]:
    """
    가능한 가구 형태, 가구원 수 그룹, 하루 식사 수, 목적 조합,
    활동량, 1끼 예산 구간 조합을 모두 생성한다.

    단, 가구 형태와 가구원 수 그룹은 실제 가능한 조합만 포함한다.
    - 1인 가구: family_count_group == "1"
    - 다인 가구: family_count_group in ["2", "3", "4+"]
    """

    catalog = []
    purpose_combinations = build_purpose_combinations()

    for (
        household_type,
        family_count_group,
        meals_per_day,
        meal_budget_band,
        activity_level,
        purposes,
    ) in product(
        HOUSEHOLD_TYPES,
        FAMILY_COUNT_GROUPS,
        MEALS_PER_DAY_OPTIONS,
        MEAL_BUDGET_BANDS,
        ACTIVITY_LEVEL_OPTIONS,
        purpose_combinations,
    ):
        if household_type == "1인 가구" and family_count_group != "1":
            continue

        if household_type == "다인 가구" and family_count_group == "1":
            continue

        persona = {
            "persona_id": build_persona_id(
                household_type=household_type,
                family_count_group=family_count_group,
                meal_budget_band=meal_budget_band,
                meals_per_day=meals_per_day,
                purposes=purposes,
                activity_level=activity_level,
            ),
            "persona_name": build_persona_name(
                household_type=household_type,
                meal_budget_band=meal_budget_band,
                purposes=purposes,
                activity_level=activity_level,
            ),
            "description": build_description(
                household_type=household_type,
                meal_budget_band=meal_budget_band,
                purposes=purposes,
            ),
            "summary": build_persona_summary(
                household_type=household_type,
                family_count_group=family_count_group,
                meal_budget_band=meal_budget_band,
                meals_per_day=meals_per_day,
                purposes=purposes,
                activity_level=activity_level,
            ),
            "conditions": {
                "household_type": household_type,
                "family_count_group": family_count_group,
                "meals_per_day": meals_per_day,
                "meal_budget_band": meal_budget_band,
                "activity_level": activity_level,
                "purposes": list(purposes),
            },
        }

        catalog.append(persona)

    return catalog


PERSONA_CATALOG = build_persona_catalog()
