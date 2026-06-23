def get_recent_day_window(diversity_penalty_strength: float) -> int:
    """
    메뉴 다양성 감점 강도에 따라 최근 며칠 동안 먹은 메뉴를 피할지 결정한다.
    """

    if diversity_penalty_strength <= 0.1:
        return 0

    if diversity_penalty_strength <= 0.3:
        return 1

    return 2


def is_similar_menu(menu: dict, selected_menu_ids: list[int]) -> bool:
    """
    현재 메뉴가 이미 선택된 메뉴들과 유사한지 확인한다.
    """

    similar_menu_ids = menu.get("similar_menu_ids", [])

    for selected_menu_id in selected_menu_ids:
        if selected_menu_id in similar_menu_ids:
            return True

    return False