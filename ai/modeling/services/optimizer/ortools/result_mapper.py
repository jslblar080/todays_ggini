from services.plan.meal_payload_service import build_menu_payload
from services.plan.plan_summary_service import calculate_monthly_plan_summary
from services.plan.meal_selector_service import (
    increase_used_menu_count,
    select_alternative_menus,
)
from services.plan.menu_similarity_service import get_recent_exposed_menus


DEFAULT_DIVERSITY_PENALTY_STRENGTH = 0.5
DEFAULT_RECENT_DAY_WINDOW = 3
DEFAULT_ALTERNATIVE_MENU_COUNT = 2


def build_ortools_monthly_plan(
    optimizer_result: dict,
    optimizer_input: dict,
    recommendations: list[dict],
    profile: dict,
) -> dict:
    """
    OR-Tools 선택 결과를 기존 monthly_plan 응답 구조에 맞게 변환한다.

    - OR-Tools가 확정한 selected_menu는 그대로 유지한다.
    - 전체 추천 후보를 활용해 selected_menu별 대안 메뉴를 후처리한다.
    - summary는 기존 calculate_monthly_plan_summary 함수를 재사용한다.
    """

    period_days = optimizer_input["period_days"]
    meal_count_per_day = optimizer_input["meal_count_per_day"]
    required_meal_count = period_days * meal_count_per_day

    diversity_penalty_strength = profile.get(
        "diversity_penalty_strength",
        DEFAULT_DIVERSITY_PENALTY_STRENGTH,
    )
    recent_day_window = profile.get(
        "recent_day_window",
        DEFAULT_RECENT_DAY_WINDOW,
    )

    selected_items = optimizer_result.get("selected_items", [])

    selected_items_by_day = {}

    for item in selected_items:
        day = item["day"]

        if day not in selected_items_by_day:
            selected_items_by_day[day] = []

        selected_items_by_day[day].append(item)

    days = []
    used_menu_count = {}

    for day in range(1, period_days + 1):
        day_items = selected_items_by_day.get(day, [])
        day_items = sorted(
            day_items,
            key=lambda item: item["meal_order"],
        )

        meals = []

        exposed_menus = get_recent_exposed_menus(
            days=days,
            recent_day_window=recent_day_window,
        )

        for item in day_items:
            selected_menu = item["selected_menu"]

            alternative_menus = select_alternative_menus(
                recommendations=recommendations,
                selected_menu=selected_menu,
                exposed_menus=exposed_menus,
                used_menu_count=used_menu_count,
                diversity_penalty_strength=diversity_penalty_strength,
                alternative_count=DEFAULT_ALTERNATIVE_MENU_COUNT,
            )

            increase_used_menu_count(
                used_menu_count=used_menu_count,
                menu=selected_menu,
                amount=1,
            )
            exposed_menus.append(selected_menu)

            for alternative_menu in alternative_menus:
                increase_used_menu_count(
                    used_menu_count=used_menu_count,
                    menu=alternative_menu,
                    amount=0.5,
                )
                exposed_menus.append(alternative_menu)

            meals.append({
                "meal_order": item["meal_order"],
                "selected_menu": build_menu_payload(selected_menu),
                "alternative_menus": [
                    build_menu_payload(alternative_menu)
                    for alternative_menu in alternative_menus
                ],
            })

        total_estimated_cost = sum(
            meal["selected_menu"].get("estimated_cost", 0) or 0
            for meal in meals
        )

        total_calories = sum(
            meal["selected_menu"].get("calories", 0) or 0
            for meal in meals
        )

        days.append({
            "day": day,
            "meals": meals,
            "total_estimated_cost": total_estimated_cost,
            "total_calories": total_calories,
        })

    summary = calculate_monthly_plan_summary(days)

    warnings = []

    if optimizer_result.get("solver_status") not in ["OPTIMAL", "FEASIBLE"]:
        warnings.append(
            "OR-Tools가 가능한 월간 식단 조합을 찾지 못했습니다."
        )

    return {
        "period_days": period_days,
        "meal_count_per_day": meal_count_per_day,
        "required_meal_count": required_meal_count,
        "available_recommendation_count": len(recommendations),
        "diversity_penalty_strength": diversity_penalty_strength,
        "recent_day_window": recent_day_window,
        "optimizer": {
            "enabled": True,
            "solver": "OR-Tools CP-SAT",
            "solver_status": optimizer_result.get("solver_status"),
            "objective_value": optimizer_result.get("objective_value"),
            "message": optimizer_result.get("message"),
            "config": optimizer_result.get("optimizer_config", {}),
        },
        "warnings": warnings,
        "summary": summary,
        "days": days,
    }
