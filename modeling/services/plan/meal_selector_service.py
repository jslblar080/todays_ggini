from services.plan.menu_similarity_service import (
    are_menus_similar,
    is_similar_to_any_menu,
    is_similar_to_exposed_menus,
)

from services.plan.mmr_service import (
    rerank_menus_by_mmr,
)


def filter_menus_by_style_priority(
    menus: list[dict],
    profile: dict
) -> list[dict]:
    """
    선택된 스타일에 따라 월간 배치에서 우선적으로 고려할 후보 메뉴를 걸러낸다.

    이 함수는 하드 필터가 아니다.
    스타일에 더 잘 맞는 후보를 먼저 시도하되,
    후보가 너무 좁아져 반복이 심해지면 전체 후보를 유지한다.
    """

    selected_style_goal = profile.get("selected_style_goal")

    if selected_style_goal == "고단백":
        protein_30_menus = [
            menu for menu in menus
            if menu.get("protein", 0) >= 30
        ]

        if len(protein_30_menus) >= 20:
            return protein_30_menus

        protein_25_menus = [
            menu for menu in menus
            if menu.get("protein", 0) >= 25
        ]

        if len(protein_25_menus) >= 20:
            return protein_25_menus

        protein_22_menus = [
            menu for menu in menus
            if menu.get("protein", 0) >= 22
        ]

        if len(protein_22_menus) >= 20:
            return protein_22_menus

        return menus

    if selected_style_goal == "간편식":
        difficulty_70_menus = [
            menu for menu in menus
            if menu.get("scores", {}).get("difficulty", 0) >= 70
        ]

        if len(difficulty_70_menus) >= 20:
            return difficulty_70_menus

        difficulty_60_menus = [
            menu for menu in menus
            if menu.get("scores", {}).get("difficulty", 0) >= 60
        ]

        if len(difficulty_60_menus) >= 20:
            return difficulty_60_menus

    return menus


def sort_style_priority_menus(
    menus: list[dict],
    profile: dict
) -> list[dict]:
    """
    스타일별 우선 후보 안에서도 더 적합한 메뉴가 먼저 오도록 정렬한다.
    """

    selected_style_goal = profile.get("selected_style_goal")

    if selected_style_goal == "고단백":
        return sorted(
            menus,
            key=lambda menu: (
                menu.get("mmr_score", 0),
                menu.get("protein", 0),
                menu.get("final_score", 0)
            ),
            reverse=True
        )

    if selected_style_goal == "간편식":
        return sorted(
            menus,
            key=lambda menu: (
                menu.get("mmr_score", 0),
                menu.get("scores", {}).get("difficulty", 0),
                menu.get("final_score", 0)
            ),
            reverse=True
        )

    return menus


def select_menu_for_meal(
    recommendations: list[dict],
    exposed_menus: list[dict],
    used_menu_count: dict,
    diversity_penalty_strength: float,
    profile: dict
) -> dict:
    """
    한 끼에 들어갈 대표 메뉴를 선택한다.

    선택 기준:
    1. MMR 점수가 높은 메뉴 우선
    2. 선택된 스타일에 맞는 후보 우선
    3. 최근 노출 메뉴와 유사하지 않은 메뉴 우선
    4. 조건을 만족하는 후보가 없으면 MMR 순서로 fallback
    """

    reranked_menus = rerank_menus_by_mmr(
        recommendations=recommendations,
        exposed_menus=exposed_menus,
        used_menu_count=used_menu_count,
        diversity_penalty_strength=diversity_penalty_strength
    )

    style_priority_menus = filter_menus_by_style_priority(
        menus=reranked_menus,
        profile=profile
    )

    style_priority_menus = sort_style_priority_menus(
        menus=style_priority_menus,
        profile=profile
    )

    for menu in style_priority_menus:
        if not is_similar_to_exposed_menus(
            menu=menu,
            exposed_menus=exposed_menus
        ):
            return menu

    if style_priority_menus:
        return style_priority_menus[0]

    for menu in reranked_menus:
        if not is_similar_to_exposed_menus(
            menu=menu,
            exposed_menus=exposed_menus
        ):
            return menu

    return reranked_menus[0]


def select_alternative_menus(
    recommendations: list[dict],
    selected_menu: dict,
    exposed_menus: list[dict],
    used_menu_count: dict,
    diversity_penalty_strength: float,
    alternative_count: int = 2
) -> list[dict]:
    """
    선택 메뉴에 대한 대체 메뉴를 고른다.

    대안 메뉴는 사용자의 다양성 설정과 관계없이 항상 높은 다양성 기준을 적용한다.
    """

    alternative_menus = []
    alternative_diversity_strength = max(diversity_penalty_strength, 0.8)
    local_exposed_menus = exposed_menus + [selected_menu]

    reranked_menus = rerank_menus_by_mmr(
        recommendations=recommendations,
        exposed_menus=local_exposed_menus,
        used_menu_count=used_menu_count,
        diversity_penalty_strength=alternative_diversity_strength,
    )

    for candidate_menu in reranked_menus:
        if candidate_menu.get("menu_id") == selected_menu.get("menu_id"):
            continue

        if are_menus_similar(candidate_menu, selected_menu):
            continue

        if is_similar_to_exposed_menus(
            menu=candidate_menu,
            exposed_menus=local_exposed_menus,
        ):
            continue

        if is_similar_to_any_menu(
            menu=candidate_menu,
            menus=alternative_menus,
        ):
            continue

        alternative_menus.append(candidate_menu)
        local_exposed_menus.append(candidate_menu)

        if len(alternative_menus) >= alternative_count:
            return alternative_menus

    for candidate_menu in reranked_menus:
        if len(alternative_menus) >= alternative_count:
            break

        if candidate_menu.get("menu_id") == selected_menu.get("menu_id"):
            continue

        if are_menus_similar(candidate_menu, selected_menu):
            continue

        if candidate_menu in alternative_menus:
            continue

        if is_similar_to_any_menu(
            menu=candidate_menu,
            menus=alternative_menus,
        ):
            continue

        alternative_menus.append(candidate_menu)
        local_exposed_menus.append(candidate_menu)

    return alternative_menus


def increase_used_menu_count(
    used_menu_count: dict,
    menu: dict,
    amount: float = 1
) -> None:
    """
    메뉴 사용 횟수를 증가시킨다.
    """

    menu_id = menu.get("menu_id")

    if menu_id is None:
        return

    used_menu_count[menu_id] = used_menu_count.get(menu_id, 0) + amount