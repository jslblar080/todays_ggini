from services.plan.diversity_service import is_similar_menu


def select_menu_candidates_for_slot(
    recommendations: list[dict],
    used_menu_ids_in_day: list[int],
    recent_menu_ids: list[int],
    diversity_penalty_strength: float,
    candidate_count: int = 3,
    allow_repeat: bool = False
) -> list[dict]:
    """
    한 끼에 들어갈 후보 메뉴를 여러 개 선택한다.

    1번째 메뉴는 기본 메뉴,
    2~3번째 메뉴는 대안 메뉴로 사용한다.
    """

    candidates = []

    for menu in recommendations:
        menu_id = menu["menu_id"]

        if menu_id in used_menu_ids_in_day and not allow_repeat:
            continue

        if diversity_penalty_strength >= 0.5:
            if is_similar_menu(menu, used_menu_ids_in_day) and not allow_repeat:
                continue

        if diversity_penalty_strength >= 0.3:
            if menu_id in recent_menu_ids and not allow_repeat:
                continue

        candidates.append(menu)

    candidates.sort(
        key=lambda menu: menu["final_score"],
        reverse=True
    )

    selected_candidates = candidates[:candidate_count]

    if len(selected_candidates) < candidate_count and not allow_repeat:
        return select_menu_candidates_for_slot(
            recommendations=recommendations,
            used_menu_ids_in_day=used_menu_ids_in_day,
            recent_menu_ids=recent_menu_ids,
            diversity_penalty_strength=diversity_penalty_strength,
            candidate_count=candidate_count,
            allow_repeat=True
        )

    return selected_candidates