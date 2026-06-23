import random

from services.recommendation.recommendation_service import recommend_menus

from services.plan.period_plan_service import (
    build_period_meal_plan,
)

from services.plan.plan_validation_service import (
    build_style_validation,
    build_difficulty_feasibility_diagnostics,
    enrich_style_validation,
)

from services.plan.plan_payload_service import (
    build_modeling_to_back_monthly_response,
)

from services.style.style_selection_service import (
    apply_selected_style_to_profile,
    build_selected_style_summary,
)


def build_monthly_plan_by_random_style(
    user_id: str,
    candidate_menus: list[dict],
    profile: dict,
    meal_style_response: dict
) -> dict:
    """
    테스트용으로 3일 샘플 스타일 중 하나를 랜덤 선택한 뒤,
    해당 스타일을 기준으로 월간 식단을 생성한다.
    """

    meal_style_candidates = meal_style_response.get("meal_style_candidates", [])

    if not meal_style_candidates:
        raise ValueError("meal_style_candidates가 비어 있어 월간 식단 스타일을 선택할 수 없습니다.")

    selected_style = random.choice(meal_style_candidates)

    selected_style_summary = build_selected_style_summary(selected_style)

    period_days = profile.get("period_days", 30)
    meal_count_per_day = profile.get("meal_count_per_day", 1)

    monthly_profile = apply_selected_style_to_profile(
        profile=profile,
        selected_style=selected_style_summary
    )

    recommendations = recommend_menus(
        menus=candidate_menus,
        profile=monthly_profile,
        top_n=len(candidate_menus)
    )

    monthly_plan = build_period_meal_plan(
        recommendations=recommendations,
        profile=monthly_profile,
        period_days=period_days,
        meal_count_per_day=meal_count_per_day
    )

    summary = monthly_plan.get("summary", {})

    base_style_validation = build_style_validation(
        selected_style=selected_style_summary,
        summary=summary,
        profile=monthly_profile
    )

    difficulty_feasibility_diagnostics = build_difficulty_feasibility_diagnostics(
        optimizer_snapshot=(
            monthly_plan
            .get("optimizer", {})
            .get("input_snapshot")
        )
    )

    style_validation = enrich_style_validation(
        style_validation=base_style_validation,
        selected_style=selected_style_summary,
        summary=summary,
        difficulty_feasibility_diagnostics=difficulty_feasibility_diagnostics
    )

    monthly_plan["style_validation"] = style_validation

    return build_modeling_to_back_monthly_response(
        user_id=user_id,
        selected_style=selected_style_summary,
        base_profile=profile,
        monthly_profile=monthly_profile,
        monthly_plan=monthly_plan,
        actual_recommendation_count=len(recommendations)
    )

