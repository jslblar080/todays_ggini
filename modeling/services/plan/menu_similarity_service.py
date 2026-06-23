STYLE_PREFIX_WORDS = [
    "담백한",
    "매콤",
    "간장",
    "저칼로리",
    "고단백",
    "든든한",
    "가벼운",
    "프리미엄",
    "간편",
    "건강한",
    "저염",
    "다이어트",
    "구운",
    "라이트",
]


def normalize_menu_name(name: str | None) -> str:
    """
    메뉴 이름에서 스타일 수식어를 제거해 유사 메뉴 비교용 이름을 만든다.
    """

    if not name:
        return ""

    normalized_name = name.strip()

    for prefix_word in STYLE_PREFIX_WORDS:
        if normalized_name.startswith(prefix_word + " "):
            normalized_name = normalized_name.replace(prefix_word + " ", "", 1)

    return normalized_name.strip()


def get_menu_ingredient_set(menu: dict) -> set:
    """
    메뉴의 재료 목록을 set 형태로 가져온다.
    """

    return set(menu.get("ingredients", []))


def get_menu_ingredient_group_set(menu: dict) -> set:
    """
    메뉴의 재료군 목록을 set 형태로 가져온다.
    """

    return set(menu.get("ingredient_groups", []))


def calculate_jaccard_similarity(first_values: set, second_values: set) -> float:
    """
    두 집합의 Jaccard 유사도를 계산한다.
    """

    if not first_values or not second_values:
        return 0

    intersection_count = len(first_values & second_values)
    union_count = len(first_values | second_values)

    if union_count == 0:
        return 0

    return intersection_count / union_count


def calculate_ingredient_similarity(
    first_menu: dict,
    second_menu: dict
) -> float:
    """
    두 메뉴의 재료 유사도를 계산한다.
    """

    return calculate_jaccard_similarity(
        get_menu_ingredient_set(first_menu),
        get_menu_ingredient_set(second_menu),
    )


def calculate_ingredient_group_similarity(
    first_menu: dict,
    second_menu: dict
) -> float:
    """
    두 메뉴의 재료군 유사도를 계산한다.
    """

    return calculate_jaccard_similarity(
        get_menu_ingredient_group_set(first_menu),
        get_menu_ingredient_group_set(second_menu),
    )


def calculate_menu_similarity_score(
    first_menu: dict,
    second_menu: dict
) -> float:
    """
    두 메뉴의 유사도를 0~1 사이 점수로 계산한다.

    menu_id, similar_menu_ids, 정규화된 이름이 같으면 거의 같은 메뉴로 본다.
    그 외에는 재료 유사도, 재료군 유사도, 카테고리 유사도를 함께 본다.
    """

    first_menu_id = first_menu.get("menu_id")
    second_menu_id = second_menu.get("menu_id")

    if first_menu_id is not None and second_menu_id is not None:
        if first_menu_id == second_menu_id:
            return 1

    first_similar_menu_ids = first_menu.get("similar_menu_ids", [])
    second_similar_menu_ids = second_menu.get("similar_menu_ids", [])

    if second_menu_id in first_similar_menu_ids:
        return 1

    if first_menu_id in second_similar_menu_ids:
        return 1

    first_name = normalize_menu_name(first_menu.get("name"))
    second_name = normalize_menu_name(second_menu.get("name"))

    if first_name and second_name and first_name == second_name:
        return 1

    ingredient_similarity = calculate_ingredient_similarity(
        first_menu=first_menu,
        second_menu=second_menu,
    )

    ingredient_group_similarity = calculate_ingredient_group_similarity(
        first_menu=first_menu,
        second_menu=second_menu,
    )

    category_similarity = 0

    if first_menu.get("category") == second_menu.get("category"):
        category_similarity = 0.2

    return max(
        ingredient_similarity,
        ingredient_group_similarity * 0.8,
        category_similarity,
    )


def are_menus_similar(
    first_menu: dict,
    second_menu: dict
) -> bool:
    """
    두 메뉴가 서로 유사한지 판단한다.
    """

    similarity_score = calculate_menu_similarity_score(
        first_menu=first_menu,
        second_menu=second_menu,
    )

    return similarity_score >= 0.6


def get_recent_exposed_menus(
    days: list[dict],
    recent_day_window: int
) -> list[dict]:
    """
    최근 N일 안에 사용자에게 노출된 메뉴를 가져온다.

    여기서 노출된 메뉴는 selected_menu뿐만 아니라 alternative_menus도 포함한다.
    """

    if recent_day_window <= 0:
        return []

    recent_days = days[-recent_day_window:]
    exposed_menus = []

    for day in recent_days:
        for meal in day.get("meals", []):
            selected_menu = meal.get("selected_menu")

            if selected_menu:
                exposed_menus.append(selected_menu)

            for alternative_menu in meal.get("alternative_menus", []):
                exposed_menus.append(alternative_menu)

    return exposed_menus


def is_similar_to_exposed_menus(
    menu: dict,
    exposed_menus: list[dict]
) -> bool:
    """
    현재 후보 메뉴가 이미 노출된 메뉴와 유사한지 확인한다.
    """

    for exposed_menu in exposed_menus:
        if are_menus_similar(menu, exposed_menu):
            return True

    return False


def is_similar_to_any_menu(
    menu: dict,
    menus: list[dict]
) -> bool:
    """
    현재 후보 메뉴가 주어진 메뉴 목록 중 하나라도 유사한지 확인한다.
    """

    for target_menu in menus:
        if are_menus_similar(menu, target_menu):
            return True

    return False


def calculate_max_similarity_to_exposed_menus(
    menu: dict,
    exposed_menus: list[dict]
) -> float:
    """
    후보 메뉴가 이미 노출된 메뉴들과 얼마나 유사한지 계산한다.
    """

    if not exposed_menus:
        return 0

    max_similarity = 0

    for exposed_menu in exposed_menus:
        similarity_score = calculate_menu_similarity_score(
            first_menu=menu,
            second_menu=exposed_menu,
        )

        if similarity_score > max_similarity:
            max_similarity = similarity_score

    return max_similarity