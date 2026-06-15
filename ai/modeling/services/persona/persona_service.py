from __future__ import annotations

from typing import Any

from services.persona.persona_catalog import PERSONA_CATALOG


ACTIVITY_LEVEL_MAP = {
    1: {
        "label": "거의 앉아서 생활해요",
        "tdee_factor": 1.2,
    },
    2: {
        "label": "가벼운 활동을 해요",
        "tdee_factor": 1.375,
    },
    3: {
        "label": "보통 활동을 해요",
        "tdee_factor": 1.55,
    },
    4: {
        "label": "활동이 많아요",
        "tdee_factor": 1.725,
    },
}

ACTIVITY_TEXT_TO_LEVEL = {
    "거의 앉아서 생활해요": 1,
    "가벼운 활동을 해요": 2,
    "보통 활동을 해요": 3,
    "활동이 많아요": 4,
}


def normalize_activity_level(activity_level: int | str) -> int:
    if isinstance(activity_level, int):
        return max(1, min(activity_level, 4))

    if isinstance(activity_level, str):
        if activity_level in ACTIVITY_TEXT_TO_LEVEL:
            return ACTIVITY_TEXT_TO_LEVEL[activity_level]

        try:
            return max(1, min(int(activity_level), 4))
        except ValueError:
            return 2

    return 2


def get_family_count_group(family_count: int) -> str:
    if family_count <= 1:
        return "1"

    if family_count == 2:
        return "2"

    if family_count == 3:
        return "3"

    return "4+"


def get_meal_budget_band(
    monthly_budget: int,
    family_count: int,
    meals_per_day: int,
    period_days: int = 30,
) -> str:
    """
    월 예산은 연속값이므로 1끼 예산 구간으로 정규화한다.
    """

    denominator = max(family_count, 1) * max(meals_per_day, 1) * period_days
    meal_budget = monthly_budget / denominator

    if meal_budget < 2500:
        return "very_low"

    if meal_budget < 4500:
        return "low"

    if meal_budget < 7000:
        return "medium"

    return "high"


def calculate_bmr(member: dict[str, Any]) -> float:
    """
    Mifflin-St Jeor 공식을 사용해 기초대사량(BMR)을 계산한다.

    남성:
    BMR = 10 × 체중kg + 6.25 × 키cm - 5 × 나이 + 5

    여성:
    BMR = 10 × 체중kg + 6.25 × 키cm - 5 × 나이 - 161
    """

    gender = member.get("gender")
    weight = float(member.get("weight", 0) or 0)
    height = float(member.get("height", 0) or 0)
    age = int(member.get("age", 0) or 0)

    if gender == "여":
        return (10 * weight) + (6.25 * height) - (5 * age) - 161

    return (10 * weight) + (6.25 * height) - (5 * age) + 5


def apply_goal_calorie_adjustment(
    tdee: float,
    bmr: float,
    purposes: list[str],
) -> int:
    """
    사용자 목적에 따라 하루 권장 칼로리를 계산한다.

    목적별 기준:
    - 다이어트: TDEE - 500kcal
      단, 최소 1200kcal 및 BMR의 95% 이상을 유지한다.
    - 고단백: TDEE + 300kcal
      근육량 증가 또는 단백질 중심 식단을 고려한다.
    - 그 외: TDEE 유지

    다이어트와 고단백이 함께 선택된 경우에는
    칼로리 제한 목적이 더 직접적이므로 다이어트 기준을 우선 적용한다.
    """

    if "다이어트" in purposes:
        adjusted = max(
            tdee - 500,
            1200,
            bmr * 0.95,
        )
    elif "고단백" in purposes:
        adjusted = tdee + 300
    else:
        adjusted = tdee

    adjusted = min(3500, adjusted)

    return round(adjusted)


def calculate_member_recommended_calorie(
    member: dict[str, Any],
    activity_level: int,
    purposes: list[str],
) -> dict[str, Any]:
    activity_config = ACTIVITY_LEVEL_MAP.get(
        activity_level,
        ACTIVITY_LEVEL_MAP[2],
    )

    gender = member.get("gender")
    bmr = calculate_bmr(member)
    tdee = bmr * activity_config["tdee_factor"]

    recommended_daily_calories = apply_goal_calorie_adjustment(
        tdee=tdee,
        bmr=bmr,
        purposes=purposes,
    )

    return {
        "nickname": member.get("nickname"),
        "gender": gender,
        "age": member.get("age"),
        "height": member.get("height"),
        "weight": member.get("weight"),
        "bmr": round(bmr, 2),
        "activity_level": activity_level,
        "activity_label": activity_config["label"],
        "estimated_tdee": round(tdee, 2),
        "recommended_daily_calories": recommended_daily_calories,
    }


def calculate_recommended_calories(
    family_members: list[dict[str, Any]],
    activity_level: int,
    purposes: list[str],
) -> dict[str, Any]:
    member_calories = [
        calculate_member_recommended_calorie(
            member=member,
            activity_level=activity_level,
            purposes=purposes,
        )
        for member in family_members
    ]

    if not member_calories:
        return {
            "recommended_daily_calories": 0,
            "member_calories": [],
        }

    recommended_daily_calories = round(
        sum(item["recommended_daily_calories"] for item in member_calories)
        / len(member_calories)
    )

    return {
        "recommended_daily_calories": recommended_daily_calories,
        "member_calories": member_calories,
    }


def build_request_condition(request_data: dict[str, Any]) -> dict[str, Any]:
    family_count = int(request_data.get("family_count", 1) or 1)
    monthly_budget = int(request_data.get("monthly_budget", 0) or 0)
    meals_per_day = int(request_data.get("meals_per_day", 1) or 1)
    activity_level = normalize_activity_level(request_data.get("activity_level"))

    return {
        "household_type": request_data.get("household_type"),
        "family_count_group": get_family_count_group(family_count),
        "meals_per_day": meals_per_day,
        "meal_budget_band": get_meal_budget_band(
            monthly_budget=monthly_budget,
            family_count=family_count,
            meals_per_day=meals_per_day,
        ),
        "activity_level": activity_level,
        "purposes": request_data.get("purpose", []) or [],
    }


def calculate_catalog_match_result(
    persona: dict[str, Any],
    request_condition: dict[str, Any],
) -> dict[str, Any]:
    """
    저장된 persona 조건과 사용자 입력 조건의 차이를 계산한다.

    임의 가중치를 두지 않고, 조건 불일치 개수와 목적 차이 개수만 사용한다.
    """

    conditions = persona.get("conditions", {})
    exact_match_count = 0
    mismatch_count = 0

    for key in [
        "household_type",
        "family_count_group",
        "meals_per_day",
        "meal_budget_band",
        "activity_level",
    ]:
        if conditions.get(key) == request_condition.get(key):
            exact_match_count += 1
        else:
            mismatch_count += 1

    persona_purposes = set(conditions.get("purposes", []))
    request_purposes = set(request_condition.get("purposes", []))

    matched_purpose_count = len(persona_purposes.intersection(request_purposes))
    missing_purpose_count = len(request_purposes - persona_purposes)
    extra_purpose_count = len(persona_purposes - request_purposes)

    exact_match_count += matched_purpose_count
    mismatch_count += missing_purpose_count + extra_purpose_count

    return {
        "match_count": exact_match_count,
        "mismatch_count": mismatch_count,
        "matched_purpose_count": matched_purpose_count,
        "missing_purpose_count": missing_purpose_count,
        "extra_purpose_count": extra_purpose_count,
    }


def build_persona_candidates(
    request_data: dict[str, Any],
    limit: int = 4,
) -> list[dict[str, Any]]:
    """
    사용자 입력과 가장 잘 맞는 페르소나 후보를 반환한다.

    household_type, family_count_group, meals_per_day, meal_budget_band,
    activity_level은 사용자가 이미 입력한 고정 조건이므로 반드시 일치하는
    catalog 후보만 사용한다.

    그 안에서 purpose 조합의 일치도를 기준으로 rank를 결정한다.
    """

    request_condition = build_request_condition(request_data)
    request_purposes = set(request_condition["purposes"])

    exact_condition_personas = []

    for persona in PERSONA_CATALOG:
        conditions = persona["conditions"]

        if conditions["household_type"] != request_condition["household_type"]:
            continue

        if conditions["family_count_group"] != request_condition["family_count_group"]:
            continue

        if conditions["meals_per_day"] != request_condition["meals_per_day"]:
            continue

        if conditions["meal_budget_band"] != request_condition["meal_budget_band"]:
            continue

        if conditions["activity_level"] != request_condition["activity_level"]:
            continue

        persona_purposes = set(conditions["purposes"])

        matched_purpose_count = len(request_purposes & persona_purposes)
        missing_purpose_count = len(request_purposes - persona_purposes)
        extra_purpose_count = len(persona_purposes - request_purposes)

        exact_condition_personas.append({
            "persona_id": persona["persona_id"],
            "persona_name": persona["persona_name"],
            "description": persona["description"],
            "summary": persona["summary"],
            "conditions": persona["conditions"],
            "match_count": 5 + matched_purpose_count,
            "mismatch_count": missing_purpose_count,
            "matched_purpose_count": matched_purpose_count,
            "missing_purpose_count": missing_purpose_count,
            "extra_purpose_count": extra_purpose_count,
        })

    exact_condition_personas = sorted(
        exact_condition_personas,
        key=lambda item: (
            item["missing_purpose_count"],
            item["extra_purpose_count"],
            -item["matched_purpose_count"],
            item["persona_id"],
        ),
    )

    return [
        {
            "rank": index,
            **persona,
        }
        for index, persona in enumerate(exact_condition_personas[:limit], start=1)
    ]


def simplify_persona_candidate(persona: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    백엔드와 프론트에 필요한 페르소나 표시 정보만 반환한다.

    summary는 프론트 카드/모달에 직접 노출되는 사용자 친화형 설명이다.
    """

    if not persona:
        return None

    return {
        "rank": persona.get("rank"),
        "persona_id": persona.get("persona_id"),
        "description": persona.get("description"),
        "summary": persona.get("summary"),
    }


def build_persona_profile_response(request_data: dict[str, Any]) -> dict[str, Any]:
    activity_level = normalize_activity_level(request_data.get("activity_level"))

    calorie_result = calculate_recommended_calories(
        family_members=request_data.get("family_members", []) or [],
        activity_level=activity_level,
        purposes=request_data.get("purpose", []) or [],
    )

    persona_candidates = build_persona_candidates(
        request_data=request_data,
        limit=4,
    )

    return {
        "id": request_data.get("id"),
        "request_type": "profile_build",
        "recommended_daily_calories": calorie_result["recommended_daily_calories"],
        "persona_candidates": [
            simplify_persona_candidate(persona)
            for persona in persona_candidates
        ],
    }

