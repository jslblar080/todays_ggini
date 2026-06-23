from collections import Counter
from copy import deepcopy


def get_menu_cost(menu: dict) -> float:
    """
    메뉴의 예상 비용을 안전하게 가져온다.

    estimated_cost가 없으면 rag_estimated_cost를 사용하고,
    둘 다 없으면 매우 큰 값으로 처리해 정렬에서 뒤로 보낸다.
    """

    cost = menu.get("estimated_cost")

    if cost is None:
        cost = menu.get("rag_estimated_cost")

    if cost is None:
        return 10**12

    try:
        return float(cost)
    except (TypeError, ValueError):
        return 10**12


def get_menu_identity(menu: dict) -> str:
    """
    메뉴 반복을 판단하기 위한 식별자를 만든다.

    menu_id가 있으면 menu_id를 우선 사용하고,
    없으면 name/category 조합을 사용한다.
    """

    menu_id = menu.get("menu_id")

    if menu_id:
        return str(menu_id)

    name = menu.get("name", "")
    category = menu.get("category", "")

    return f"{name}|{category}"


def sort_menus_by_lowest_cost(menus: list[dict]) -> list[dict]:
    """
    후보 메뉴를 비용이 낮은 순서로 정렬한다.

    비용이 같으면 final_score가 높은 메뉴를 우선한다.
    """

    return sorted(
        menus,
        key=lambda menu: (
            get_menu_cost(menu),
            -float(menu.get("final_score") or 0),
        ),
    )


def select_least_cost_menus(
    recommendations: list[dict],
    required_meal_count: int,
    max_repeat_per_menu: int = 2,
) -> tuple[list[dict], dict]:
    """
    최저가 기준으로 월간 식단에 사용할 메뉴를 선택한다.

    가장 저렴한 메뉴를 max_repeat_per_menu까지 먼저 사용한 뒤,
    다음으로 저렴한 메뉴를 선택한다.

    즉, 비용 최소화 baseline의 의도에 맞게
    다양성보다 비용 최소화를 우선한다.
    """

    sorted_menus = sort_menus_by_lowest_cost(recommendations)
    selected_menus = []
    repeat_counter = Counter()

    for menu in sorted_menus:
        identity = get_menu_identity(menu)

        while (
            repeat_counter[identity] < max_repeat_per_menu
            and len(selected_menus) < required_meal_count
        ):
            selected_menus.append(deepcopy(menu))
            repeat_counter[identity] += 1

        if len(selected_menus) >= required_meal_count:
            break

    diagnostics = {
        "required_meal_count": required_meal_count,
        "selected_menu_count": len(selected_menus),
        "available_recommendation_count": len(recommendations),
        "max_repeat_per_menu": max_repeat_per_menu,
        "is_enough": len(selected_menus) >= required_meal_count,
        "shortage_count": max(required_meal_count - len(selected_menus), 0),
    }

    return selected_menus, diagnostics


def build_days_from_selected_menus(
    selected_menus: list[dict],
    period_days: int,
    meal_count_per_day: int,
) -> list[dict]:
    """
    선택된 메뉴 목록을 days 구조로 변환한다.
    """

    days = []
    menu_index = 0

    for day in range(1, period_days + 1):
        meals = []
        total_estimated_cost = 0
        total_calories = 0

        for meal_order in range(1, meal_count_per_day + 1):
            if menu_index >= len(selected_menus):
                break

            selected_menu = selected_menus[menu_index]
            menu_index += 1

            estimated_cost = get_menu_cost(selected_menu)
            calories = selected_menu.get("calories", 0) or 0

            total_estimated_cost += estimated_cost
            total_calories += calories

            meals.append(
                {
                    "meal_order": meal_order,
                    "selected_menu": selected_menu,
                    "alternative_menus": [],
                }
            )

        days.append(
            {
                "day": day,
                "meals": meals,
                "total_estimated_cost": round(total_estimated_cost, 2),
                "total_calories": round(total_calories, 2),
            }
        )

    return days


def calculate_average_score(
    selected_menus: list[dict],
    score_key: str,
) -> float | None:
    """
    selected_menus의 scores 내부 평균 점수를 계산한다.
    """

    scores = []

    for menu in selected_menus:
        menu_scores = menu.get("scores", {}) or {}
        score = menu_scores.get(score_key)

        if score is None:
            continue

        try:
            scores.append(float(score))
        except (TypeError, ValueError):
            continue

    if not scores:
        return None

    return round(sum(scores) / len(scores), 2)


def build_least_cost_summary(selected_menus: list[dict]) -> dict:
    """
    Least-cost baseline 결과 summary를 만든다.
    """

    selected_menu_count = len(selected_menus)
    identities = [get_menu_identity(menu) for menu in selected_menus]
    unique_menu_count = len(set(identities))
    duplicate_menu_count = selected_menu_count - unique_menu_count

    repeat_counter = Counter(identities)
    max_menu_repeat_count = max(repeat_counter.values()) if repeat_counter else 0

    total_estimated_cost = sum(get_menu_cost(menu) for menu in selected_menus)

    return {
        "selected_menu_count": selected_menu_count,
        "unique_menu_count": unique_menu_count,
        "duplicate_menu_count": duplicate_menu_count,
        "max_menu_repeat_count": max_menu_repeat_count,
        "total_estimated_cost": round(total_estimated_cost, 2),
        "average_daily_cost": None,
        "average_preference_score": calculate_average_score(
            selected_menus=selected_menus,
            score_key="preference",
        ),
        "average_budget_score": calculate_average_score(
            selected_menus=selected_menus,
            score_key="budget",
        ),
        "average_nutrition_score": calculate_average_score(
            selected_menus=selected_menus,
            score_key="nutrition",
        ),
        "average_final_score": round(
            sum(float(menu.get("final_score") or 0) for menu in selected_menus)
            / selected_menu_count,
            2,
        )
        if selected_menu_count
        else None,
    }


def build_least_cost_monthly_plan(
    recommendations: list[dict],
    profile: dict,
    period_days: int,
    meal_count_per_day: int,
) -> dict:
    """
    Least-cost Diet baseline 월간 식단을 생성한다.

    이 함수는 서비스 기본 정책이 아니라,
    OR-Tools 결과와 비교하기 위한 baseline 생성용이다.
    """

    required_meal_count = period_days * meal_count_per_day
    max_repeat_per_menu = int(profile.get("max_repeat_per_menu", 2) or 2)

    selected_menus, diagnostics = select_least_cost_menus(
        recommendations=recommendations,
        required_meal_count=required_meal_count,
        max_repeat_per_menu=max_repeat_per_menu,
    )

    summary = build_least_cost_summary(selected_menus)

    if period_days:
        summary["average_daily_cost"] = round(
            summary["total_estimated_cost"] / period_days,
            2,
        )

    days = build_days_from_selected_menus(
        selected_menus=selected_menus,
        period_days=period_days,
        meal_count_per_day=meal_count_per_day,
    )

    success = len(selected_menus) >= required_meal_count

    return {
        "baseline": {
            "name": "least_cost_diet",
            "description": "estimated_cost 기준 최저가 메뉴를 우선 선택하는 비교용 baseline",
            "success": success,
            "failure_reason": None if success else "candidate_insufficient",
            "diagnostics": diagnostics,
            "config": {
                "max_repeat_per_menu": max_repeat_per_menu,
            },
        },
        "period_days": period_days,
        "meal_count_per_day": meal_count_per_day,
        "required_meal_count": required_meal_count,
        "available_recommendation_count": len(recommendations),
        "summary": summary,
        "days": days,
    }
