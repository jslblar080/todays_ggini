def build_rag_request(
    user_input,
    profile: dict,
    candidate_count: int
) -> dict:
    """
    Modeling 파트에서 RAG 파트로 넘길 요청 JSON을 생성한다.

    RAG는 후보 메뉴 검색만 담당한다.
    요리 난이도와 메뉴 예상 가격은 Modeling에서 계산한다.
    """

    return {
        "request_type": "meal_candidates",
        "candidate_count": candidate_count,
        "user_conditions": {
            "goals": profile.get("goals", []),
            "meal_budget": profile.get("meal_budget", 0),
            "preferred_categories": profile.get("preferred_categories", []),
            "ingredient_preferences": profile.get("ingredient_preferences", []),
            "allergy_ingredients": profile.get("allergy_ingredients", []),
        },
        "response_format": "candidate_menus_v1"
    }


def calculate_candidate_count(
    meal_count_per_day: int,
    period_days: int = 7,
    buffer_multiplier: int = 3
) -> int:
    """
    RAG에 요청할 후보 메뉴 개수를 계산한다.

    실제 식단에 필요한 메뉴 수보다 여유 있게 요청한다.

    예:
    하루 2끼 × 7일 × 3배수 = 42개 후보 요청
    """

    return meal_count_per_day * period_days * buffer_multiplier