from typing import Any


def get_menu_identity(menu: dict) -> str:
    """
    후보 메뉴의 중복 제거 기준이 되는 식별자를 반환한다.

    menu_id가 있으면 menu_id를 우선 사용하고,
    없으면 name/category 조합을 보조 식별자로 사용한다.
    """
    menu_id = menu.get("menu_id")

    if menu_id:
        return str(menu_id)

    name = menu.get("name", "")
    category = menu.get("category", "")

    return f"{category}:{name}"


def count_unique_menus(candidate_menus: list[dict]) -> int:
    """
    후보 메뉴 목록에서 고유 메뉴 수를 계산한다.
    """
    identities = {
        get_menu_identity(menu)
        for menu in candidate_menus
        if get_menu_identity(menu)
    }

    return len(identities)


def calculate_additional_candidate_count(
    required_meal_count: int,
    optimizer_candidate_limit: int,
    current_candidate_count: int,
) -> int:
    """
    후보 풀이 부족할 때 추가로 요청할 RAG 후보 수를 계산한다.

    너무 적게 요청하면 추가 요청 효과가 작으므로,
    required_meal_count의 40%를 최소 추가 요청량으로 사용한다.
    """
    shortage_count = max(optimizer_candidate_limit - current_candidate_count, 0)
    minimum_additional_count = int(round(required_meal_count * 0.4))

    return max(shortage_count, minimum_additional_count)


def diagnose_monthly_candidate_pool(
    candidate_menus: list[dict],
    profile: dict,
    required_meal_count: int,
    optimizer_candidate_limit: int,
    max_repeat_per_menu: int = 2,
) -> dict[str, Any]:
    """
    월간 식단 생성을 위한 후보 풀이 충분한지 진단한다.

    이 함수는 바로 RAG를 재요청하지 않고,
    후보 부족 여부와 부족 사유만 판단한다.
    """
    candidate_count = len(candidate_menus)
    unique_menu_count = count_unique_menus(candidate_menus)
    max_fillable_meal_count = unique_menu_count * max_repeat_per_menu

    shortage_reasons = []

    if candidate_count == 0:
        shortage_reasons.append("candidate_empty")

    if candidate_count < optimizer_candidate_limit:
        shortage_reasons.append("below_optimizer_candidate_limit")

    if max_fillable_meal_count < required_meal_count:
        shortage_reasons.append("below_repeat_fill_capacity")

    # 후보는 있지만 고유 메뉴가 지나치게 적으면 다양성/반복 제약에서 위험하다.
    # S10처럼 강한 제약 케이스도 성공 가능성을 남겨야 하므로 기준은 과도하게 높이지 않는다.
    minimum_unique_menu_count = max(
        int(round(required_meal_count * 0.45)),
        int(round(optimizer_candidate_limit * 0.35)),
    )

    if unique_menu_count < minimum_unique_menu_count:
        shortage_reasons.append("not_enough_unique_menus")

    is_enough = len(shortage_reasons) == 0

    recommended_next_step = (
        "use_current_candidates"
        if is_enough
        else "additional_rag_request"
    )

    additional_candidate_count = 0

    if not is_enough:
        additional_candidate_count = calculate_additional_candidate_count(
            required_meal_count=required_meal_count,
            optimizer_candidate_limit=optimizer_candidate_limit,
            current_candidate_count=candidate_count,
        )

    return {
        "is_enough": is_enough,
        "shortage_reasons": shortage_reasons,
        "candidate_count": candidate_count,
        "unique_menu_count": unique_menu_count,
        "required_meal_count": required_meal_count,
        "optimizer_candidate_limit": optimizer_candidate_limit,
        "max_repeat_per_menu": max_repeat_per_menu,
        "max_fillable_meal_count": max_fillable_meal_count,
        "minimum_unique_menu_count": minimum_unique_menu_count,
        "recommended_next_step": recommended_next_step,
        "additional_candidate_count": additional_candidate_count,
    }


def merge_candidate_menus(
    base_candidate_menus: list[dict],
    additional_candidate_menus: list[dict],
) -> list[dict]:
    """
    기존 후보와 추가 후보를 병합한다.

    동일 menu_id 또는 보조 식별자가 있는 후보는 중복으로 보고 제거한다.
    기존 후보의 순서를 우선 유지한다.
    """
    merged_menus = []
    seen_identities = set()

    for menu in base_candidate_menus + additional_candidate_menus:
        identity = get_menu_identity(menu)

        if not identity or identity in seen_identities:
            continue

        seen_identities.add(identity)
        merged_menus.append(menu)

    return merged_menus
