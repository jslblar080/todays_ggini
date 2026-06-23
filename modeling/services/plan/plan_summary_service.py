def calculate_day_total_estimated_cost(meals: list[dict]) -> int:
    """
    하루 식단의 총 예상 비용을 계산한다.
    """

    total_cost = 0

    for meal in meals:
        selected_menu = meal.get("selected_menu", {})
        total_cost += selected_menu.get("estimated_cost", 0) or 0

    return total_cost


def calculate_day_total_calories(meals: list[dict]) -> int:
    """
    하루 식단의 총 칼로리를 계산한다.
    """

    total_calories = 0

    for meal in meals:
        selected_menu = meal.get("selected_menu", {})
        total_calories += selected_menu.get("calories", 0) or 0

    return total_calories


def calculate_monthly_plan_summary(days: list[dict]) -> dict:
    """
    월간 식단 결과를 요약한다.

    전체 monthly_plan을 다 펼쳐보지 않아도
    평균 칼로리, 평균 단백질, 총 비용, 메뉴 반복 수, 평균 점수를 확인할 수 있다.
    """

    selected_menus = []

    for day in days:
        for meal in day.get("meals", []):
            selected_menu = meal.get("selected_menu")

            if selected_menu:
                selected_menus.append(selected_menu)

    selected_menu_count = len(selected_menus)

    if selected_menu_count == 0:
        return {
            "selected_menu_count": 0,
            "unique_menu_count": 0,
            "duplicate_menu_count": 0,
            "total_estimated_cost": 0,
            "average_daily_cost": 0,
            "average_calories": 0,
            "average_protein": 0,
            "average_carbohydrate": 0,
            "average_fat": 0,
            "average_nutrition_score": 0,
            "average_budget_score": 0,
            "average_preference_score": 0,
            "average_difficulty_score": 0,
            "average_diversity_score": 0,
        }

    menu_ids = [
        menu.get("menu_id")
        for menu in selected_menus
        if menu.get("menu_id") is not None
    ]

    unique_menu_count = len(set(menu_ids))
    duplicate_menu_count = selected_menu_count - unique_menu_count

    total_estimated_cost = sum(
        menu.get("estimated_cost", 0) or 0
        for menu in selected_menus
    )

    total_calories = sum(
        menu.get("calories", 0) or 0
        for menu in selected_menus
    )

    total_protein = sum(
        menu.get("protein", 0) or 0
        for menu in selected_menus
    )

    total_carbohydrate = sum(
        menu.get("carbohydrate", 0) or 0
        for menu in selected_menus
    )

    total_fat = sum(
        menu.get("fat", 0) or 0
        for menu in selected_menus
    )

    total_nutrition_score = sum(
        menu.get("scores", {}).get("nutrition", 0) or 0
        for menu in selected_menus
    )

    total_budget_score = sum(
        menu.get("scores", {}).get("budget", 0) or 0
        for menu in selected_menus
    )

    total_preference_score = sum(
        menu.get("scores", {}).get("preference", 0) or 0
        for menu in selected_menus
    )

    total_difficulty_score = sum(
        menu.get("scores", {}).get("difficulty", 0) or 0
        for menu in selected_menus
    )

    total_diversity_score = sum(
        menu.get("scores", {}).get("diversity", 0) or 0
        for menu in selected_menus
    )

    day_count = len(days)

    average_daily_cost = 0

    if day_count > 0:
        average_daily_cost = round(total_estimated_cost / day_count)

    return {
        "selected_menu_count": selected_menu_count,
        "unique_menu_count": unique_menu_count,
        "duplicate_menu_count": duplicate_menu_count,
        "total_estimated_cost": total_estimated_cost,
        "average_daily_cost": average_daily_cost,
        "average_calories": round(total_calories / selected_menu_count, 2),
        "average_protein": round(total_protein / selected_menu_count, 2),
        "average_carbohydrate": round(total_carbohydrate / selected_menu_count, 2),
        "average_fat": round(total_fat / selected_menu_count, 2),
        "average_nutrition_score": round(total_nutrition_score / selected_menu_count, 2),
        "average_budget_score": round(total_budget_score / selected_menu_count, 2),
        "average_preference_score": round(total_preference_score / selected_menu_count, 2),
        "average_difficulty_score": round(total_difficulty_score / selected_menu_count, 2),
        "average_diversity_score": round(total_diversity_score / selected_menu_count, 2),
    }