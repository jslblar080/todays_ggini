def calculate_budget_score(menu_cost: int | None, meal_budget: int) -> float:
    """
    메뉴 가격이 한 끼 예산 안에 들어오면 100점이다.
    예산을 초과하면 초과 비율만큼 점수를 깎는다.

    menu_cost가 없으면 가격 판단이 불가능하므로 중립 점수 70점을 부여한다.
    """

    if menu_cost is None or menu_cost <= 0:
        return 70

    if meal_budget <= 0:
        return 70

    if menu_cost <= meal_budget:
        return 100

    score = 100 - ((menu_cost - meal_budget) / meal_budget) * 100

    return max(0, score)


def get_effective_difficulty(menu: dict) -> int:
    """
    menu.difficulty가 있으면 그대로 사용하고,
    비어 있으면 recipe 정보를 바탕으로 조리 난이도를 보조 추론한다.

    RAG 응답에서는 difficulty가 비어 있는 경우가 많다.
    이때 기본값 3으로 처리하면 간편식/낮은 조리 실력 사용자에게
    과도한 감점이 발생할 수 있으므로 cooking_time과 재료 수를 함께 본다.
    """

    raw_difficulty = menu.get("difficulty")

    try:
        if raw_difficulty is not None:
            difficulty = int(raw_difficulty)

            if difficulty < 1:
                return 1

            if difficulty > 5:
                return 5

            return difficulty
    except (TypeError, ValueError):
        pass

    recipe = menu.get("recipe", {}) or {}

    cooking_time = recipe.get("cooking_time")
    required_ingredients = recipe.get("required_ingredients", []) or []
    steps = recipe.get("steps", []) or []

    try:
        cooking_time = int(cooking_time or 0)
    except (TypeError, ValueError):
        cooking_time = 0

    ingredient_count = len(required_ingredients)
    step_count = len(steps)

    # 조리 정보가 거의 없으면 중립 난이도 2로 처리한다.
    # 기존 기본값 3보다 간편식 사용자에게 덜 가혹하게 반영한다.
    if cooking_time <= 0 and ingredient_count == 0 and step_count == 0:
        return 2

    if cooking_time > 0 and cooking_time <= 10 and ingredient_count <= 6:
        return 1

    if cooking_time > 0 and cooking_time <= 20 and ingredient_count <= 9:
        return 2

    if cooking_time > 0 and cooking_time <= 20 and ingredient_count <= 12:
        return 2

    # RAG 응답은 steps가 비어 있는 경우가 많다.
    # 조리 시간이 20분 이내이고 단계 정보가 없으면,
    # 재료 수가 조금 많아도 간편식 후보로 볼 수 있게 난이도 2로 완화한다.
    if cooking_time > 0 and cooking_time <= 20 and step_count == 0 and ingredient_count <= 14:
        return 2

    if cooking_time > 0 and cooking_time <= 20:
        return 3

    if cooking_time > 0 and cooking_time <= 30 and ingredient_count <= 12:
        return 3

    return 4


def calculate_difficulty_score(menu_difficulty: int, cooking_skill: int) -> float:
    """
    메뉴 난이도가 사용자 요리 실력보다 낮거나 같으면 100점이다.
    사용자 실력보다 어려우면 단계 차이마다 30점씩 감점한다.
    """

    if menu_difficulty <= cooking_skill:
        return 100

    score = 100 - (menu_difficulty - cooking_skill) * 30

    return max(0, score)


CATEGORY_ALIASES = {
    "샐러드/건강식": [
        "샐러드/건강식",
        "다이어트",
    ],
    "디저트": [
        "디저트",
    ],
    "다 좋아요": [
        "한식",
        "양식",
        "일식",
        "중식",
        "분식",
        "다이어트",
        "디저트",
    ],
}


def expand_preferred_categories(preferred_categories: list[str]) -> list[str]:
    """
    사용자에게 보이는 UI 카테고리와 RAG가 실제 반환하는 category가 다를 수 있어,
    preference score 계산 시 내부 매칭 카테고리를 확장한다.

    예:
    - UI: 샐러드/건강식 -> RAG: 다이어트
    - UI: 디저트 -> RAG: 디저트
    """

    expanded_categories = []

    for category in preferred_categories:
        aliases = CATEGORY_ALIASES.get(category, [category])

        for alias in aliases:
            if alias not in expanded_categories:
                expanded_categories.append(alias)

    return expanded_categories


def calculate_category_score(
    menu_category: str,
    preferred_categories: list[str]
) -> float:
    """
    메뉴 카테고리가 사용자의 선호 카테고리에 포함되는지 계산한다.

    상관없음을 선택한 경우 카테고리 영향은 중립 점수로 처리한다.
    """

    expanded_categories = expand_preferred_categories(preferred_categories)

    if "상관없음" in preferred_categories or "다 좋아요" in preferred_categories:
        return 70

    if menu_category in preferred_categories:
        return 100

    if menu_category in expanded_categories:
        return 85

    return 40


INGREDIENT_GROUP_KEYWORDS = {
    "계란 및 유제품류": [
        "계란",
        "달걀",
        "우유",
        "치즈",
        "버터",
        "크림",
        "요거트",
        "요구르트",
        "마요네즈",
        "달걀노른자",
        "계란노른자",
        "달걀흰자",
        "계란흰자",
        "모짜렐라",
        "체다",
        "생크림",
        "요플레",
    ],
    "육류": [
        "소고기",
        "쇠고기",
        "돼지고기",
        "닭고기",
        "닭",
        "오리",
        "햄",
        "소시지",
        "스팸",
        "베이컨",
        "불고기",
        "고기",
        "차돌",
        "우삼겹",
        "삼겹살",
        "목살",
        "제육",
        "닭가슴살",
        "닭다리",
        "닭봉",
    ],
    "해산물류": [
        "새우",
        "오징어",
        "고등어",
        "연어",
        "참치",
        "굴",
        "바지락",
        "홍합",
        "멸치",
        "어묵",
        "게맛살",
        "크래미",
        "생선",
        "명태",
        "동태",
        "갈치",
        "꽁치",
        "조기",
        "조개",
        "해물",
        "미역",
        "다시마",
        "김",
    ],
    "식물성 단백질류": [
        "두부",
        "콩",
        "병아리콩",
        "렌틸",
        "비지",
        "템페",
        "순두부",
        "유부",
        "콩고기",
        "낫토",
        "완두콩",
        "검은콩",
        "강낭콩",
    ],
    "채소류": [
        "양파",
        "대파",
        "파",
        "마늘",
        "당근",
        "양배추",
        "배추",
        "시금치",
        "상추",
        "깻잎",
        "가지",
        "호박",
        "애호박",
        "콩나물",
        "숙주",
        "버섯",
        "브로콜리",
        "오이",
        "토마토",
        "고추",
        "무",
        "감자",
        "고구마",
        "피망",
        "파프리카",
        "부추",
        "청경채",
        "양상추",
        "양송이",
        "새송이",
        "표고",
    ],
}


def normalize_ingredient_name(ingredient: object) -> str:
    """
    ingredient 값을 문자열로 변환하고 대체 표기 문구를 제거한다.
    """

    text = str(ingredient or "").strip()
    text = text.replace("(대체)", "")
    text = text.replace(" 대체", "")

    return text


def infer_ingredient_groups_from_ingredients(ingredients: list) -> list[str]:
    """
    RAG 응답의 ingredient_groups가 비어 있을 때 ingredients 이름을 기반으로
    재료군을 보조 추론한다.

    이 값은 hard constraint가 아니라 preference score 보조 계산에만 사용한다.
    """

    inferred_groups = []

    ingredient_text = " ".join(
        normalize_ingredient_name(ingredient)
        for ingredient in ingredients
    )

    for group, keywords in INGREDIENT_GROUP_KEYWORDS.items():
        if any(keyword in ingredient_text for keyword in keywords):
            inferred_groups.append(group)

    return inferred_groups


def get_effective_ingredient_groups(menu: dict) -> list[str]:
    """
    menu.ingredient_groups가 있으면 그대로 사용하고,
    비어 있으면 ingredients 기반으로 보조 재료군을 추론한다.
    """

    ingredient_groups = menu.get("ingredient_groups", []) or []

    if ingredient_groups:
        return ingredient_groups

    return infer_ingredient_groups_from_ingredients(
        ingredients=menu.get("ingredients", []) or []
    )


def calculate_ingredient_score(
    menu_ingredient_groups: list[str],
    ingredient_preferences: list[str]
) -> float:
    """
    메뉴의 재료군이 사용자가 선택한 선호 재료군과 얼마나 겹치는지 계산한다.

    ingredient_preferences 예:
    ["육류", "식물성 단백질류"]

    계산 방식:
    겹친 재료군 수 / 사용자가 선택한 선호 재료군 수 * 100
    """

    if not ingredient_preferences:
        return 50

    if not menu_ingredient_groups:
        return 50

    matched_count = 0

    for ingredient_group in menu_ingredient_groups:
        if ingredient_group in ingredient_preferences:
            matched_count += 1

    score = (matched_count / len(ingredient_preferences)) * 100

    return min(score, 100)


def calculate_preference_score(menu: dict, profile: dict) -> float:
    """
    사용자 선호 카테고리와 선호 재료군을 바탕으로 선호도 점수를 계산한다.

    선호도 점수 = 카테고리 점수 50% + 재료군 점수 50%
    """

    preferred_categories = profile.get("preferred_categories", [])
    ingredient_preferences = profile.get("ingredient_preferences", [])

    menu_category = menu.get("category", "")
    menu_ingredient_groups = get_effective_ingredient_groups(menu)

    category_score = calculate_category_score(
        menu_category=menu_category,
        preferred_categories=preferred_categories
    )

    ingredient_score = calculate_ingredient_score(
        menu_ingredient_groups=menu_ingredient_groups,
        ingredient_preferences=ingredient_preferences
    )

    preference_score = category_score * 0.5 + ingredient_score * 0.5

    return preference_score


def get_menu_nutrients(menu: dict) -> dict:
    """
    메뉴 영양 정보를 통일된 형태로 가져온다.

    기존 sample_menus 구조와
    RAG nutrient_summary 구조를 모두 지원한다.
    """

    nutrient_summary = menu.get("nutrient_summary", {})

    return {
        "calories": menu.get("calories", 0),
        "carbohydrate": menu.get(
            "carbohydrate",
            nutrient_summary.get("carbohydrate", 0)
        ),
        "protein": menu.get(
            "protein",
            nutrient_summary.get("protein", 0)
        ),
        "fat": menu.get(
            "fat",
            nutrient_summary.get("fat", 0)
        )
    }


def calculate_diet_score(
    calories: float,
    fat: float
) -> float:
    """
    다이어트 목표에 대한 영양 점수를 계산한다.

    다이어트 식단에서는 칼로리와 지방을 중심으로 본다.
    특히 지방이 높은 메뉴는 칼로리가 적당해도 다이어트 적합도가 낮아지도록 제한한다.
    """

    if fat >= 35:
        return 35

    if fat >= 30:
        return 45

    if fat >= 25:
        return 60

    if calories <= 500 and fat <= 15:
        return 100

    if calories <= 650 and fat <= 20:
        return 90

    if calories <= 800 and fat <= 22:
        return 75

    if calories <= 950:
        return 55

    return 40


def calculate_high_protein_score(
    protein: float
) -> float:
    """
    고단백 목표에 대한 영양 점수를 계산한다.

    고단백 식단에서는 단백질 함량을 가장 중요하게 본다.
    """

    if protein >= 35:
        return 100

    if protein >= 30:
        return 95

    if protein >= 25:
        return 90

    if protein >= 20:
        return 80

    if protein >= 15:
        return 65

    if protein >= 10:
        return 50

    return 35


def calculate_balanced_nutrition_score(
    calories: float,
    carbohydrate: float,
    protein: float,
    fat: float
) -> float:
    """
    영양 균형 목표에 대한 영양 점수를 계산한다.

    영양 균형 식단에서는 탄수화물, 단백질, 지방의 비율을 함께 본다.
    """

    total_macro = carbohydrate + protein + fat

    if total_macro <= 0:
        return 60

    carbohydrate_ratio = carbohydrate / total_macro
    protein_ratio = protein / total_macro
    fat_ratio = fat / total_macro

    if (
        0.45 <= carbohydrate_ratio <= 0.65
        and 0.15 <= protein_ratio <= 0.35
        and 0.15 <= fat_ratio <= 0.35
        and 400 <= calories <= 850
    ):
        return 100

    if (
        0.35 <= carbohydrate_ratio <= 0.70
        and 0.10 <= protein_ratio <= 0.40
        and 0.10 <= fat_ratio <= 0.45
        and 350 <= calories <= 950
    ):
        return 80

    return 60


def calculate_nutrition_score(menu: dict, profile: dict) -> float:
    """
    사용자의 목적에 따라 영양 점수를 계산한다.

    기본 goals뿐만 아니라,
    사용자가 선택한 3일 샘플 스타일의 nutrition_detail_weights도 함께 반영한다.
    """

    goals = profile.get("goals", [])
    nutrition_detail_weights = profile.get("nutrition_detail_weights", {})

    nutrients = get_menu_nutrients(menu)

    calories = nutrients["calories"]
    carbohydrate = nutrients["carbohydrate"]
    protein = nutrients["protein"]
    fat = nutrients["fat"]

    detail_scores = {
        "diet": calculate_diet_score(
            calories=calories,
            fat=fat
        ),
        "high_protein": calculate_high_protein_score(
            protein=protein
        ),
        "balance": calculate_balanced_nutrition_score(
            calories=calories,
            carbohydrate=carbohydrate,
            protein=protein,
            fat=fat
        )
    }

    if nutrition_detail_weights:
        total_weight = sum(nutrition_detail_weights.values())

        if total_weight > 0:
            weighted_score = 0

            for key, weight in nutrition_detail_weights.items():
                weighted_score += detail_scores.get(key, 0) * weight

            return round(weighted_score / total_weight, 2)

    nutrition_scores = []

    if "다이어트" in goals:
        nutrition_scores.append(detail_scores["diet"])

    if "고단백" in goals:
        nutrition_scores.append(detail_scores["high_protein"])

    if "영양 균형" in goals:
        nutrition_scores.append(detail_scores["balance"])

    if not nutrition_scores:
        return 70

    return round(sum(nutrition_scores) / len(nutrition_scores), 2)


def calculate_diversity_score(
    menu: dict,
    selected_menu_ids: list,
    penalty_strength: float
) -> float:
    """
    이미 선택된 메뉴들과 현재 메뉴가 비슷한지 확인하고 다양성 점수를 계산한다.

    현재 메뉴가 이미 선택된 메뉴와 비슷하면 사용자 다양성 선호도에 따라 감점한다.
    """

    similar_menu_ids = menu.get("similar_menu_ids", [])

    for selected_menu_id in selected_menu_ids:
        if selected_menu_id in similar_menu_ids:
            diversity_score = 100 - (100 * penalty_strength)
            return max(0, diversity_score)

    return 100