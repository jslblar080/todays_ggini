import logging
from collections import Counter
from contextvars import ContextVar

from services.rag.ingredient_group_mapper import fill_missing_ingredient_groups

logger = logging.getLogger(__name__)

_RAG_MAPPING_DIAGNOSTICS_EVENTS: ContextVar[list[dict] | None] = (
    ContextVar("rag_mapping_diagnostics_events", default=None)
)


def clear_rag_mapping_diagnostics() -> None:
    """
    실험 실행 단위에서 RAG mapping diagnostics를 초기화한다.

    서비스 응답 payload에는 포함하지 않고,
    experiments runner가 result artifact에만 저장하기 위한 진단 정보이다.
    """

    _RAG_MAPPING_DIAGNOSTICS_EVENTS.set([])


def merge_counter_dicts(events: list[dict], key: str) -> dict:
    """
    diagnostics event에 저장된 count dict를 합산한다.
    """

    merged: dict[str, int] = {}

    for event in events:
        counter = event.get(key) or {}

        for item_key, count in counter.items():
            merged[item_key] = merged.get(item_key, 0) + int(count or 0)

    return merged


def merge_quality_issue_examples(
    events: list[dict],
    max_examples_per_issue: int = 5,
) -> dict:
    """
    diagnostics event에 저장된 quality issue 대표 샘플을 issue type별로 병합한다.
    """

    merged: dict[str, list[dict]] = {}

    for event in events:
        examples = event.get("quality_issue_examples") or {}

        for issue_type, issue_examples in examples.items():
            merged.setdefault(issue_type, [])

            for example in issue_examples:
                if len(merged[issue_type]) >= max_examples_per_issue:
                    break

                merged[issue_type].append(example)

    return merged


def build_quality_issue_example(
    candidate_menu: dict,
    issue_type: str,
) -> dict:
    """
    품질 이슈 원인 확인을 위한 대표 샘플을 만든다.

    이 값은 서비스 응답 payload가 아니라 experiment diagnostics artifact에만 저장된다.
    """

    nutrient_summary = candidate_menu.get("nutrient_summary") or {}
    ingredients = candidate_menu.get("ingredients") or []
    ingredient_groups = candidate_menu.get("ingredient_groups") or []
    ingredient_usages = candidate_menu.get("ingredient_usages") or []

    return {
        "issue_type": issue_type,
        "menu_id": candidate_menu.get("menu_id"),
        "name": candidate_menu.get("name"),
        "category": candidate_menu.get("category"),
        "ingredients_count": len(ingredients),
        "ingredient_groups_count": len(ingredient_groups),
        "ingredient_usages_count": len(ingredient_usages),
        "ingredients_preview": ingredients[:10],
        "calories": candidate_menu.get("calories"),
        "protein": (
            candidate_menu.get("protein")
            if candidate_menu.get("protein") is not None
            else nutrient_summary.get("protein")
        ),
        "carbohydrate": (
            candidate_menu.get("carbohydrate")
            if candidate_menu.get("carbohydrate") is not None
            else nutrient_summary.get("carbohydrate")
        ),
        "fat": (
            candidate_menu.get("fat")
            if candidate_menu.get("fat") is not None
            else nutrient_summary.get("fat")
        ),
    }


def get_rag_mapping_diagnostics() -> dict:
    """
    현재까지 수집된 RAG mapping diagnostics를 반환한다.
    """

    events = list(_RAG_MAPPING_DIAGNOSTICS_EVENTS.get() or [])

    total_raw_menus = sum(event["raw_menus"] for event in events)
    total_mapped_menus = sum(event["mapped_menus"] for event in events)
    total_excluded_menus = sum(event["excluded_menus"] for event in events)
    total_quality_issue_menus = sum(
        event["quality_issue_menus"]
        for event in events
    )
    quality_issue_type_count = merge_counter_dicts(
        events=events,
        key="quality_issue_type_count",
    )
    quality_issue_examples = merge_quality_issue_examples(events)
    ingredient_group_mapping_status_count = merge_counter_dicts(
        events=events,
        key="ingredient_group_mapping_status_count",
    )

    mapping_success_rate = (
        round(total_mapped_menus / total_raw_menus, 4)
        if total_raw_menus
        else 0
    )

    quality_issue_rate = (
        round(total_quality_issue_menus / total_mapped_menus, 4)
        if total_mapped_menus
        else 0
    )

    return {
        "event_count": len(events),
        "raw_menus": total_raw_menus,
        "mapped_menus": total_mapped_menus,
        "excluded_menus": total_excluded_menus,
        "quality_issue_menus": total_quality_issue_menus,
        "quality_issue_type_count": quality_issue_type_count,
        "quality_issue_examples": quality_issue_examples,
        "ingredient_group_mapping_status_count": ingredient_group_mapping_status_count,
        "mapping_success_rate": mapping_success_rate,
        "quality_issue_rate": quality_issue_rate,
        "events": events,
    }


def record_rag_mapping_diagnostics(
    raw_menus: int,
    mapped_menus: int,
    excluded_menus: int,
    quality_issue_menus: int,
    quality_issue_type_count: dict | None = None,
    quality_issue_examples: dict | None = None,
    ingredient_group_mapping_status_count: dict | None = None,
) -> None:
    """
    RAG mapper 호출 단위 diagnostics를 기록한다.
    """

    mapping_success_rate = (
        round(mapped_menus / raw_menus, 4)
        if raw_menus
        else 0
    )

    quality_issue_rate = (
        round(quality_issue_menus / mapped_menus, 4)
        if mapped_menus
        else 0
    )

    events = _RAG_MAPPING_DIAGNOSTICS_EVENTS.get()

    if events is None:
        return

    events.append({
        "raw_menus": raw_menus,
        "mapped_menus": mapped_menus,
        "excluded_menus": excluded_menus,
        "quality_issue_menus": quality_issue_menus,
        "quality_issue_type_count": quality_issue_type_count or {},
        "quality_issue_examples": quality_issue_examples or {},
        "ingredient_group_mapping_status_count": ingredient_group_mapping_status_count or {},
        "ingredient_group_mapping_status_count": (
            ingredient_group_mapping_status_count or {}
        ),
        "mapping_success_rate": mapping_success_rate,
        "quality_issue_rate": quality_issue_rate,
    })

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


def normalize_ingredient_name(ingredient_name: str | None) -> str:
    """
    재료명을 비교하기 쉬운 형태로 정리한다.

    예:
    - " 물 " -> "물"
    - "후추 가루" -> "후추가루"
    """

    if not ingredient_name:
        return ""

    return ingredient_name.replace(" ", "").strip()


# def is_basic_pantry_ingredient(ingredient_name: str | None) -> bool:
#     """
#     기본 조미료/기본 재료 여부를 판단한다.

#     이런 재료는 메뉴 1회 조리 비용에 그대로 반영하면
#     가격이 과도하게 계산될 수 있으므로 estimated_cost를 0으로 처리한다.
#     """

#     normalized_name = normalize_ingredient_name(ingredient_name)

#     basic_ingredients = {
#         "물",
#         "생수",
#         "정수",
#         "소금",
#         "후추",
#         "후추가루",
#         "후춧가루",
#     }

#     return normalized_name in basic_ingredients

def is_water_ingredient(ingredient_name: str | None) -> bool:
    """
    물 계열 재료인지 확인한다.

    물은 1g과 1ml를 거의 동일하게 볼 수 있으므로,
    사용량 단위와 판매 기준 단위가 g/ml로 엇갈려도 계산할 수 있게 처리한다.
    """

    normalized_name = normalize_ingredient_name(ingredient_name)

    water_names = {
        "물",
        "생수",
        "정수",
    }

    return normalized_name in water_names


def is_convertible_water_unit(
    ingredient_name: str | None,
    usage_unit: str | None,
    standard_unit_type: str | None
) -> bool:
    """
    물 재료의 g/ml 단위 불일치를 허용할 수 있는지 확인한다.

    예:
    - 사용량: 500g, 판매 기준: 2000ml
    - 사용량: 500ml, 판매 기준: 2000g

    물은 1g ≒ 1ml로 간주하여 계산 가능하게 처리한다.
    """

    if not is_water_ingredient(ingredient_name):
        return False

    normalized_usage_unit = normalize_unit(usage_unit)
    normalized_standard_unit_type = normalize_unit(standard_unit_type)

    return {
        normalized_usage_unit,
        normalized_standard_unit_type
    } == {"g", "ml"}


# def build_basic_pantry_ingredient_cost(
#     ingredient_id: str | None,
#     ingredient_name: str | None,
#     display_amount: str | None,
#     amount: float | int | None,
#     unit: str | None,
#     is_estimated: bool,
# ) -> dict:
#     """
#     기본 재료 비용 계산 결과를 만든다.

#     물, 소금, 후추처럼 보통 가정에 기본적으로 있다고 보는 재료는
#     메뉴 예상 비용 계산에서 0원으로 처리한다.
#     """

#     return {
#         "ingredient_id": ingredient_id,
#         "ingredient_name": ingredient_name,
#         "display_amount": display_amount,
#         "amount": amount,
#         "unit": unit,
#         "is_estimated": is_estimated,
#         "estimated_cost": 0,
#         "pricing_status": "basic_pantry_ingredient"
#     }


NON_FOOD_PRODUCT_KEYWORDS = [
    "와인잔",
    "글라스",
    "컵",
    "머그",
    "접시",
    "그릇",
    "식기",
    "용기",
    "도마",
    "칼",
    "냄비",
    "팬",
    "프라이팬",
    "로션",
    "크림",
    "샴푸",
    "바디워시",
    "세제",
    "비누",
    "화장품",
]


def normalize_text_for_matching(value: str | None) -> str:
    """
    상품명 비교를 위해 공백과 대소문자를 정규화한다.
    """

    if not value:
        return ""

    return value.replace(" ", "").lower()


def is_invalid_product_match(
    product_title: str | None,
) -> bool:
    """
    매칭된 상품명이 식재료가 아닌 상품으로 보이는지 확인한다.
    """

    normalized_title = normalize_text_for_matching(product_title)

    if not normalized_title:
        return False

    for keyword in NON_FOOD_PRODUCT_KEYWORDS:
        if normalize_text_for_matching(keyword) in normalized_title:
            return True

    return False


def is_price_outlier(
    estimated_cost: float,
    standard_amount: float,
    standard_unit_type: str | None,
) -> bool:
    """
    표준 단위 기준 가격이 지나치게 높은 경우 이상치로 판단한다.

    1차 기준:
    - g/ml 기준 100g 또는 100ml당 30,000원 초과 시 이상치
    """

    normalized_unit = normalize_unit(standard_unit_type)

    if normalized_unit not in ["g", "ml"]:
        return False

    if standard_amount <= 0:
        return False

    cost_per_100_unit = estimated_cost * (100 / standard_amount)

    return cost_per_100_unit > 30000


def is_cost_gap_outlier(
    calculated_cost: float,
    rag_estimated_cost: float | int | None,
    max_ratio: float = 3.0,
) -> bool:
    """
    ingredient 기반 재계산 비용이 RAG 기준 비용보다 지나치게 큰 경우를 감지한다.

    특정 재료명에 의존하지 않고,
    메뉴 단위 비용 비율을 기준으로 이상치를 판단한다.
    """

    if rag_estimated_cost is None:
        return False

    if rag_estimated_cost <= 0:
        return False

    if calculated_cost <= 0:
        return False

    return calculated_cost > rag_estimated_cost * max_ratio


def build_invalid_ingredient_cost(
    ingredient_id: str | None,
    ingredient_name: str | None,
    display_amount: str | None,
    amount: float | int | None,
    unit: str | None,
    is_estimated: bool,
    pricing_status: str,
    standard_amount: float | int | None,
    standard_unit_type: str | None,
    lowest_price_info: dict,
) -> dict:
    """
    비정상 가격 후보를 ingredient_cost 형식으로 반환한다.
    estimated_cost는 합산되지 않도록 0으로 둔다.
    """

    return build_failed_ingredient_cost(
        ingredient_id=ingredient_id,
        ingredient_name=ingredient_name,
        display_amount=display_amount,
        amount=amount,
        unit=unit,
        is_estimated=is_estimated,
        pricing_status=pricing_status,
        extra_data={
            "standard_amount": standard_amount,
            "standard_unit_type": standard_unit_type,
            "lowest_price": lowest_price_info.get("lowest_price"),
            "lowest_market": lowest_price_info.get("market"),
            "delivery_type": lowest_price_info.get("delivery_type"),
            "product_title": lowest_price_info.get("product_title"),
            "purchase_link": lowest_price_info.get("purchase_link"),
        }
    )


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

    pool_ingredient_name = None
    if ingredient:
        pool_ingredient_name = ingredient.get("ingredient_name")

    resolved_ingredient_name = ingredient_name or pool_ingredient_name

    # if is_basic_pantry_ingredient(resolved_ingredient_name):
    #     return build_basic_pantry_ingredient_cost(
    #         ingredient_id=ingredient_id,
    #         ingredient_name=resolved_ingredient_name,
    #         display_amount=display_amount,
    #         amount=amount,
    #         unit=unit,
    #         is_estimated=is_estimated,
    #     )

    if not ingredient:
        return build_failed_ingredient_cost(
            ingredient_id=ingredient_id,
            ingredient_name=resolved_ingredient_name,
            display_amount=display_amount,
            amount=amount,
            unit=unit,
            is_estimated=is_estimated,
            pricing_status="ingredient_not_found"
        )

    ingredient_name = resolved_ingredient_name

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
        can_convert_water_unit = is_convertible_water_unit(
            ingredient_name=ingredient_name,
            usage_unit=unit,
            standard_unit_type=standard_unit_type
        )

        if not can_convert_water_unit:
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
                    "lowest_market": lowest_price_info["market"],
                    "delivery_type": lowest_price_info.get("delivery_type"),
                    "product_title": lowest_price_info.get("product_title"),
                    "purchase_link": lowest_price_info.get("purchase_link"),
                }
            )

    estimated_cost = lowest_price_info["lowest_price"] * (
        usage_amount / standard_amount
    )

    if is_invalid_product_match(
        product_title=lowest_price_info.get("product_title"),
    ):
        return build_invalid_ingredient_cost(
            ingredient_id=ingredient_id,
            ingredient_name=ingredient_name,
            display_amount=display_amount,
            amount=amount,
            unit=unit,
            is_estimated=is_estimated,
            pricing_status="invalid_product_match",
            standard_amount=standard_amount,
            standard_unit_type=standard_unit_type,
            lowest_price_info=lowest_price_info,
        )

    if is_price_outlier(
        estimated_cost=estimated_cost,
        standard_amount=standard_amount,
        standard_unit_type=standard_unit_type,
    ):
        return build_invalid_ingredient_cost(
            ingredient_id=ingredient_id,
            ingredient_name=ingredient_name,
            display_amount=display_amount,
            amount=amount,
            unit=unit,
            is_estimated=is_estimated,
            pricing_status="price_outlier",
            standard_amount=standard_amount,
            standard_unit_type=standard_unit_type,
            lowest_price_info=lowest_price_info,
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

    invalid_pricing_statuses = [
        "invalid_ingredient_name",
        "invalid_product_match",
        "price_outlier",
    ]

    has_invalid_price = any(
        status in invalid_pricing_statuses
        for status in pricing_statuses
    )

    rag_estimated_cost = candidate_menu.get("estimated_cost")

    if has_invalid_price and rag_estimated_cost:
        final_estimated_cost = rag_estimated_cost
        pricing_status = "fallback_to_rag_estimated_cost"
    elif is_cost_gap_outlier(
        calculated_cost=total_cost,
        rag_estimated_cost=rag_estimated_cost,
    ):
        final_estimated_cost = rag_estimated_cost
        pricing_status = "fallback_to_rag_estimated_cost_by_cost_gap"
    elif total_cost > 0:
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
    ingredient_groups, ingredient_group_mapping = fill_missing_ingredient_groups(
        candidate_menu
    )

    cost_result = calculate_menu_estimated_cost(
        candidate_menu=candidate_menu,
        ingredients_pool=ingredients_pool
    )

    difficulty_result = calculate_difficulty_from_recipe(
        candidate_menu=candidate_menu
    )

    nutrition_outlier_result = analyze_nutrition_outlier(candidate_menu)

    return {
        "menu_id": candidate_menu.get("menu_id"),
        "name": candidate_menu.get("name"),
        "category": candidate_menu.get("category"),
        "ingredient_groups": ingredient_groups,
        "ingredient_group_mapping": ingredient_group_mapping,
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
        "recipe": candidate_menu.get("recipe", {}),

        "nutrition_outlier_issues": nutrition_outlier_result[
            "nutrition_outlier_issues"
        ],
        "nutrition_outlier_penalty": nutrition_outlier_result[
            "nutrition_outlier_penalty"
        ],
        "is_extreme_nutrition_outlier": nutrition_outlier_result[
            "is_extreme_nutrition_outlier"
        ],
    }

def is_blank_string(value) -> bool:
    """
    값이 None이거나 빈 문자열인지 확인한다.
    """

    return value is None or str(value).strip() == ""


def is_invalid_ingredient_name(value) -> bool:
    """
    재료명이 실제 의미 있는 값인지 확인한다.

    RAG 응답에서 "-", "", "N/A"처럼 내려오는 값은
    실제 재료명으로 보기 어렵기 때문에 품질 이슈로 처리한다.
    """

    if is_blank_string(value):
        return True

    normalized_value = str(value).replace(" ", "").strip().lower()

    invalid_values = {
        "-",
        "없음",
        "없슴",
        "n/a",
        "na",
        "none",
        "null",
        "unknown",
    }

    return normalized_value in invalid_values


def is_empty_string_list(values) -> bool:
    """
    리스트가 비어 있거나, [""]처럼 빈 문자열만 들어 있는지 확인한다.
    """

    if not values:
        return True

    for value in values:
        if not is_invalid_ingredient_name(value):
            return False

    return True


def get_nutrient_value(menu: dict, key: str) -> float:
    """
    nutrient_summary 또는 menu 최상위 필드에서 영양 값을 가져온다.
    """

    nutrient_summary = menu.get("nutrient_summary") or {}

    value = (
        menu.get(key)
        if menu.get(key) is not None
        else nutrient_summary.get(key, 0)
    )

    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0



def analyze_nutrition_outlier(menu: dict) -> dict:
    """
    RAG 영양값이 1끼 기준으로 보기 어려운 이상치인지 진단한다.

    1차 구현에서는 후보를 바로 제외하지 않고,
    이상치 이슈와 penalty 후보 값만 기록한다.
    """

    calories = get_nutrient_value(menu, "calories")
    protein = get_nutrient_value(menu, "protein")
    carbohydrate = get_nutrient_value(menu, "carbohydrate")
    fat = get_nutrient_value(menu, "fat")

    issues = []
    penalty = 0
    is_extreme = False

    # 일반 이상치 기준
    if calories >= 2000:
        issues.append("calories_too_high")
        penalty += 15

    if protein >= 150:
        issues.append("protein_too_high")
        penalty += 15

    if carbohydrate >= 300:
        issues.append("carbohydrate_too_high")
        penalty += 10

    if fat >= 100:
        issues.append("fat_too_high")
        penalty += 15

    # 극단 이상치 기준
    if calories >= 5000:
        issues.append("calories_extreme")
        penalty += 50
        is_extreme = True

    if protein >= 300:
        issues.append("protein_extreme")
        penalty += 40
        is_extreme = True

    if carbohydrate >= 700:
        issues.append("carbohydrate_extreme")
        penalty += 40
        is_extreme = True

    if fat >= 250:
        issues.append("fat_extreme")
        penalty += 50
        is_extreme = True

    # 영양값 내부 정합성 기준
    #
    # calories는 RAG가 내려준 총 열량이고,
    # macro_calories는 탄수화물/단백질/지방으로부터 계산한 예상 열량이다.
    # 두 값은 반올림, 식이섬유, 조리 단위 차이 등으로 완전히 같을 필요는 없다.
    # 다만 macro_calories가 calories보다 지나치게 크면
    # RAG 영양값의 단위 또는 환산 오류 가능성이 높다.
    macro_calories = (carbohydrate * 4) + (protein * 4) + (fat * 9)

    if calories > 0 and macro_calories > 0:
        macro_calorie_ratio = macro_calories / calories

        if macro_calorie_ratio >= 1.5:
            issues.append("nutrient_calorie_mismatch")
            penalty += 20

        if macro_calorie_ratio >= 2.0:
            issues.append("nutrient_calorie_extreme_mismatch")
            penalty += 40
            is_extreme = True

        single_macro_calories = {
            "carbohydrate": carbohydrate * 4,
            "protein": protein * 4,
            "fat": fat * 9,
        }

        for nutrient_name, nutrient_calories in single_macro_calories.items():
            single_macro_ratio = nutrient_calories / calories

            if single_macro_ratio >= 1.25:
                issues.append(f"{nutrient_name}_calories_exceed_total")
                penalty += 25

            if single_macro_ratio >= 1.5:
                issues.append(f"{nutrient_name}_calories_extreme_exceed_total")
                penalty += 40
                is_extreme = True

    return {
        "nutrition_outlier_issues": issues,
        "nutrition_outlier_penalty": penalty,
        "is_extreme_nutrition_outlier": is_extreme,
    }


def validate_rag_candidate_menu(menu: dict) -> tuple[bool, list[str]]:
    """
    RAG 후보 메뉴가 모델링 추천에 사용할 수 있는지 검사한다.

    반환:
    - is_valid: 완전히 제외해야 하는지 여부
    - issues: 데이터 품질 이슈 목록

    기준:
    - menu_id, name이 없으면 구조적으로 무효한 후보로 제외한다.
    - calories, nutrient_summary, ingredients 등이 비어 있으면 품질 이슈로 기록한다.
    """

    issues = []

    menu_id = menu.get("menu_id")
    name = menu.get("name")

    if is_blank_string(menu_id):
        issues.append("menu_id_missing")

    if is_blank_string(name):
        issues.append("name_missing")

    # menu_id 또는 name이 없으면 추천 후보로 사용할 수 없으므로 제외한다.
    if "menu_id_missing" in issues or "name_missing" in issues:
        return False, issues

    calories = menu.get("calories", 0) or 0
    protein = get_nutrient_value(menu, "protein")
    carbohydrate = get_nutrient_value(menu, "carbohydrate")
    fat = get_nutrient_value(menu, "fat")

    try:
        calories = float(calories)
    except (TypeError, ValueError):
        calories = 0

    if calories <= 0:
        issues.append("calories_zero_or_missing")

    if protein <= 0:
        issues.append("protein_zero_or_missing")

    if carbohydrate <= 0 and protein <= 0 and fat <= 0:
        issues.append("nutrient_summary_empty")

    ingredients = menu.get("ingredients", [])
    ingredient_groups, ingredient_group_mapping = fill_missing_ingredient_groups(menu)
    ingredient_usages = menu.get("ingredient_usages", [])

    if is_empty_string_list(ingredients):
        issues.append("ingredients_empty")

    if not ingredient_groups:
        issues.append("ingredient_groups_empty")

    if ingredient_group_mapping.get("status") == "mapping_unavailable":
        issues.append("ingredient_groups_mapping_unavailable")

    valid_usage_count = 0
    invalid_usage_name_count = 0
    
    for usage in ingredient_usages:
        ingredient_name = usage.get("ingredient_name")
        ingredient_id = usage.get("ingredient_id")

        has_valid_name = not is_invalid_ingredient_name(ingredient_name)
        has_valid_id = not is_blank_string(ingredient_id)

        if has_valid_name:
            valid_usage_count += 1

        elif has_valid_id:
            invalid_usage_name_count += 1

    if valid_usage_count == 0:
        issues.append("ingredient_usages_empty_or_invalid")

    if invalid_usage_name_count > 0:
        issues.append("ingredient_usage_name_invalid")

    return True, issues


def calculate_rag_data_quality_score(issues: list[str]) -> int:
    """
    RAG 후보 메뉴의 데이터 품질 점수를 계산한다.

    100점에서 시작하여 이슈별로 감점한다.
    이 점수는 추후 모델링 점수 패널티에 활용할 수 있다.
    """

    penalty_map = {
        "calories_zero_or_missing": 20,
        "protein_zero_or_missing": 15,
        "nutrient_summary_empty": 25,
        "ingredients_empty": 20,
        "ingredient_groups_empty": 10,
        "ingredient_usages_empty_or_invalid": 20,
        "ingredient_usage_name_invalid": 15,
    }

    score = 100

    for issue in issues:
        score -= penalty_map.get(issue, 5)

    return max(score, 0)


def map_rag_response_to_candidate_menus(rag_response: dict) -> list[dict]:
    """
    RAG 응답을 Modeling 내부 candidate_menus 구조로 변환한다.

    RAG 응답 구조:
    {
        "response_format": "candidate_menus_v1",
        "candidate_menus": [...],
        "ingredients_pool": {...}
    }

    처리 흐름:
    1. candidate_menus 추출
    2. ingredients_pool 추출
    3. 구조적으로 무효한 후보 제외
    4. 데이터 품질 이슈 기록
    5. Modeling 내부 후보 메뉴 구조로 변환
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
    excluded_count = 0
    quality_issue_count = 0
    quality_issue_type_counter = Counter()
    ingredient_group_mapping_status_counter = Counter()
    quality_issue_examples: dict[str, list[dict]] = {}
    max_examples_per_issue = 5

    for menu in raw_menus:
        is_valid, issues = validate_rag_candidate_menu(menu)

        if not is_valid:
            excluded_count += 1
            continue

        mapped_menu = map_candidate_menu_to_modeling_menu(
            candidate_menu=menu,
            ingredients_pool=ingredients_pool,
        )

        data_quality_score = calculate_rag_data_quality_score(issues)

        mapped_menu["rag_data_quality_score"] = data_quality_score
        mapped_menu["rag_data_quality_issues"] = issues

        if issues:
            quality_issue_count += 1
            quality_issue_type_counter.update(issues)

            for issue in issues:
                quality_issue_examples.setdefault(issue, [])

                if len(quality_issue_examples[issue]) < max_examples_per_issue:
                    quality_issue_examples[issue].append(
                        build_quality_issue_example(
                            candidate_menu=menu,
                            issue_type=issue,
                        )
                    )

        candidate_menus.append(mapped_menu)

    for candidate_menu in candidate_menus:
        ingredient_group_mapping = (
            candidate_menu.get("ingredient_group_mapping") or {}
        )
        ingredient_group_mapping_status = ingredient_group_mapping.get(
            "status",
            "unknown",
        )
        ingredient_group_mapping_status_counter[
            ingredient_group_mapping_status
        ] += 1

    record_rag_mapping_diagnostics(
        raw_menus=len(raw_menus),
        mapped_menus=len(candidate_menus),
        excluded_menus=excluded_count,
        quality_issue_menus=quality_issue_count,
        quality_issue_type_count=dict(quality_issue_type_counter),
        quality_issue_examples=quality_issue_examples,
        ingredient_group_mapping_status_count=dict(
            ingredient_group_mapping_status_counter
        ),
    )

    logger.warning(
        "[RAG Mapper] raw_menus=%s, mapped_menus=%s, excluded_menus=%s, quality_issue_menus=%s",
        len(raw_menus),
        len(candidate_menus),
        excluded_count,
        quality_issue_count,
    )

    if not candidate_menus and raw_menus:
        logger.warning(
            "[RAG Mapper] 모든 RAG 후보가 제외되었습니다. RAG 응답 데이터 품질을 확인해야 합니다."
        )

    return candidate_menus
