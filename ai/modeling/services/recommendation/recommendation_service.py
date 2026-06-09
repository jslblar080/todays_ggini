from services.recommendation.scoring_service import (
    calculate_budget_score,
    calculate_difficulty_score,
    calculate_preference_score,
    calculate_nutrition_score,
    calculate_diversity_score
)


def has_excluded_ingredient(menu: dict, excluded_ingredients: list) -> bool:
    """
    메뉴에 사용자가 제외한 재료 또는 알레르기 재료가 포함되어 있는지 확인한다.
    """

    menu_ingredients = menu.get("ingredients", [])
    menu_allergy_ingredients = menu.get("allergy_ingredients", [])

    check_targets = menu_ingredients + menu_allergy_ingredients

    for excluded_ingredient in excluded_ingredients:
        if excluded_ingredient in check_targets:
            return True

    return False


def score_to_level(score: float) -> str:
    """
    0~100 점수를 설명용 수준 문구로 변환한다.
    """

    if score >= 90:
        return "매우 적합"

    if score >= 75:
        return "적합"

    if score >= 60:
        return "보통"

    if score >= 40:
        return "낮음"

    return "부적합"


def build_budget_reason(
    menu: dict,
    profile: dict,
    budget_score: float
) -> dict:
    """
    예산 점수에 따른 추천 이유를 만든다.
    """

    menu_cost = menu.get("estimated_cost")
    meal_budget = profile.get("meal_budget", 0)

    if meal_budget <= 0:
        message = "한 끼 예산 정보가 없어 예산 적합도를 정확히 판단하기 어렵습니다."

    elif menu_cost is None or menu_cost <= 0:
        message = "메뉴 예상 가격을 계산하지 못해 예산 적합도는 중립적으로 반영되었습니다."

    elif menu_cost <= meal_budget:
        remain_budget = meal_budget - menu_cost
        remain_rate = (remain_budget / meal_budget) * 100

        if remain_rate >= 20:
            message = (
                f"한 끼 예산 {meal_budget:,}원보다 {remain_budget:,}원 저렴해 "
                "예산 여유가 큰 메뉴입니다."
            )
        elif remain_rate >= 5:
            message = (
                f"한 끼 예산 {meal_budget:,}원 이내에 안정적으로 들어오는 메뉴입니다."
            )
        else:
            message = (
                f"한 끼 예산 {meal_budget:,}원에 거의 맞춰 구성 가능한 메뉴입니다."
            )

    else:
        over_budget = menu_cost - meal_budget
        over_rate = (over_budget / meal_budget) * 100

        if budget_score >= 85:
            message = (
                f"한 끼 예산보다 {over_budget:,}원 초과하지만, "
                f"초과율이 약 {over_rate:.1f}%로 부담이 크지 않은 편입니다."
            )
        elif budget_score >= 70:
            message = (
                f"한 끼 예산보다 {over_budget:,}원 초과하여 "
                f"약 {over_rate:.1f}%의 추가 비용이 발생합니다."
            )
        elif budget_score >= 50:
            message = (
                f"한 끼 예산 대비 약 {over_rate:.1f}% 초과되어 "
                "예산 기준에서는 다소 부담이 있는 메뉴입니다."
            )
        else:
            message = (
                f"한 끼 예산 대비 약 {over_rate:.1f}% 초과되어 "
                "예산 절약 목적에는 적합도가 낮은 메뉴입니다."
            )

    return {
        "type": "budget",
        "score": round(budget_score, 2),
        "level": score_to_level(budget_score),
        "message": message
    }


def build_nutrition_reason(
    menu: dict,
    profile: dict,
    nutrition_score: float
) -> dict:
    """
    영양 점수에 따른 추천 이유를 만든다.
    """

    goals = profile.get("goals", [])
    calories = menu.get("calories", 0)
    nutrient_summary = menu.get("nutrient_summary", {})
    carbohydrate = menu.get("carbohydrate", nutrient_summary.get("carbohydrate", 0))
    protein = menu.get("protein", nutrient_summary.get("protein", 0)) or 0
    fat = menu.get("fat", nutrient_summary.get("fat", 0))

    nutrition_messages = []

    if "다이어트" in goals:
        if calories <= 500 and fat <= 15:
            nutrition_messages.append(
                f"칼로리 {calories}kcal, 지방 {fat}g으로 다이어트 목표에 매우 적합합니다."
            )
        elif calories <= 650 and fat <= 20:
            nutrition_messages.append(
                f"칼로리 {calories}kcal, 지방 {fat}g으로 다이어트 식단에 적합한 편입니다."
            )
        elif calories <= 800:
            nutrition_messages.append(
                f"칼로리가 {calories}kcal로 다이어트 기준에서는 보통 수준입니다."
            )
        else:
            nutrition_messages.append(
                f"칼로리가 {calories}kcal로 높아 다이어트 목적에는 다소 부담이 있습니다."
            )

    if "고단백" in goals:
        if protein >= 30:
            nutrition_messages.append(
                f"단백질이 {protein}g으로 높아 고단백 목표에 매우 적합합니다."
            )
        elif protein >= 20:
            nutrition_messages.append(
                f"단백질이 {protein}g으로 고단백 목표에 적합한 편입니다."
            )
        elif protein >= 10:
            nutrition_messages.append(
                f"단백질이 {protein}g으로 기본적인 단백질 보충은 가능합니다."
            )
        else:
            nutrition_messages.append(
                f"단백질이 {protein}g으로 고단백 목표에는 다소 부족합니다."
            )

    if "영양 균형" in goals:
        total_macro = carbohydrate + protein + fat

        if total_macro <= 0:
            nutrition_messages.append(
                "탄수화물, 단백질, 지방 정보가 부족해 영양 균형은 중립적으로 반영되었습니다."
            )
        else:
            carbohydrate_ratio = carbohydrate / total_macro
            protein_ratio = protein / total_macro
            fat_ratio = fat / total_macro

            if (
                0.45 <= carbohydrate_ratio <= 0.65
                and 0.15 <= protein_ratio <= 0.35
                and 0.15 <= fat_ratio <= 0.35
                and 400 <= calories <= 850
            ):
                nutrition_messages.append(
                    "탄수화물, 단백질, 지방 비율이 안정적이어서 영양 균형 목표에 매우 적합합니다."
                )
            elif (
                0.35 <= carbohydrate_ratio <= 0.70
                and 0.10 <= protein_ratio <= 0.40
                and 0.10 <= fat_ratio <= 0.45
                and 350 <= calories <= 950
            ):
                nutrition_messages.append(
                    "탄수화물, 단백질, 지방 비율이 대체로 무난해 영양 균형 목표에 적합한 편입니다."
                )
            else:
                nutrition_messages.append(
                    "탄수화물, 단백질, 지방 비율 기준으로는 영양 균형 조정이 필요할 수 있습니다."
                )

    if not nutrition_messages:
        if nutrition_score >= 75:
            message = "선택한 목표에서 특별한 영양 제한은 없지만, 기본 영양 기준을 무난하게 만족합니다."
        else:
            message = "선택한 목표에서 영양 기준은 보조적으로 반영되었습니다."
    else:
        message = " ".join(nutrition_messages)

    return {
        "type": "nutrition",
        "score": round(nutrition_score, 2),
        "level": score_to_level(nutrition_score),
        "message": message
    }


def build_preference_reason(
    menu: dict,
    profile: dict,
    preference_score: float
) -> dict:
    """
    선호도 점수에 따른 추천 이유를 만든다.
    """

    preferred_categories = profile.get("preferred_categories", [])
    ingredient_preferences = profile.get("ingredient_preferences", [])

    menu_category = menu.get("category", "")
    menu_ingredient_groups = menu.get("ingredient_groups", [])

    matched_ingredient_groups = [
        ingredient_group
        for ingredient_group in menu_ingredient_groups
        if ingredient_group in ingredient_preferences
    ]

    category_matched = (
        "상관없음" in preferred_categories
        or menu_category in preferred_categories
    )

    if preference_score >= 90:
        if category_matched and matched_ingredient_groups:
            message = (
                f"선호 카테고리 '{menu_category}'에 해당하고, "
                f"선호 재료군({', '.join(matched_ingredient_groups)})도 포함되어 있습니다."
            )
        elif category_matched:
            message = f"선호 카테고리 '{menu_category}'에 해당해 취향 반영도가 높습니다."
        else:
            message = "선호 재료군이 충분히 포함되어 취향 반영도가 높습니다."

    elif preference_score >= 75:
        if category_matched:
            message = f"선호 카테고리 '{menu_category}'가 반영되어 선호도 기준에 적합합니다."
        elif matched_ingredient_groups:
            message = (
                f"선호 재료군({', '.join(matched_ingredient_groups)})이 포함되어 "
                "선호도 기준에 적합한 편입니다."
            )
        else:
            message = "사용자 선호 조건을 일부 만족하는 메뉴입니다."

    elif preference_score >= 60:
        message = "선호 카테고리나 선호 재료군과 일부만 맞아 취향 반영도는 보통 수준입니다."

    elif preference_score >= 40:
        message = "선호 카테고리나 선호 재료군과의 일치도가 낮아 취향 반영이 약한 편입니다."

    else:
        message = "사용자가 입력한 선호 카테고리와 재료군 기준에서는 적합도가 낮습니다."

    return {
        "type": "preference",
        "score": round(preference_score, 2),
        "level": score_to_level(preference_score),
        "message": message
    }


def build_difficulty_reason(
    menu: dict,
    profile: dict,
    difficulty_score: float
) -> dict:
    """
    난이도 점수에 따른 추천 이유를 만든다.
    """

    menu_difficulty = menu.get("difficulty", 3)
    max_difficulty = profile.get("max_difficulty", 3)
    difficulty_detail = menu.get("difficulty_detail", {})

    if menu_difficulty <= max_difficulty:
        message = (
            f"메뉴 난이도 {menu_difficulty}로 사용자 가능 난이도 {max_difficulty} 이내에 있어 "
            "충분히 조리 가능한 메뉴입니다."
        )

    else:
        difficulty_gap = menu_difficulty - max_difficulty

        if difficulty_gap == 1:
            message = (
                f"메뉴 난이도 {menu_difficulty}로 사용자 가능 난이도보다 1단계 높아 "
                "약간의 조리 부담이 있을 수 있습니다."
            )
        elif difficulty_gap == 2:
            message = (
                f"메뉴 난이도 {menu_difficulty}로 사용자 가능 난이도보다 2단계 높아 "
                "조리 부담이 다소 큰 메뉴입니다."
            )
        else:
            message = (
                f"메뉴 난이도 {menu_difficulty}로 사용자 가능 난이도 {max_difficulty}보다 많이 높아 "
                "현재 조리 실력 기준에서는 적합도가 낮습니다."
            )

    if difficulty_detail:
        message += (
            f" 재료 {difficulty_detail.get('ingredient_count', 0)}개, "
            f"조리 단계 {difficulty_detail.get('step_count', 0)}개, "
            f"조리 시간 {difficulty_detail.get('cooking_time', 0)}분 기준입니다."
        )

    return {
        "type": "difficulty",
        "score": round(difficulty_score, 2),
        "level": score_to_level(difficulty_score),
        "message": message
    }


def build_diversity_reason(
    menu: dict,
    selected_menu_ids: list,
    diversity_score: float
) -> dict:
    """
    다양성 점수에 따른 추천 이유를 만든다.
    """

    similar_menu_ids = menu.get("similar_menu_ids", [])

    matched_similar_ids = [
        selected_menu_id
        for selected_menu_id in selected_menu_ids
        if selected_menu_id in similar_menu_ids
    ]

    if diversity_score >= 90:
        message = "최근 선택된 메뉴와 유사도가 낮아 반복을 줄일 수 있습니다."

    elif diversity_score >= 75:
        message = "최근 식단과 약간의 유사성은 있지만, 반복 부담은 크지 않은 메뉴입니다."

    elif diversity_score >= 60:
        message = "최근 선택된 메뉴와 일부 유사해 다양성 기준에서는 보통 수준입니다."

    elif diversity_score >= 40:
        if matched_similar_ids:
            message = "최근 선택된 메뉴와 유사한 메뉴군에 포함되어 다양성 점수가 낮게 반영되었습니다."
        else:
            message = "식단 내 반복 가능성이 있어 다양성 기준에서는 아쉬운 메뉴입니다."

    else:
        message = "최근 선택 메뉴와 유사도가 높아 반복 방지 측면에서는 적합도가 낮습니다."

    return {
        "type": "diversity",
        "score": round(diversity_score, 2),
        "level": score_to_level(diversity_score),
        "message": message
    }

def calculate_style_soft_constraint_score(
    menu: dict,
    profile: dict,
    scores: dict
) -> float:
    """
    사용자가 선택한 스타일에 따라 final_score에 추가 보정 점수를 부여한다.

    이 점수는 하드 필터가 아니라 soft constraint이다.
    즉, 조건에 맞지 않는 메뉴를 무조건 제거하지 않고,
    스타일 적합도가 높은 메뉴는 올리고 낮은 메뉴는 내린다.
    """

    selected_style_goal = profile.get("selected_style_goal")
    source_goal = profile.get("source_goal")

    # 둘 중 하나라도 들어오면 사용할 수 있게 처리한다.
    style_goal = selected_style_goal or source_goal

    if style_goal == "고단백":
        return calculate_high_protein_soft_constraint_score(menu)

    if style_goal == "간편식":
        return calculate_easy_cooking_soft_constraint_score(scores)

    return 0


def calculate_high_protein_soft_constraint_score(menu: dict) -> float:
    """
    고단백 스타일에서 단백질 함량을 기준으로 추가 보정 점수를 계산한다.

    월간 식단에서는 단백질만 과도하게 높이는 것보다
    단백질 적합성과 메뉴 다양성을 함께 유지하는 것이 중요하다.
    """

    protein = menu.get("protein", 0)

    if protein >= 35:
        return 3

    if protein >= 30:
        return 2

    if protein >= 25:
        return 1

    if protein >= 22:
        return 0

    if protein >= 18:
        return -2

    return -4


def calculate_easy_cooking_soft_constraint_score(scores: dict) -> float:
    """
    간편식 스타일에서 difficulty_score를 기준으로 추가 보정 점수를 계산한다.

    difficulty_score가 높다는 것은 사용자 조리 실력 대비 부담이 낮다는 뜻이다.
    간편식 스타일에서는 조리 부담이 낮은 메뉴가 더 우선되도록 보정한다.
    """

    difficulty_score = scores.get("difficulty", 0)

    if difficulty_score >= 90:
        return 8

    if difficulty_score >= 80:
        return 6

    if difficulty_score >= 70:
        return 4

    if difficulty_score >= 60:
        return 0

    if difficulty_score >= 40:
        return -6

    return -10


def build_recommendation_reasons(
    menu: dict,
    profile: dict,
    selected_menu_ids: list,
    scores: dict
) -> list[dict]:
    """
    메뉴별 점수를 바탕으로 추천 이유 목록을 만든다.
    """

    return [
        build_budget_reason(
            menu=menu,
            profile=profile,
            budget_score=scores["budget"]
        ),
        build_nutrition_reason(
            menu=menu,
            profile=profile,
            nutrition_score=scores["nutrition"]
        ),
        build_preference_reason(
            menu=menu,
            profile=profile,
            preference_score=scores["preference"]
        ),
        build_difficulty_reason(
            menu=menu,
            profile=profile,
            difficulty_score=scores["difficulty"]
        ),
        build_diversity_reason(
            menu=menu,
            selected_menu_ids=selected_menu_ids,
            diversity_score=scores["diversity"]
        )
    ]


def calculate_rag_data_quality_penalty(menu: dict) -> float:
    """
    RAG 응답 데이터 품질이 낮은 메뉴에 적용할 감점 점수를 계산한다.

    rag_data_quality_score는 0~100 기준이다.
    점수가 낮을수록 final_score에서 더 많이 감점한다.

    현재는 후보 부족을 막기 위해 제외가 아니라 감점 방식으로 처리한다.
    """

    quality_score = menu.get("rag_data_quality_score")

    # RAG가 아닌 mock/local 데이터에는 품질 점수가 없을 수 있으므로 감점하지 않는다.
    if quality_score is None:
        return 0

    try:
        quality_score = float(quality_score)
    except (TypeError, ValueError):
        return 0

    if quality_score >= 80:
        return 0

    if quality_score >= 60:
        return 3

    if quality_score >= 40:
        return 7

    if quality_score >= 20:
        return 12

    return 18


def calculate_nutrition_missing_penalty(menu: dict, profile: dict) -> float:
    """
    calories/protein 등 영양 정보가 비어 있는 메뉴에 대한 추가 감점이다.

    특히 고단백, 다이어트, 영양 균형처럼 영양 정보가 중요한 목표에서는
    calories/protein이 0인 메뉴가 상위에 올라오지 않도록 더 강하게 감점한다.
    """

    goals = profile.get("goals", []) or []

    calories = menu.get("calories", 0) or 0
    protein = menu.get("protein", 0) or 0

    nutrient_summary = menu.get("nutrient_summary", {}) or {}
    carbohydrate = menu.get("carbohydrate", nutrient_summary.get("carbohydrate", 0)) or 0
    fat = menu.get("fat", nutrient_summary.get("fat", 0)) or 0

    try:
        calories = float(calories)
        protein = float(protein)
        carbohydrate = float(carbohydrate)
        fat = float(fat)
    except (TypeError, ValueError):
        calories = 0
        protein = 0
        carbohydrate = 0
        fat = 0

    nutrition_sensitive_goals = ["고단백", "다이어트", "영양 균형"]

    is_nutrition_sensitive = any(
        goal in nutrition_sensitive_goals
        for goal in goals
    )

    penalty = 0

    if calories <= 0:
        penalty += 5

    if protein <= 0:
        penalty += 5

    if carbohydrate <= 0 and protein <= 0 and fat <= 0:
        penalty += 8

    # 영양 중심 목표에서는 영양 정보 누락을 더 강하게 감점한다.
    if is_nutrition_sensitive:
        penalty *= 1.5

    return round(penalty, 2)


def calculate_final_score(
    menu: dict,
    profile: dict,
    selected_menu_ids: list
) -> dict:
    """
    메뉴 하나에 대해 예산, 영양, 선호도, 난이도, 다양성 점수를 계산하고
    최종 점수와 추천 이유를 만든다.
    """

    weights = profile["weights"]

    budget_score = calculate_budget_score(
        menu.get("estimated_cost"),
        profile["meal_budget"]
    )

    nutrition_score = calculate_nutrition_score(
        menu,
        profile=profile
    )

    preference_score = calculate_preference_score(
        menu,
        profile
    )

    difficulty_score = calculate_difficulty_score(
        menu.get("difficulty", 3),
        profile["max_difficulty"]
    )

    diversity_score = calculate_diversity_score(
        menu=menu,
        selected_menu_ids=selected_menu_ids,
        penalty_strength=profile["diversity_penalty_strength"]
    )

    scores = {
        "budget": round(budget_score, 2),
        "nutrition": round(nutrition_score, 2),
        "preference": round(preference_score, 2),
        "difficulty": round(difficulty_score, 2),
        "diversity": round(diversity_score, 2)
    }

    base_final_score = (
        budget_score * weights["budget"]
        + nutrition_score * weights["nutrition"]
        + preference_score * weights["preference"]
        + difficulty_score * weights["difficulty"]
        + diversity_score * weights["diversity"]
    )

    style_soft_constraint_score = calculate_style_soft_constraint_score(
        menu=menu,
        profile=profile,
        scores=scores   
    )

    rag_data_quality_penalty = calculate_rag_data_quality_penalty(menu)

    nutrition_missing_penalty = calculate_nutrition_missing_penalty(
        menu=menu,
        profile=profile,
    )

    total_quality_penalty = (
        rag_data_quality_penalty
        + nutrition_missing_penalty
    )

    final_score = (
        base_final_score
        + style_soft_constraint_score
        - total_quality_penalty
    )

    final_score = max(final_score, 0)

    all_reasons = build_recommendation_reasons(
        menu=menu,
        profile=profile,
        selected_menu_ids=selected_menu_ids,
        scores=scores
    )

    reasons = filter_reasons_by_focus_key(
        reasons=all_reasons,
        profile=profile
    )

    nutrient_summary = menu.get("nutrient_summary", {})

    return {
        "menu_id": menu.get("menu_id"),
        "name": menu.get("name"),
        "category": menu.get("category"),
        "final_score": round(final_score, 2),
        "base_final_score": round(base_final_score, 2),
        "style_soft_constraint_score": round(style_soft_constraint_score, 2),
        "scores": scores,
        "reasons": reasons,
        "estimated_cost": menu.get("estimated_cost"),
        "rag_estimated_cost": menu.get("rag_estimated_cost"),
        "pricing_status": menu.get("pricing_status"),
        "ingredient_costs": menu.get("ingredient_costs", []),
        "calories": menu.get("calories", 0),
        "nutrient_summary": nutrient_summary,
        "carbohydrate": menu.get("carbohydrate", nutrient_summary.get("carbohydrate", 0)),
        "protein": menu.get("protein", nutrient_summary.get("protein", 0)),
        "fat": menu.get("fat", nutrient_summary.get("fat", 0)),
        "difficulty": menu.get("difficulty", 3),
        "difficulty_detail": menu.get("difficulty_detail", {}),
        "ingredients": menu.get("ingredients", []),
        "ingredient_groups": menu.get("ingredient_groups", []),
        "ingredient_usages": menu.get("ingredient_usages", []),
        "similar_menu_ids": menu.get("similar_menu_ids", []),
        "allergy_ingredients": menu.get("allergy_ingredients", []),
        "recipe": menu.get("recipe", {}),
        "rag_data_quality_score": menu.get("rag_data_quality_score"),
        "rag_data_quality_issues": menu.get("rag_data_quality_issues", []),
        "rag_data_quality_penalty": round(rag_data_quality_penalty, 2),
        "nutrition_missing_penalty": round(nutrition_missing_penalty, 2),
        "total_quality_penalty": round(total_quality_penalty, 2),
        "nutrition_outlier_issues": menu.get("nutrition_outlier_issues", []),
        "nutrition_outlier_penalty": menu.get("nutrition_outlier_penalty", 0),
        "is_extreme_nutrition_outlier": menu.get(
            "is_extreme_nutrition_outlier",
            False,
        ),
    }


def recommend_menus(menus: list, profile: dict, top_n: int = 5) -> list:
    """
    메뉴를 하나씩 선택하면서 다양성 점수를 반영해 추천한다.

    1개 메뉴를 선택할 때마다 selected_menu_ids에 추가하고,
    다음 메뉴 계산 시 이미 선택된 메뉴와의 유사성을 반영한다.
    """

    recommendations = []
    selected_menu_ids = []
    candidate_menus = []

    for menu in menus:
        if has_excluded_ingredient(
            menu=menu,
            excluded_ingredients=profile.get("allergy_ingredients", [])
        ):
            continue

        candidate_menus.append(menu)

    while len(recommendations) < top_n and candidate_menus:
        scored_menus = []

        for menu in candidate_menus:
            result = calculate_final_score(
                menu=menu,
                profile=profile,
                selected_menu_ids=selected_menu_ids
            )

            scored_menus.append({
                "menu": menu,
                "result": result
            })

        scored_menus.sort(
            key=lambda x: x["result"]["final_score"],
            reverse=True
        )

        best_menu = scored_menus[0]["menu"]
        best_result = scored_menus[0]["result"]

        recommendations.append(best_result)
        selected_menu_ids.append(best_menu.get("menu_id"))

        candidate_menus = [
            menu for menu in candidate_menus
            if menu.get("menu_id") != best_menu.get("menu_id")
        ]

    return recommendations

def get_reason_type_by_focus_key(focus_key: str | None) -> str | None:
    """
    선택 스타일의 focus_key를 추천 이유 type과 매핑한다.

    예:
    - budget -> budget 이유만 노출
    - nutrition -> nutrition 이유만 노출
    - difficulty -> difficulty 이유만 노출
    - preference -> preference 이유만 노출
    """

    mapping = {
        "budget": "budget",
        "nutrition": "nutrition",
        "difficulty": "difficulty",
        "preference": "preference",
        "diversity": "diversity",
    }

    return mapping.get(focus_key)


def filter_reasons_by_focus_key(
    reasons: list[dict],
    profile: dict
) -> list[dict]:
    """
    월간 식단 응답에서 사용자에게 보여줄 핵심 추천 이유만 남긴다.

    selected_style의 focus_key가 있으면 해당 이유만 남기고,
    focus_key가 없거나 매칭되는 이유가 없으면 전체 이유를 반환한다.
    """

    focus_key = profile.get("selected_style_focus_key")

    reason_type = get_reason_type_by_focus_key(focus_key)

    if not reason_type:
        return reasons

    filtered_reasons = [
        reason for reason in reasons
        if reason.get("type") == reason_type
    ]

    if not filtered_reasons:
        return reasons

    return filtered_reasons