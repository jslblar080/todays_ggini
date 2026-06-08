def build_menu_payload(menu: dict) -> dict:
    """
    식단에 저장할 메뉴 정보를 공통 형식으로 만든다.
    """

    nutrient_summary = menu.get("nutrient_summary", {}) or {}

    calories = menu.get("calories", 0)
    carbohydrate = menu.get(
        "carbohydrate",
        nutrient_summary.get("carbohydrate", 0),
    )
    protein = menu.get(
        "protein",
        nutrient_summary.get("protein", 0),
    )
    fat = menu.get(
        "fat",
        nutrient_summary.get("fat", 0),
    )

    return {
        "menu_id": menu["menu_id"],
        "name": menu["name"],
        "category": menu.get("category"),
        "final_score": menu["final_score"],
        "estimated_cost": menu["estimated_cost"],

        "calories": calories,
        "carbohydrate": carbohydrate,
        "protein": protein,
        "fat": fat,
        "nutrient_summary": {
            "carbohydrate": carbohydrate,
            "protein": protein,
            "fat": fat,
        },

        "ingredients": menu.get("ingredients", []),
        "ingredient_groups": menu.get("ingredient_groups", []),
        "recipe": menu.get("recipe", {}),
        "scores": menu["scores"],
        "reasons": menu.get("reasons", []),
        "rag_data_quality_score": menu.get("rag_data_quality_score"),
        "rag_data_quality_issues": menu.get("rag_data_quality_issues", []),
        "rag_data_quality_penalty": menu.get("rag_data_quality_penalty", 0),
        "nutrition_missing_penalty": menu.get("nutrition_missing_penalty", 0),
        "total_quality_penalty": menu.get("total_quality_penalty", 0),
        "nutrition_outlier_issues": menu.get("nutrition_outlier_issues", []),
        "nutrition_outlier_penalty": menu.get("nutrition_outlier_penalty", 0),
        "is_extreme_nutrition_outlier": menu.get(
            "is_extreme_nutrition_outlier",
            False,
        ),
    }
