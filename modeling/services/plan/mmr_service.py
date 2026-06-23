from services.plan.menu_similarity_service import (
    calculate_max_similarity_to_exposed_menus,
)


def get_mmr_lambda(diversity_penalty_strength: float) -> float:
    """
    MMR에서 추천 점수와 다양성 중 무엇을 더 볼지 결정한다.

    lambda 값이 높을수록 final_score를 더 중요하게 본다.
    lambda 값이 낮을수록 다양성을 더 강하게 반영한다.
    """

    if diversity_penalty_strength >= 0.6:
        return 0.55

    if diversity_penalty_strength >= 0.4:
        return 0.65

    return 0.8


def calculate_mmr_score(
    menu: dict,
    exposed_menus: list[dict],
    used_menu_count: dict,
    diversity_penalty_strength: float
) -> float:
    """
    MMR 방식으로 메뉴 점수를 계산한다.

    MMR 점수는 다음 요소를 함께 반영한다.

    1. final_score
       - 사용자 조건에 얼마나 잘 맞는지

    2. max_similarity
       - 이미 노출된 메뉴와 얼마나 비슷한지

    3. use_count
       - 같은 메뉴가 이미 몇 번 사용되었는지
    """

    lambda_score = get_mmr_lambda(diversity_penalty_strength)

    final_score = menu.get("final_score", 0)

    max_similarity = calculate_max_similarity_to_exposed_menus(
        menu=menu,
        exposed_menus=exposed_menus,
    )

    menu_id = menu.get("menu_id")
    use_count = used_menu_count.get(menu_id, 0)

    relevance_score = final_score
    diversity_penalty = max_similarity * 100
    use_count_penalty = use_count * 8

    mmr_score = (
        relevance_score * lambda_score
        - diversity_penalty * (1 - lambda_score)
        - use_count_penalty
    )

    return mmr_score


def rerank_menus_by_mmr(
    recommendations: list[dict],
    exposed_menus: list[dict],
    used_menu_count: dict,
    diversity_penalty_strength: float
) -> list[dict]:
    """
    추천 후보를 MMR 점수 기준으로 재정렬한다.
    """

    reranked_menus = []

    for menu in recommendations:
        mmr_score = calculate_mmr_score(
            menu=menu,
            exposed_menus=exposed_menus,
            used_menu_count=used_menu_count,
            diversity_penalty_strength=diversity_penalty_strength,
        )

        reranked_menu = {
            **menu,
            "mmr_score": round(mmr_score, 2),
        }

        reranked_menus.append(reranked_menu)

    reranked_menus.sort(
        key=lambda menu: (
            menu.get("mmr_score", 0),
            -used_menu_count.get(menu.get("menu_id"), 0),
            menu.get("final_score", 0),
        ),
        reverse=True,
    )

    return reranked_menus