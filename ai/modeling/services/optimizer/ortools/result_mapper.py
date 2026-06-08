from services.plan.meal_payload_service import build_menu_payload
from services.plan.plan_summary_service import calculate_monthly_plan_summary


def build_ortools_monthly_plan(
    optimizer_result: dict,
    optimizer_input: dict,
    recommendations: list[dict],
    profile: dict,
) -> dict:
    """
    OR-Tools 선택 결과를 기존 monthly_plan 응답 구조에 맞게 변환한다.

    1차 구현 범위:
    - selected_items를 day 단위로 묶는다.
    - 각 meal에는 기존 selected_menu payload를 넣는다.
    - summary는 기존 calculate_monthly_plan_summary 함수를 재사용한다.
    """

    period_days = optimizer_input["period_days"]
    meal_count_per_day = optimizer_input["meal_count_per_day"]
    required_meal_count = period_days * meal_count_per_day

    selected_items = optimizer_result.get("selected_items", [])

    selected_items_by_day = {}

    for item in selected_items:
        day = item["day"]

        if day not in selected_items_by_day:
            selected_items_by_day[day] = []

        selected_items_by_day[day].append(item)

    days = []

    for day in range(1, period_days + 1):
        day_items = selected_items_by_day.get(day, [])
        day_items = sorted(day_items, key=lambda item: item["meal_order"])

        meals = []

        for item in day_items:
            selected_menu = item["selected_menu"]

            meals.append({
                "meal_order": item["meal_order"],
                "selected_menu": build_menu_payload(selected_menu),
                "alternative_menus": [],
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
        warnings.append("OR-Tools가 가능한 월간 식단 조합을 찾지 못했습니다.")

    return {
        "period_days": period_days,
        "meal_count_per_day": meal_count_per_day,
        "required_meal_count": required_meal_count,
        "available_recommendation_count": len(recommendations),
        "diversity_penalty_strength": profile.get("diversity_penalty_strength"),
        "recent_day_window": None,
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
