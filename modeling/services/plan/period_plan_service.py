from services.plan.menu_similarity_service import (
    get_recent_exposed_menus,
)

from services.plan.meal_selector_service import (
    increase_used_menu_count,
    select_alternative_menus,
    select_menu_for_meal,
)

from services.plan.plan_summary_service import (
    calculate_day_total_calories,
    calculate_day_total_estimated_cost,
    calculate_monthly_plan_summary,
)


def get_recent_day_window(diversity_penalty_strength: float) -> int:
    """
    다양성 강도에 따라 최근 며칠의 메뉴 반복을 피할지 결정한다.
    """

    if diversity_penalty_strength <= 0.1:
        return 0

    if diversity_penalty_strength <= 0.3:
        return 1

    return 2


def build_period_meal_plan(
    recommendations: list[dict],
    profile: dict,
    period_days: int,
    meal_count_per_day: int
) -> dict:
    """
    기간별 식단표를 생성한다.

    selected_menu와 alternative_menus를 모두 노출 메뉴로 간주해
    대표 식단과 대안 식단의 반복을 함께 줄인다.

    period_days 값에 따라 7일, 29일, 30일 등 다양한 기간의 식단을 생성할 수 있다.
    """

    required_meal_count = period_days * meal_count_per_day
    available_recommendation_count = len(recommendations)

    diversity_penalty_strength = profile.get(
        "diversity_penalty_strength",
        0.2,
    )

    recent_day_window = get_recent_day_window(
        diversity_penalty_strength,
    )

    warnings = []

    if available_recommendation_count < required_meal_count:
        warnings.append(
            f"요청한 {required_meal_count}개 식단 중 조건을 통과한 추천 메뉴가 "
            f"{available_recommendation_count}개입니다. 후보가 부족한 경우 일부 메뉴가 반복 배치될 수 있습니다."
        )

    days = []
    used_menu_count = {}

    for day_number in range(1, period_days + 1):
        meals = []

        exposed_menus = get_recent_exposed_menus(
            days=days,
            recent_day_window=recent_day_window,
        )

        for meal_order in range(1, meal_count_per_day + 1):
            selected_menu = select_menu_for_meal(
                recommendations=recommendations,
                exposed_menus=exposed_menus,
                used_menu_count=used_menu_count,
                diversity_penalty_strength=diversity_penalty_strength,
                profile=profile
            )

            alternative_menus = select_alternative_menus(
                recommendations=recommendations,
                selected_menu=selected_menu,
                exposed_menus=exposed_menus,
                used_menu_count=used_menu_count,
                diversity_penalty_strength=diversity_penalty_strength,
                alternative_count=2,
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
                "meal_order": meal_order,
                "selected_menu": selected_menu,
                "alternative_menus": alternative_menus,
            })

        days.append({
            "day": day_number,
            "meals": meals,
            "total_estimated_cost": calculate_day_total_estimated_cost(meals),
            "total_calories": calculate_day_total_calories(meals),
        })

    summary = calculate_monthly_plan_summary(days)

    return {
        "period_days": period_days,
        "meal_count_per_day": meal_count_per_day,
        "required_meal_count": required_meal_count,
        "available_recommendation_count": available_recommendation_count,
        "diversity_penalty_strength": diversity_penalty_strength,
        "recent_day_window": recent_day_window,
        "warnings": warnings,
        "summary": summary,
        "days": days,
    }


def build_monthly_plan(
    recommendations: list[dict],
    profile: dict,
    period_days: int,
    meal_count_per_day: int
) -> dict:
    """
    월간 식단표를 생성한다.

    기존 코드 호환성을 위해 build_period_meal_plan을 감싸는 wrapper 함수이다.
    """

    return build_period_meal_plan(
        recommendations=recommendations,
        profile=profile,
        period_days=period_days,
        meal_count_per_day=meal_count_per_day,
    )