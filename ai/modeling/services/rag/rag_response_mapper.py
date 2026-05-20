def normalize_unit(unit: str | None) -> str | None:
    """
    단위 문자열을 비교하기 쉬운 형태로 정리한다.

    예:
    - "g" -> "g"
    - " G " -> "g"
    - "ml" -> "ml"
    """

    if not unit:
        return None

    return unit.replace(" ", "").lower()


def get_lowest_price_info(ingredient: dict) -> dict | None:
    """
    재료의 쇼핑몰 가격 정보 중 최저가 정보를 찾는다.

    반환 예:
    {
        "market": "naver_shopping",
        "lowest_price": 2300,
        "delivery_type": "일반배송",
        "product_title": "두부 300g",
        "purchase_link": "..."
    }
    """

    e_commerce_prices = ingredient.get("e_commerce_prices", {})

    lowest_market = None
    lowest_info = None
    lowest_price = None

    for market, market_info in e_commerce_prices.items():
        if not market_info:
            continue

        price = market_info.get("lowest_price")

        if price is None or price <= 0:
            continue

        if lowest_price is None or price < lowest_price:
            lowest_price = price
            lowest_market = market
            lowest_info = market_info

    if lowest_info is None:
        return None

    return {
        "market": lowest_market,
        "lowest_price": lowest_price,
        "delivery_type": lowest_info.get("delivery_type"),
        "product_title": lowest_info.get("product_title"),
        "purchase_link": lowest_info.get("purchase_link")
    }


def convert_usage_to_base_unit(
    amount: float | int | None,
    unit: str | None
) -> float | None:
    """
    재료 사용량을 계산용 단위로 변환한다.

    현재 RAG와 약속한 계산용 단위는 g 또는 ml이다.
    amount는 이미 g/ml 기준 숫자이므로 그대로 float으로 변환한다.
    """

    if amount is None:
        return None

    normalized_unit = normalize_unit(unit)

    if normalized_unit in ["g", "ml"]:
        return float(amount)

    return None


def build_failed_ingredient_cost(
    ingredient_id: str | None,
    ingredient_name: str | None,
    display_amount: str | None,
    amount: float | int | None,
    unit: str | None,
    is_estimated: bool,
    pricing_status: str,
    extra_data: dict | None = None
) -> dict:
    """
    재료 비용 계산 실패 시 공통 반환 구조를 만든다.
    """

    result = {
        "ingredient_id": ingredient_id,
        "ingredient_name": ingredient_name,
        "display_amount": display_amount,
        "amount": amount,
        "unit": unit,
        "is_estimated": is_estimated,
        "estimated_cost": 0,
        "pricing_status": pricing_status
    }

    if extra_data:
        result.update(extra_data)

    return result


def calculate_ingredient_cost(
    ingredient_usage: dict,
    ingredients_pool: dict
) -> dict:
    """
    재료 1개의 사용량 기준 비용을 계산한다.

    계산식:
    재료 사용 비용 = 최저가 × 사용량 / 판매 단위량
    """

    ingredient_id = ingredient_usage.get("ingredient_id")
    ingredient_name = ingredient_usage.get("ingredient_name")
    display_amount = ingredient_usage.get("display_amount")
    amount = ingredient_usage.get("amount")
    unit = ingredient_usage.get("unit")
    is_estimated = ingredient_usage.get("is_estimated", False)

    ingredient = ingredients_pool.get(ingredient_id)

    if not ingredient:
        return build_failed_ingredient_cost(
            ingredient_id=ingredient_id,
            ingredient_name=ingredient_name,
            display_amount=display_amount,
            amount=amount,
            unit=unit,
            is_estimated=is_estimated,
            pricing_status="ingredient_not_found"
        )

    ingredient_name = ingredient_name or ingredient.get("ingredient_name")

    lowest_price_info = get_lowest_price_info(ingredient)

    if lowest_price_info is None:
        return build_failed_ingredient_cost(
            ingredient_id=ingredient_id,
            ingredient_name=ingredient_name,
            display_amount=display_amount,
            amount=amount,
            unit=unit,
            is_estimated=is_estimated,
            pricing_status="price_not_found"
        )

    standard_amount = ingredient.get("standard_amount")
    standard_unit_type = ingredient.get("standard_unit_type")

    if standard_amount is None or standard_amount <= 0:
        return build_failed_ingredient_cost(
            ingredient_id=ingredient_id,
            ingredient_name=ingredient_name,
            display_amount=display_amount,
            amount=amount,
            unit=unit,
            is_estimated=is_estimated,
            pricing_status="standard_amount_missing",
            extra_data={
                "lowest_price": lowest_price_info["lowest_price"],
                "lowest_market": lowest_price_info["market"]
            }
        )

    if not standard_unit_type:
        return build_failed_ingredient_cost(
            ingredient_id=ingredient_id,
            ingredient_name=ingredient_name,
            display_amount=display_amount,
            amount=amount,
            unit=unit,
            is_estimated=is_estimated,
            pricing_status="standard_unit_type_missing",
            extra_data={
                "standard_amount": standard_amount,
                "lowest_price": lowest_price_info["lowest_price"],
                "lowest_market": lowest_price_info["market"]
            }
        )

    usage_amount = convert_usage_to_base_unit(
        amount=amount,
        unit=unit
    )

    if usage_amount is None:
        return build_failed_ingredient_cost(
            ingredient_id=ingredient_id,
            ingredient_name=ingredient_name,
            display_amount=display_amount,
            amount=amount,
            unit=unit,
            is_estimated=is_estimated,
            pricing_status="usage_unit_not_supported",
            extra_data={
                "standard_amount": standard_amount,
                "standard_unit_type": standard_unit_type,
                "lowest_price": lowest_price_info["lowest_price"],
                "lowest_market": lowest_price_info["market"]
            }
        )

    normalized_usage_unit = normalize_unit(unit)
    normalized_standard_unit_type = normalize_unit(standard_unit_type)

    if normalized_usage_unit != normalized_standard_unit_type:
        return build_failed_ingredient_cost(
            ingredient_id=ingredient_id,
            ingredient_name=ingredient_name,
            display_amount=display_amount,
            amount=amount,
            unit=unit,
            is_estimated=is_estimated,
            pricing_status="unit_mismatch",
            extra_data={
                "standard_amount": standard_amount,
                "standard_unit_type": standard_unit_type,
                "lowest_price": lowest_price_info["lowest_price"],
                "lowest_market": lowest_price_info["market"]
            }
        )

    estimated_cost = lowest_price_info["lowest_price"] * (
        usage_amount / standard_amount
    )

    return {
        "ingredient_id": ingredient_id,
        "ingredient_name": ingredient_name,
        "display_amount": display_amount,
        "amount": amount,
        "unit": unit,
        "is_estimated": is_estimated,
        "standard_amount": standard_amount,
        "standard_unit_type": standard_unit_type,
        "lowest_price": lowest_price_info["lowest_price"],
        "lowest_market": lowest_price_info["market"],
        "delivery_type": lowest_price_info.get("delivery_type"),
        "product_title": lowest_price_info.get("product_title"),
        "purchase_link": lowest_price_info.get("purchase_link"),
        "estimated_cost": round(estimated_cost),
        "pricing_status": "calculated"
    }


def calculate_menu_estimated_cost(
    candidate_menu: dict,
    ingredients_pool: dict
) -> dict:
    """
    메뉴의 재료 사용량과 재료 가격 정보를 바탕으로
    메뉴 1끼 예상 가격을 계산한다.

    계산에 실패하면 RAG가 제공한 estimated_cost를 fallback으로 사용한다.
    """

    ingredient_usages = candidate_menu.get("ingredient_usages", [])
    ingredient_costs = []
    total_cost = 0

    for ingredient_usage in ingredient_usages:
        ingredient_cost = calculate_ingredient_cost(
            ingredient_usage=ingredient_usage,
            ingredients_pool=ingredients_pool
        )

        ingredient_costs.append(ingredient_cost)
        total_cost += ingredient_cost.get("estimated_cost", 0)

    pricing_statuses = [
        ingredient_cost.get("pricing_status")
        for ingredient_cost in ingredient_costs
    ]

    if not ingredient_costs:
        pricing_status = "no_ingredient_usages"
    elif all(status == "calculated" for status in pricing_statuses):
        pricing_status = "calculated"
    elif any(status == "calculated" for status in pricing_statuses):
        pricing_status = "partially_calculated"
    else:
        pricing_status = "not_calculated"

    rag_estimated_cost = candidate_menu.get("estimated_cost")

    if total_cost > 0:
        final_estimated_cost = round(total_cost)
    else:
        final_estimated_cost = rag_estimated_cost

    return {
        "estimated_cost": final_estimated_cost,
        "rag_estimated_cost": rag_estimated_cost,
        "ingredient_costs": ingredient_costs,
        "pricing_status": pricing_status
    }


def calculate_ingredient_count(candidate_menu: dict) -> int:
    """
    메뉴의 재료 개수를 계산한다.

    ingredient_usages가 일부 재료만 포함할 수 있으므로,
    ingredients, recipe.required_ingredients까지 함께 보고 가장 큰 값을 사용한다.
    """

    ingredient_usages = candidate_menu.get("ingredient_usages", [])
    ingredients = candidate_menu.get("ingredients", [])

    recipe = candidate_menu.get("recipe", {})
    required_ingredients = recipe.get("required_ingredients", [])

    return max(
        len(ingredient_usages),
        len(ingredients),
        len(required_ingredients)
    )


def calculate_recipe_step_count(candidate_menu: dict) -> int:
    """
    레시피 단계 수를 계산한다.
    """

    recipe = candidate_menu.get("recipe", {})
    steps = recipe.get("steps", [])

    return len(steps)


def calculate_cooking_time(candidate_menu: dict) -> int:
    """
    레시피 조리 시간을 가져온다.

    조리 시간이 없으면 0으로 처리한다.
    0은 '정보 없음'에 가깝기 때문에 난이도 가산점에는 크게 반영하지 않는다.
    """

    recipe = candidate_menu.get("recipe", {})
    cooking_time = recipe.get("cooking_time")

    if cooking_time is None:
        return 0

    return cooking_time


def calculate_estimated_usage_ratio(candidate_menu: dict) -> float:
    """
    ingredient_usages 중 is_estimated가 true인 재료 비율을 계산한다.

    추정 단위가 많은 메뉴는 계량 불확실성이 있으므로
    난이도 계산에 약하게 반영한다.
    """

    ingredient_usages = candidate_menu.get("ingredient_usages", [])

    if not ingredient_usages:
        return 0

    estimated_count = 0

    for usage in ingredient_usages:
        if usage.get("is_estimated", False):
            estimated_count += 1

    return estimated_count / len(ingredient_usages)


def calculate_ingredient_count_points(ingredient_count: int) -> int:
    """
    재료 개수에 따른 난이도 가산점을 계산한다.
    """

    if ingredient_count <= 4:
        return 0

    if ingredient_count <= 6:
        return 1

    if ingredient_count <= 8:
        return 2

    return 3


def calculate_step_count_points(step_count: int) -> int:
    """
    레시피 단계 수에 따른 난이도 가산점을 계산한다.
    """

    if step_count <= 3:
        return 0

    if step_count <= 5:
        return 1

    if step_count <= 7:
        return 2

    return 3


def calculate_cooking_time_points(cooking_time: int) -> int:
    """
    조리 시간에 따른 난이도 가산점을 계산한다.
    """

    if cooking_time <= 0:
        return 0

    if cooking_time <= 10:
        return 0

    if cooking_time <= 20:
        return 1

    if cooking_time <= 30:
        return 2

    return 3


def calculate_estimated_usage_points(estimated_usage_ratio: float) -> int:
    """
    추정 재료 비율에 따른 보조 난이도 가산점을 계산한다.
    """

    if estimated_usage_ratio <= 0.3:
        return 0

    if estimated_usage_ratio <= 0.6:
        return 1

    return 1


def calculate_action_difficulty_points(steps: list[str]) -> int:
    """
    레시피 문장에 포함된 조리 동작 키워드를 바탕으로
    난이도 가산점을 계산한다.

    너무 과하게 반영되지 않도록 최대 2점까지만 부여한다.
    """

    if not steps:
        return 0

    basic_action_keywords = [
        "자르",
        "썰",
        "손질",
        "올리",
        "섞",
        "곁들"
    ]

    heat_action_keywords = [
        "삶",
        "굽",
        "볶",
        "끓",
        "데우",
        "익히"
    ]

    hard_action_keywords = [
        "튀기",
        "반죽",
        "숙성",
        "졸이",
        "데치",
        "찜"
    ]

    joined_steps = " ".join(steps)

    points = 0

    if any(keyword in joined_steps for keyword in basic_action_keywords):
        points += 1

    if any(keyword in joined_steps for keyword in heat_action_keywords):
        points += 1

    if any(keyword in joined_steps for keyword in hard_action_keywords):
        points += 2

    return min(points, 2)


def convert_points_to_difficulty(difficulty_points: int) -> int:
    """
    difficulty_points를 1~5 난이도로 변환한다.
    """

    if difficulty_points <= 1:
        return 1

    if difficulty_points <= 3:
        return 2

    if difficulty_points <= 5:
        return 3

    if difficulty_points <= 7:
        return 4

    return 5


def calculate_difficulty_from_recipe(candidate_menu: dict) -> dict:
    """
    Modeling에서 레시피와 재료 정보를 바탕으로 난이도를 계산한다.

    difficulty:
    1 = 매우 쉬움
    2 = 쉬움
    3 = 보통
    4 = 어려움
    5 = 매우 어려움
    """

    ingredient_count = calculate_ingredient_count(candidate_menu)
    step_count = calculate_recipe_step_count(candidate_menu)
    cooking_time = calculate_cooking_time(candidate_menu)

    recipe = candidate_menu.get("recipe", {})
    steps = recipe.get("steps", [])

    estimated_usage_ratio = calculate_estimated_usage_ratio(candidate_menu)

    ingredient_points = calculate_ingredient_count_points(
        ingredient_count=ingredient_count
    )

    step_points = calculate_step_count_points(
        step_count=step_count
    )

    cooking_time_points = calculate_cooking_time_points(
        cooking_time=cooking_time
    )

    action_points = calculate_action_difficulty_points(
        steps=steps
    )

    estimated_usage_points = calculate_estimated_usage_points(
        estimated_usage_ratio=estimated_usage_ratio
    )

    difficulty_points = (
        ingredient_points
        + step_points
        + cooking_time_points
        + action_points
        + estimated_usage_points
    )

    difficulty = convert_points_to_difficulty(
        difficulty_points=difficulty_points
    )

    return {
        "difficulty": difficulty,
        "difficulty_detail": {
            "ingredient_count": ingredient_count,
            "step_count": step_count,
            "cooking_time": cooking_time,
            "estimated_usage_ratio": round(estimated_usage_ratio, 2),
            "ingredient_points": ingredient_points,
            "step_points": step_points,
            "cooking_time_points": cooking_time_points,
            "action_points": action_points,
            "estimated_usage_points": estimated_usage_points,
            "difficulty_points": difficulty_points
        }
    }


def map_candidate_menu_to_modeling_menu(
    candidate_menu: dict,
    ingredients_pool: dict
) -> dict:
    """
    RAG의 candidate_menu를 기존 추천 로직이 사용하는 menu 구조로 변환한다.
    """

    nutrient_summary = candidate_menu.get("nutrient_summary", {})

    cost_result = calculate_menu_estimated_cost(
        candidate_menu=candidate_menu,
        ingredients_pool=ingredients_pool
    )

    difficulty_result = calculate_difficulty_from_recipe(
        candidate_menu=candidate_menu
    )

    return {
        "menu_id": candidate_menu.get("menu_id"),
        "name": candidate_menu.get("name"),
        "category": candidate_menu.get("category"),
        "ingredient_groups": candidate_menu.get("ingredient_groups", []),
        "ingredients": candidate_menu.get("ingredients", []),
        "calories": candidate_menu.get("calories", 0),

        "nutrient_summary": {
            "carbohydrate": nutrient_summary.get("carbohydrate", 0),
            "protein": nutrient_summary.get("protein", 0),
            "fat": nutrient_summary.get("fat", 0)
        },
        "carbohydrate": nutrient_summary.get("carbohydrate", 0),
        "protein": nutrient_summary.get("protein", 0),
        "fat": nutrient_summary.get("fat", 0),

        "estimated_cost": cost_result["estimated_cost"],
        "rag_estimated_cost": cost_result["rag_estimated_cost"],
        "pricing_status": cost_result["pricing_status"],
        "ingredient_costs": cost_result["ingredient_costs"],

        "difficulty": difficulty_result["difficulty"],
        "difficulty_detail": difficulty_result["difficulty_detail"],

        "ingredient_usages": candidate_menu.get("ingredient_usages", []),
        "similar_menu_ids": candidate_menu.get("similar_menu_ids", []),
        "allergy_ingredients": candidate_menu.get("allergy_ingredients", []),
        "recipe": candidate_menu.get("recipe", {})
    }


def map_rag_response_to_candidate_menus(rag_response: dict) -> list[dict]:
    """
    RAG 응답을 Modeling 내부 candidate_menus 구조로 변환한다.

    RAG 응답 구조:
    {
        "response_format": "candidate_menus_v1",
        "candidate_menus": [...],
        "ingredients_pool": {...}
    }

    candidate_menus는 메뉴 후보 목록이고,
    ingredients_pool은 재료별 가격 계산에 사용한다.
    """

    if isinstance(rag_response, list):
        raw_menus = rag_response
        ingredients_pool = {}

    elif isinstance(rag_response, dict):
        raw_menus = (
            rag_response.get("candidate_menus")
            or rag_response.get("menus")
            or rag_response.get("data")
            or []
        )
        ingredients_pool = rag_response.get("ingredients_pool", {})

    else:
        raw_menus = []
        ingredients_pool = {}

    candidate_menus = []

    for menu in raw_menus:
        mapped_menu = map_candidate_menu_to_modeling_menu(
            candidate_menu=menu,
            ingredients_pool=ingredients_pool,
        )

        candidate_menus.append(mapped_menu)

    return candidate_menus