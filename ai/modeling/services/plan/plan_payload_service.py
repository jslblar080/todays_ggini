from datetime import datetime


def build_modeling_profile_summary(profile: dict) -> dict:
    """
    Back에서 저장하거나 추적하기 좋은 모델링 프로필 요약 정보를 만든다.

    사용자 입력값과 모델링 계산값을 함께 포함한다.
    """

    return {
        "goals": profile.get("goals", []),
        "monthly_budget": profile.get("monthly_budget"),
        "period_days": profile.get("period_days"),
        "meal_count_per_day": profile.get("meal_count_per_day"),
        "cooking_skill": profile.get("cooking_skill"),
        "preferred_categories": profile.get("preferred_categories", []),
        "diversity_level": profile.get("diversity_level"),
        "ingredient_preferences": profile.get("ingredient_preferences", []),
        "allergy_ingredients": profile.get("allergy_ingredients", []),

        "budget_period_days": profile.get("budget_period_days"),
        "sample_period_days": profile.get("sample_period_days"),
        "meal_budget": profile.get("meal_budget"),
        "weights": profile.get("weights", {}),
        "max_difficulty": profile.get("max_difficulty"),
        "diversity_penalty_strength": profile.get("diversity_penalty_strength"),
    }


def build_applied_style_adjustment(
    base_profile: dict,
    monthly_profile: dict,
    selected_style: dict
) -> dict:
    """
    선택한 스타일이 월간 식단 가중치에 어떻게 반영되었는지 정리한다.
    """

    return {
        "applied_style_focus_key": selected_style.get("focus_key"),
        "base_weights": base_profile.get("weights", {}),
        "applied_monthly_weights": monthly_profile.get("weights", {}),
        "applied_nutrition_detail_weights": monthly_profile.get(
            "nutrition_detail_weights",
            {}
        ),
    }


def filter_reasons_by_focus_key(
    reasons: list[dict],
    focus_key: str | None
) -> list[dict]:
    """
    선택한 스타일의 focus_key에 맞는 추천 이유만 남긴다.

    예:
    - focus_key == "budget"이면 budget reason만 반환
    - focus_key == "nutrition"이면 nutrition reason만 반환
    """

    if not focus_key:
        return reasons

    filtered_reasons = [
        reason for reason in reasons
        if reason.get("type") == focus_key
    ]

    if filtered_reasons:
        return filtered_reasons

    return reasons[:1]


def format_recipe_summary_for_back(recipe: dict) -> dict:
    """
    월간 식단 화면에 필요한 레시피 요약 정보만 반환한다.
    """

    return {
        "serving_size": recipe.get("serving_size"),
        "cooking_time": recipe.get("cooking_time"),
        "required_ingredients": recipe.get("required_ingredients", []),
    }


def format_menu_for_back(
    menu: dict,
    focus_key: str | None
) -> dict:
    """
    selected_menu / alternative_menu를 Back/Front 전달용으로 경량화한다.

    월간 식단 기본 응답에서는 모델링 디버깅용 점수와 품질 진단 필드를 제외하고,
    화면 표시와 장보기 계산에 필요한 핵심 필드는 유지한다.
    """

    nutrient_summary = menu.get("nutrient_summary", {})
    recipe = menu.get("recipe", {})

    carbohydrate = menu.get(
        "carbohydrate",
        nutrient_summary.get("carbohydrate", 0)
    )
    protein = menu.get("protein", nutrient_summary.get("protein", 0))
    fat = menu.get("fat", nutrient_summary.get("fat", 0))

    return {
        "menu_id": menu.get("menu_id"),
        "name": menu.get("name"),
        "category": menu.get("category"),

        "final_score": menu.get("final_score"),

        "estimated_cost": menu.get("estimated_cost"),
        "rag_estimated_cost": menu.get("rag_estimated_cost"),
        "pricing_status": menu.get("pricing_status"),

        "calories": menu.get("calories", 0),
        "protein": protein,
        "carbohydrate": carbohydrate,
        "fat": fat,
        "nutrient_summary": {
            "carbohydrate": carbohydrate,
            "protein": protein,
            "fat": fat,
        },

        "difficulty": menu.get("difficulty"),

        "ingredients": menu.get("ingredients", []),
        "ingredient_groups": menu.get("ingredient_groups", []),
        "ingredient_usages": menu.get("ingredient_usages", []),
        "ingredient_costs": menu.get("ingredient_costs", []),

        "recipe": format_recipe_summary_for_back(recipe),

        "reasons": filter_reasons_by_focus_key(
            reasons=menu.get("reasons", []),
            focus_key=focus_key
        ),

        "allergy_ingredients": menu.get("allergy_ingredients", []),
    }


def format_monthly_plan_for_back(
    monthly_plan: dict,
    focus_key: str | None
) -> dict:
    """
    월간 식단 내부 구조를 Back 전달용으로 정리한다.

    - summary 유지
    - style_validation 위치 보장
    - days 내부 selected_menu / alternative_menus 필드 순서 통일
    """

    formatted_days = []

    for day in monthly_plan.get("days", []):
        formatted_meals = []

        for meal in day.get("meals", []):
            selected_menu = meal.get("selected_menu", {})
            alternative_menus = meal.get("alternative_menus", [])

            formatted_meals.append({
                "meal_order": meal.get("meal_order"),
                "selected_menu": format_menu_for_back(
                    menu=selected_menu,
                    focus_key=focus_key
                ),
                "alternative_menus": [
                    format_menu_for_back(
                        menu=alternative_menu,
                        focus_key=focus_key
                    )
                    for alternative_menu in alternative_menus
                ],
            })

        formatted_days.append({
            "day": day.get("day"),
            "meals": formatted_meals,
            "total_estimated_cost": day.get("total_estimated_cost", 0),
            "total_calories": day.get("total_calories", 0),
        })

    return {
        "period_days": monthly_plan.get("period_days"),
        "meal_count_per_day": monthly_plan.get("meal_count_per_day"),
        "required_meal_count": monthly_plan.get("required_meal_count"),
        "available_recommendation_count": monthly_plan.get(
            "available_recommendation_count"
        ),
        "diversity_penalty_strength": monthly_plan.get(
            "diversity_penalty_strength"
        ),
        "recent_day_window": monthly_plan.get("recent_day_window"),
        "warnings": monthly_plan.get("warnings", []),
        "optimizer": monthly_plan.get("optimizer"),
        "profiling": monthly_plan.get("profiling", {}),
        "fallback": monthly_plan.get("fallback", {}),
        "summary": monthly_plan.get("summary", {}),
        "style_validation": monthly_plan.get("style_validation", {}),
        "days": formatted_days,
    }


def build_modeling_to_back_monthly_response(
    user_id: str,
    selected_style: dict,
    base_profile: dict,
    monthly_profile: dict,
    monthly_plan: dict,
    actual_recommendation_count: int
) -> dict:
    """
    Modeling → Back 월간 식단 추천 최종 응답 JSON을 만든다.

    이 함수에서 응답 구조를 고정하면,
    내부 추천 로직이 바뀌어도 Back/Front와 맞춘 응답 형식을 유지할 수 있다.
    """

    focus_key = selected_style.get("focus_key")

    period_days = monthly_plan.get("period_days")
    meal_count_per_day = monthly_plan.get("meal_count_per_day")
    required_meal_count = monthly_plan.get("required_meal_count")

    return {
        "id": user_id,
        "request_type": "monthly_plan",
        "success": True,
        "failure_reason": None,
        "selected_style": selected_style,
        "meta": {
            "period_days": period_days,
            "meal_count_per_day": meal_count_per_day,
            "required_meal_count": required_meal_count,
            "available_recommendation_count": actual_recommendation_count,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "warnings": monthly_plan.get("warnings", []),
            "fallback": monthly_plan.get("fallback", {}),
        },
        "modeling_profile": build_modeling_profile_summary(
            profile=base_profile
        ),
        "applied_style_adjustment": build_applied_style_adjustment(
            base_profile=base_profile,
            monthly_profile=monthly_profile,
            selected_style=selected_style
        ),
        "monthly_plan": format_monthly_plan_for_back(
            monthly_plan=monthly_plan,
            focus_key=focus_key
        ),
    }