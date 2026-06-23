def get_menu_similarity_key(menu: dict) -> str:
    """
    메뉴 이름에서 핵심 메뉴명을 추출한다.

    예:
    - 담백한 닭가슴살 포케 -> 닭가슴살 포케
    - 저칼로리 닭가슴살 포케 -> 닭가슴살 포케
    - 매콤 두부 비빔밥 -> 두부 비빔밥

    목적:
    이름만 조금 다른 유사 메뉴가 연속으로 노출되는 것을 줄이기 위함이다.
    """

    name = menu.get("name", "")

    remove_words = [
        "담백한",
        "저칼로리",
        "라이트",
        "매콤",
        "간장",
        "구운",
        "고단백",
        "건강한",
        "든든한",
        "가벼운",
    ]

    for word in remove_words:
        name = name.replace(word, "")

    return name.strip()


def are_menus_similar(menu_a: dict, menu_b: dict) -> bool:
    """
    두 메뉴가 서로 유사한 메뉴인지 판단한다.

    판단 기준:
    1. menu_id가 같으면 유사
    2. similar_menu_ids에 서로 포함되면 유사
    3. 핵심 메뉴명이 같으면 유사
    4. 재료 구성이 많이 겹치면 유사
    """

    menu_a_id = menu_a.get("menu_id")
    menu_b_id = menu_b.get("menu_id")

    if menu_a_id == menu_b_id:
        return True

    menu_a_similar_ids = menu_a.get("similar_menu_ids", [])
    menu_b_similar_ids = menu_b.get("similar_menu_ids", [])

    if menu_b_id in menu_a_similar_ids:
        return True

    if menu_a_id in menu_b_similar_ids:
        return True

    if get_menu_similarity_key(menu_a) == get_menu_similarity_key(menu_b):
        return True

    menu_a_ingredients = set(menu_a.get("ingredients", []))
    menu_b_ingredients = set(menu_b.get("ingredients", []))

    if not menu_a_ingredients or not menu_b_ingredients:
        return False

    intersection_count = len(menu_a_ingredients & menu_b_ingredients)
    union_count = len(menu_a_ingredients | menu_b_ingredients)

    ingredient_similarity = intersection_count / union_count

    return ingredient_similarity >= 0.6


def is_similar_to_exposed_menus(
    menu: dict,
    exposed_menus: list[dict]
) -> bool:
    """
    현재 후보 메뉴가 이미 노출된 메뉴와 유사한지 확인한다.

    exposed_menus에는 selected_menu와 alternative_menus가 모두 포함된다.
    """

    for exposed_menu in exposed_menus:
        if are_menus_similar(menu, exposed_menu):
            return True

    return False


def calculate_mmr_score(
    menu: dict,
    exposed_menus: list[dict],
    lambda_score: float = 0.75
) -> float:
    """
    MMR 방식으로 메뉴 점수를 계산한다.

    MMR = 추천 적합도 × lambda - 유사도 패널티 × (1 - lambda)

    lambda_score가 높을수록 기존 final_score를 더 중요하게 본다.
    lambda_score가 낮을수록 다양성을 더 강하게 본다.
    """

    final_score = menu.get("final_score", 0)

    if not exposed_menus:
        return final_score

    max_similarity = 0

    menu_ingredients = set(menu.get("ingredients", []))

    for exposed_menu in exposed_menus:
        exposed_ingredients = set(exposed_menu.get("ingredients", []))

        if not menu_ingredients or not exposed_ingredients:
            continue

        intersection_count = len(menu_ingredients & exposed_ingredients)
        union_count = len(menu_ingredients | exposed_ingredients)

        similarity = intersection_count / union_count

        if are_menus_similar(menu, exposed_menu):
            similarity = max(similarity, 1)

        max_similarity = max(max_similarity, similarity)

    relevance_score = final_score
    diversity_penalty = max_similarity * 100

    return (
        relevance_score * lambda_score
        - diversity_penalty * (1 - lambda_score)
    )


def rerank_menus_with_diversity(
    candidates: list[dict],
    exposed_menus: list[dict],
    diversity_penalty_strength: float
) -> list[dict]:
    """
    후보 메뉴를 MMR 기반으로 재정렬한다.

    다양성 선호가 높을수록 lambda를 낮춰서
    기존 점수보다 다양성을 더 강하게 반영한다.
    """

    if diversity_penalty_strength >= 0.6:
        lambda_score = 0.65
    elif diversity_penalty_strength >= 0.4:
        lambda_score = 0.75
    else:
        lambda_score = 0.85

    reranked_menus = []

    for menu in candidates:
        mmr_score = calculate_mmr_score(
            menu=menu,
            exposed_menus=exposed_menus,
            lambda_score=lambda_score
        )

        reranked_menu = {
            **menu,
            "mmr_score": round(mmr_score, 2)
        }

        reranked_menus.append(reranked_menu)

    reranked_menus.sort(
        key=lambda menu: menu.get("mmr_score", 0),
        reverse=True
    )

    return reranked_menus


def select_diverse_menu(
    candidates: list[dict],
    exposed_menus: list[dict],
    diversity_penalty_strength: float
) -> dict | None:
    """
    후보 중에서 이미 노출된 메뉴와 최대한 덜 유사한 메뉴를 선택한다.

    1차: 유사하지 않은 메뉴 중 MMR 점수가 가장 높은 메뉴 선택
    2차: 모두 유사하면 MMR 점수가 가장 높은 메뉴 선택
    """

    if not candidates:
        return None

    reranked_menus = rerank_menus_with_diversity(
        candidates=candidates,
        exposed_menus=exposed_menus,
        diversity_penalty_strength=diversity_penalty_strength
    )

    for menu in reranked_menus:
        if not is_similar_to_exposed_menus(
            menu=menu,
            exposed_menus=exposed_menus
        ):
            return menu

    return reranked_menus[0]


def select_diverse_alternatives(
    candidates: list[dict],
    selected_menu: dict,
    exposed_menus: list[dict],
    diversity_penalty_strength: float,
    alternative_count: int = 2
) -> list[dict]:
    """
    대안 메뉴를 다양성을 고려해 선택한다.

    대안 메뉴는 다음 항목들과 겹치지 않도록 한다.
    1. 현재 selected_menu
    2. 이전에 노출된 selected_menu
    3. 이전에 노출된 alternative_menus
    4. 같은 meal 안에서 이미 뽑힌 alternative_menus
    """

    alternatives = []
    local_exposed_menus = exposed_menus + [selected_menu]

    available_candidates = [
        candidate
        for candidate in candidates
        if candidate.get("menu_id") != selected_menu.get("menu_id")
    ]

    while len(alternatives) < alternative_count and available_candidates:
        selected_alternative = select_diverse_menu(
            candidates=available_candidates,
            exposed_menus=local_exposed_menus,
            diversity_penalty_strength=diversity_penalty_strength
        )

        if selected_alternative is None:
            break

        alternatives.append(selected_alternative)
        local_exposed_menus.append(selected_alternative)

        available_candidates = [
            candidate
            for candidate in available_candidates
            if candidate.get("menu_id") != selected_alternative.get("menu_id")
        ]

    return alternatives