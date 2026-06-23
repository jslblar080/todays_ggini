from services.optimizer.ortools.result_mapper import build_ortools_monthly_plan


def make_menu(
    menu_id: int,
    name: str,
    category: str,
    ingredient_group: str,
) -> dict:
    return {
        "menu_id": menu_id,
        "name": name,
        "category": category,
        "estimated_cost": 3000,
        "calories": 500,
        "protein": 20,
        "carbohydrate": 60,
        "fat": 15,
        "ingredients": [ingredient_group],
        "ingredient_groups": [ingredient_group],
        "similar_menu_ids": [],
        "scores": {
            "nutrition": 80,
            "budget": 80,
            "preference": 80,
            "difficulty": 80,
            "diversity": 80,
        },
        "final_score": 80,
    }


def test_ortools_plan_populates_alternative_menus():
    selected_menu = make_menu(1, "닭가슴살 덮밥", "밥", "닭고기")

    recommendations = [
        selected_menu,
        make_menu(2, "연어 샐러드", "샐러드", "생선"),
        make_menu(3, "두부 스테이크", "구이", "두부"),
        make_menu(4, "소고기 채소볶음", "볶음", "소고기"),
    ]

    optimizer_result = {
        "solver_status": "OPTIMAL",
        "objective_value": 100,
        "message": "success",
        "optimizer_config": {},
        "selected_items": [
            {
                "day": 1,
                "meal_order": 1,
                "selected_menu": selected_menu,
            }
        ],
    }

    optimizer_input = {
        "period_days": 1,
        "meal_count_per_day": 1,
    }

    profile = {
        "diversity_penalty_strength": 0.5,
        "recent_day_window": 3,
    }

    result = build_ortools_monthly_plan(
        optimizer_result=optimizer_result,
        optimizer_input=optimizer_input,
        recommendations=recommendations,
        profile=profile,
    )

    meal = result["days"][0]["meals"][0]
    alternatives = meal["alternative_menus"]

    assert meal["selected_menu"]["menu_id"] == 1
    assert len(alternatives) == 2

    alternative_ids = [
        alternative["menu_id"]
        for alternative in alternatives
    ]

    assert 1 not in alternative_ids
    assert len(alternative_ids) == len(set(alternative_ids))


def test_ortools_plan_keeps_empty_alternatives_when_no_candidate_exists():
    selected_menu = make_menu(1, "닭가슴살 덮밥", "밥", "닭고기")

    optimizer_result = {
        "solver_status": "OPTIMAL",
        "objective_value": 100,
        "message": "success",
        "optimizer_config": {},
        "selected_items": [
            {
                "day": 1,
                "meal_order": 1,
                "selected_menu": selected_menu,
            }
        ],
    }

    result = build_ortools_monthly_plan(
        optimizer_result=optimizer_result,
        optimizer_input={
            "period_days": 1,
            "meal_count_per_day": 1,
        },
        recommendations=[selected_menu],
        profile={},
    )

    meal = result["days"][0]["meals"][0]

    assert meal["selected_menu"]["menu_id"] == 1
    assert meal["alternative_menus"] == []
