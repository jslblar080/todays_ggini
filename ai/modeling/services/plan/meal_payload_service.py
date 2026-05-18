def build_menu_payload(menu: dict) -> dict:
    """
    식단에 저장할 메뉴 정보를 공통 형식으로 만든다.
    """

    return {
        "menu_id": menu["menu_id"],
        "name": menu["name"],
        "category": menu.get("category"),
        "final_score": menu["final_score"],
        "estimated_cost": menu["estimated_cost"],
        "calories": menu["calories"],
        "protein": menu["protein"],
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
    }
