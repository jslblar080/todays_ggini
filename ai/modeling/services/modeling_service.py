from copy import deepcopy
from services.profile.profile_service import build_user_profile_response

from services.rag.rag_request_service import build_rag_request
from services.rag.rag_client import request_candidate_menus_from_rag
from services.rag.rag_response_mapper import map_rag_response_to_candidate_menus

from services.style.meal_style_service import build_meal_style_candidates
from services.style.style_selection_service import (
    apply_selected_style_to_profile,
    build_selected_style_summary,
)

from services.recommendation.recommendation_service import recommend_menus

from services.plan.period_plan_service import build_period_meal_plan
from services.plan.plan_validation_service import (
    build_style_validation,
    enrich_style_validation,
)
from services.plan.plan_payload_service import build_modeling_to_back_monthly_response


def get_required_user_id(request_data: dict) -> str:
    """
    Back 요청에서 user_id를 안전하게 가져온다.
    """

    user_id = request_data.get("user_id")

    if not user_id:
        raise ValueError("user_id가 없어 모델링 요청을 처리할 수 없습니다.")

    return user_id


def extract_candidate_menus(mapped_rag_response) -> list[dict]:
    """
    RAG mapper 결과에서 candidate_menus 리스트를 안전하게 꺼낸다.

    mapper가 list를 바로 반환하는 경우와
    dict 안에 candidate_menus를 담아 반환하는 경우를 모두 처리한다.
    """

    if isinstance(mapped_rag_response, list):
        return mapped_rag_response

    if isinstance(mapped_rag_response, dict):
        candidate_menus = mapped_rag_response.get("candidate_menus", [])

        if isinstance(candidate_menus, list):
            return candidate_menus

    raise ValueError("RAG 응답에서 candidate_menus 리스트를 찾을 수 없습니다.")


def calculate_style_candidate_count(profile: dict) -> int:
    """
    3일 샘플 스타일 생성을 위한 후보 메뉴 개수를 계산한다.
    """

    sample_period_days = profile.get("sample_period_days", 3)
    meal_count_per_day = profile.get("meal_count_per_day", 1)

    # 스타일 후보는 3개 스타일을 만들어야 하므로 넉넉하게 3배 요청한다.
    return sample_period_days * meal_count_per_day * 3


def calculate_monthly_candidate_count(profile: dict) -> int:
    """
    월간 식단 생성을 위한 후보 메뉴 개수를 계산한다.
    """

    period_days = profile.get("period_days", 30)
    meal_count_per_day = profile.get("meal_count_per_day", 1)

    # 월간 식단은 대체 메뉴까지 필요하므로 3배 후보를 요청한다.
    return period_days * meal_count_per_day * 3


def copy_profile_with_relaxed_conditions(
    profile: dict,
    preferred_categories: list[str] | None = None,
    ingredient_preferences: list[str] | None = None,
    goals: list[str] | None = None,
    diversity_level: str | None = None,
) -> dict:
    """
    RAG 후보가 부족할 때 조건을 완화한 profile 복사본을 만든다.

    allergy_ingredients는 안전 조건이므로 절대 완화하지 않는다.
    """

    relaxed_profile = deepcopy(profile)

    if preferred_categories is not None:
        relaxed_profile["preferred_categories"] = preferred_categories

    if ingredient_preferences is not None:
        relaxed_profile["ingredient_preferences"] = ingredient_preferences

    if goals is not None:
        relaxed_profile["goals"] = goals

    if diversity_level is not None:
        relaxed_profile["diversity_level"] = diversity_level

    return relaxed_profile


def build_style_candidate_fallback_profiles(profile: dict) -> list[tuple[str, dict]]:
    """
    스타일 후보 생성을 위한 RAG fallback profile 목록을 만든다.

    fallback 순서:
    1. 선호 카테고리 완화
    2. 선호 재료군 완화
    3. 선호 카테고리와 선호 재료군 모두 완화

    단, 알레르기 조건은 유지한다.
    """

    return [
        (
            "preferred_categories_relaxed",
            copy_profile_with_relaxed_conditions(
                profile=profile,
                preferred_categories=["상관없음"],
            )
        ),
        (
            "ingredient_preferences_relaxed",
            copy_profile_with_relaxed_conditions(
                profile=profile,
                ingredient_preferences=[],
            )
        ),
        (
            "preferred_categories_and_ingredient_preferences_relaxed",
            copy_profile_with_relaxed_conditions(
                profile=profile,
                preferred_categories=["상관없음"],
                ingredient_preferences=[],
            )
        ),
    ]


def request_style_candidate_menus_with_fallback(
    request_data: dict,
    profile: dict,
    candidate_count: int
) -> tuple[list[dict], list[str]]:
    """
    스타일 후보 생성을 위한 RAG 후보 메뉴를 요청한다.

    원래 조건으로 후보가 없으면 선호 조건을 단계적으로 완화해 재요청한다.
    알레르기 조건은 완화하지 않는다.
    """

    warnings = []

    rag_request = build_rag_request(
        user_input=request_data,
        profile=profile,
        candidate_count=candidate_count,
    )

    rag_response = request_candidate_menus_from_rag(
        rag_request=rag_request,
    )

    mapped_rag_response = map_rag_response_to_candidate_menus(
        rag_response=rag_response,
    )

    candidate_menus = extract_candidate_menus(
        mapped_rag_response=mapped_rag_response,
    )

    if candidate_menus:
        return candidate_menus, warnings

    for _fallback_reason, fallback_profile in build_style_candidate_fallback_profiles(profile):
        fallback_rag_request = build_rag_request(
            user_input=request_data,
            profile=fallback_profile,
            candidate_count=candidate_count,
        )

        fallback_rag_response = request_candidate_menus_from_rag(
            rag_request=fallback_rag_request,
        )

        fallback_mapped_rag_response = map_rag_response_to_candidate_menus(
            rag_response=fallback_rag_response,
        )

        fallback_candidate_menus = extract_candidate_menus(
            mapped_rag_response=fallback_mapped_rag_response,
        )

        if fallback_candidate_menus:
            warnings.append(
                "선호 조건에 맞는 후보 메뉴가 부족하여 일부 선호 조건을 완화해 샘플 식단을 생성했습니다."
            )

            return fallback_candidate_menus, warnings

    warnings.append(
        "선호 조건을 완화했지만 추천 가능한 후보 메뉴를 찾지 못했습니다."
    )

    return [], warnings


def expand_ingredient_preferences(ingredient_preferences: list[str]) -> list[str]:
    """
    월간 식단 후보 부족 시 선호 재료군 탐색 범위를 넓힌다.

    사용자가 선택한 재료군은 유지하면서,
    허용 가능한 재료군을 추가해 RAG 후보 검색 범위를 확장한다.
    """

    fallback_ingredient_groups = [
        "육류",
        "해산물류",
        "식물성 단백질류",
        "채소류",
        "계란 및 유제품류",
    ]

    expanded_preferences = list(ingredient_preferences)

    for ingredient_group in fallback_ingredient_groups:
        if ingredient_group not in expanded_preferences:
            expanded_preferences.append(ingredient_group)

    return expanded_preferences


def build_monthly_candidate_fallback_profiles(
    profile: dict
) -> list[tuple[str, dict, int | None]]:
    """
    월간 식단 후보 생성을 위한 RAG fallback profile 목록을 만든다.

    fallback 순서:
    1. candidate_count 확대
    2. 선호 카테고리 완화
    3. 선호 재료군 확장
    4. 목표 조건을 핵심 목표 1개로 완화
    5. 다양성 수준을 보통으로 완화
    6. 카테고리, 재료군, 목표, 다양성 복합 완화

    단, 알레르기 조건은 절대 완화하지 않는다.
    """

    goals = profile.get("goals", [])
    primary_goal = goals[0] if goals else None

    expanded_ingredient_preferences = expand_ingredient_preferences(
        ingredient_preferences=profile.get("ingredient_preferences", []),
    )

    fallback_profiles = [
        (
            "candidate_count_expanded",
            profile,
            2,
        ),
        (
            "preferred_categories_relaxed",
            copy_profile_with_relaxed_conditions(
                profile=profile,
                preferred_categories=["다 좋아요"],
            ),
            None,
        ),
        (
            "ingredient_preferences_expanded",
            copy_profile_with_relaxed_conditions(
                profile=profile,
                ingredient_preferences=expanded_ingredient_preferences,
            ),
            None,
        ),
    ]

    if primary_goal:
        fallback_profiles.append(
            (
                "goals_relaxed_to_primary",
                copy_profile_with_relaxed_conditions(
                    profile=profile,
                    goals=[primary_goal],
                ),
                None,
            )
        )

    fallback_profiles.append(
        (
            "diversity_level_relaxed",
            copy_profile_with_relaxed_conditions(
                profile=profile,
                diversity_level="보통",
            ),
            None,
        )
    )

    if primary_goal:
        fallback_profiles.append(
            (
                "combined_relaxed",
                copy_profile_with_relaxed_conditions(
                    profile=profile,
                    goals=[primary_goal],
                    preferred_categories=["다 좋아요"],
                    ingredient_preferences=expanded_ingredient_preferences,
                    diversity_level="보통",
                ),
                2,
            )
        )

    return fallback_profiles


def request_monthly_candidate_menus_with_fallback(
    request_data: dict,
    profile: dict,
    candidate_count: int
) -> tuple[list[dict], dict]:
    """
    월간 식단 생성을 위한 RAG 후보 메뉴를 요청한다.

    원래 조건으로 후보가 없으면 조건을 단계적으로 완화해 재요청한다.
    알레르기 조건은 완화하지 않는다.
    """

    fallback_info = {
        "fallback_used": False,
        "fallback_steps": [],
        "warnings": [],
        "final_candidate_count": 0,
    }

    rag_request = build_rag_request(
        user_input=request_data,
        profile=profile,
        candidate_count=candidate_count,
    )

    rag_response = request_candidate_menus_from_rag(
        rag_request=rag_request,
    )

    mapped_rag_response = map_rag_response_to_candidate_menus(
        rag_response=rag_response,
    )

    candidate_menus = extract_candidate_menus(
        mapped_rag_response=mapped_rag_response,
    )

    if candidate_menus:
        fallback_info["final_candidate_count"] = len(candidate_menus)
        return candidate_menus, fallback_info

    for fallback_reason, fallback_profile, candidate_count_multiplier in (
        build_monthly_candidate_fallback_profiles(profile)
    ):
        fallback_candidate_count = candidate_count

        if candidate_count_multiplier:
            fallback_candidate_count = candidate_count * candidate_count_multiplier

        fallback_rag_request = build_rag_request(
            user_input=request_data,
            profile=fallback_profile,
            candidate_count=fallback_candidate_count,
        )

        fallback_rag_response = request_candidate_menus_from_rag(
            rag_request=fallback_rag_request,
        )

        fallback_mapped_rag_response = map_rag_response_to_candidate_menus(
            rag_response=fallback_rag_response,
        )

        fallback_candidate_menus = extract_candidate_menus(
            mapped_rag_response=fallback_mapped_rag_response,
        )

        fallback_info["fallback_used"] = True
        fallback_info["fallback_steps"].append(
            {
                "reason": fallback_reason,
                "candidate_count": fallback_candidate_count,
                "result_count": len(fallback_candidate_menus),
            }
        )

        if fallback_candidate_menus:
            fallback_info["final_candidate_count"] = len(fallback_candidate_menus)
            fallback_info["warnings"].append(
                "선호 조건에 맞는 후보 메뉴가 부족하여 일부 조건을 완화해 월간 식단을 생성했습니다."
            )

            return fallback_candidate_menus, fallback_info

    fallback_info["warnings"].append(
        "조건을 완화했지만 추천 가능한 월간 식단 후보 메뉴를 찾지 못했습니다."
    )

    return [], fallback_info


def build_candidate_empty_monthly_response(
    user_id: str,
    selected_style: dict,
    base_profile: dict,
    monthly_profile: dict,
    period_days: int,
    meal_count_per_day: int,
    fallback_info: dict,
) -> dict:
    """
    월간 식단 후보가 끝까지 없을 때 Back에 반환할 실패 응답을 만든다.
    """

    required_meal_count = period_days * meal_count_per_day

    return {
        "user_id": user_id,
        "request_type": "monthly_plan",
        "success": False,
        "failure_reason": "candidate_empty",
        "message": "현재 조건에 맞는 추천 후보가 부족하여 월간 식단을 생성할 수 없습니다.",
        "relaxation_suggestions": [
            "선호 카테고리를 넓혀주세요.",
            "선호 재료군을 추가해 주세요.",
            "목표 조건을 1~2개로 줄여주세요.",
            "알레르기를 제외한 선호 조건을 완화해 주세요.",
        ],
        "selected_style": selected_style,
        "meta": {
            "period_days": period_days,
            "meal_count_per_day": meal_count_per_day,
            "required_meal_count": required_meal_count,
            "available_recommendation_count": 0,
            "warnings": fallback_info.get("warnings", []),
            "fallback": fallback_info,
        },
        "modeling_profile": base_profile,
        "monthly_profile": monthly_profile,
        "monthly_plan": {
            "period_days": period_days,
            "meal_count_per_day": meal_count_per_day,
            "required_meal_count": required_meal_count,
            "available_recommendation_count": 0,
            "warnings": fallback_info.get("warnings", []),
            "summary": {
                "selected_menu_count": 0,
                "unique_menu_count": 0,
                "duplicate_menu_count": 0,
                "total_estimated_cost": 0,
                "average_daily_cost": 0,
            },
            "days": [],
        },
    }


def create_meal_style_candidates(request_data: dict) -> dict:
    """
    Back → Modeling 식단 스타일 후보 생성 진입점이다.

    처리 흐름:
    1. Back에서 받은 사용자 입력을 모델링 profile로 변환한다.
    2. profile을 기반으로 RAG 후보 요청을 생성한다.
    3. RAG 또는 Mock RAG에서 후보 메뉴를 가져온다.
    4. 후보 메뉴를 모델링 내부 candidate_menus 형식으로 변환한다.
    5. 3일치 식단 스타일 후보 3개를 생성한다.
    """

    user_id = get_required_user_id(request_data)

    profile_response = build_user_profile_response(
        request_data=request_data,
    )

    profile = profile_response["profile"]

    candidate_count = calculate_style_candidate_count(
        profile=profile,
    )

    candidate_menus, fallback_warnings = request_style_candidate_menus_with_fallback(
        request_data=request_data,
        profile=profile,
        candidate_count=candidate_count,
    )

    meal_count_per_day = profile.get("meal_count_per_day", 1)
    sample_period_days = profile.get("sample_period_days", 3)

    meal_style_response = build_meal_style_candidates(
        user_id=user_id,
        candidate_menus=candidate_menus,
        profile=profile,
        meal_count_per_day=meal_count_per_day,
        sample_period_days=sample_period_days,
    )

    meal_style_response["meta"]["warnings"] = (
        fallback_warnings
        + meal_style_response.get("meta", {}).get("warnings", [])
    )

    return meal_style_response


def create_monthly_plan(request_data: dict) -> dict:
    """
    Back → Modeling 월간 식단 생성 진입점이다.

    처리 흐름:
    1. Back에서 받은 사용자 입력을 모델링 profile로 변환한다.
    2. 사용자가 선택한 스타일을 월간 식단용 profile에 반영한다.
    3. 월간 식단에 필요한 RAG 후보 요청을 생성한다.
    4. RAG 또는 Mock RAG에서 후보 메뉴를 가져온다.
    5. 후보 메뉴를 사용자 조건과 선택 스타일 기준으로 re-rank한다.
    6. MMR 기반으로 기간별 식단을 생성한다.
    7. 스타일 반영 검증과 Back 응답 payload를 생성한다.
    """

    user_id = get_required_user_id(request_data)

    selected_style = request_data.get("selected_style", {})

    if not selected_style:
        raise ValueError("selected_style이 없어 월간 식단을 생성할 수 없습니다.")

    profile_response = build_user_profile_response(
        request_data=request_data,
    )

    base_profile = profile_response["profile"]

    selected_style_summary = build_selected_style_summary(
        selected_style=selected_style,
    )

    monthly_profile = apply_selected_style_to_profile(
        profile=base_profile,
        selected_style=selected_style_summary,
    )

    period_days = monthly_profile.get("period_days", 30)
    meal_count_per_day = monthly_profile.get("meal_count_per_day", 1)

    candidate_count = calculate_monthly_candidate_count(
        profile=monthly_profile,
    )

    candidate_menus, fallback_info = request_monthly_candidate_menus_with_fallback(
        request_data=request_data,
        profile=monthly_profile,
        candidate_count=candidate_count,
    )

    if not candidate_menus:
        return build_candidate_empty_monthly_response(
            user_id=user_id,
            selected_style=selected_style_summary,
            base_profile=base_profile,
            monthly_profile=monthly_profile,
            period_days=period_days,
            meal_count_per_day=meal_count_per_day,
            fallback_info=fallback_info,
        )

    recommendations = recommend_menus(
        menus=candidate_menus,
        profile=monthly_profile,
        top_n=len(candidate_menus),
    )

    monthly_plan = build_period_meal_plan(
        recommendations=recommendations,
        profile=monthly_profile,
        period_days=period_days,
        meal_count_per_day=meal_count_per_day,
    )

    summary = monthly_plan.get("summary", {})

    base_style_validation = build_style_validation(
        selected_style=selected_style_summary,
        summary=summary,
        profile=monthly_profile,
    )

    style_validation = enrich_style_validation(
        style_validation=base_style_validation,
        selected_style=selected_style_summary,
        summary=summary,
    )

    monthly_plan["style_validation"] = style_validation

    if fallback_info.get("warnings"):
        monthly_plan["warnings"] = (
            fallback_info.get("warnings", [])
            + monthly_plan.get("warnings", [])
        )

    monthly_plan["fallback"] = fallback_info

    return build_modeling_to_back_monthly_response(
        user_id=user_id,
        selected_style=selected_style_summary,
        base_profile=base_profile,
        monthly_profile=monthly_profile,
        monthly_plan=monthly_plan,
        actual_recommendation_count=len(recommendations),
    )