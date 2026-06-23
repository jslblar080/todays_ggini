import json
from collections import Counter
from pathlib import Path

from services.modeling_service import create_monthly_plan


REQUEST_FIXTURE_PATH = Path(
    "modeling/experiments/fixtures/backend_monthly_plan_request.json"
)


def load_request_fixture() -> dict:
    with open(REQUEST_FIXTURE_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def analyze_monthly_plan_shopping_coverage(response: dict) -> dict:
    days = response.get("monthly_plan", {}).get("days", [])

    total_days = len(days)
    total_meals = 0
    menus_with_ingredient_usages = 0
    menus_with_ingredient_costs = 0

    menu_pricing_status_count = Counter()
    ingredient_pricing_status_count = Counter()
    issue_unit_count = Counter()
    issue_ingredient_name_count = Counter()
    issue_status_unit_count = Counter()
    issue_status_ingredient_count = Counter()
    issue_status_standard_unit_count = Counter()
    issue_unit_standard_unit_count = Counter()
    issue_status_market_count = Counter()
    price_not_found_market_count = Counter()

    total_ingredient_costs = 0
    calculated_ingredient_costs = 0
    priced_ingredient_costs = 0

    empty_cost_examples = []
    issue_examples = []

    for day in days:
        for meal in day.get("meals", []):
            total_meals += 1

            selected_menu = meal.get("selected_menu", {}) or {}
            ingredient_usages = selected_menu.get("ingredient_usages") or []
            ingredient_costs = selected_menu.get("ingredient_costs") or []
            menu_pricing_status = selected_menu.get("pricing_status")

            menu_pricing_status_count[menu_pricing_status] += 1

            if ingredient_usages:
                menus_with_ingredient_usages += 1

            if ingredient_costs:
                menus_with_ingredient_costs += 1
            elif len(empty_cost_examples) < 5:
                empty_cost_examples.append(
                    {
                        "day": day.get("day"),
                        "meal_order": meal.get("meal_order"),
                        "menu_id": selected_menu.get("menu_id"),
                        "name": selected_menu.get("name"),
                        "ingredients_count": len(selected_menu.get("ingredients") or []),
                        "ingredient_usages_count": len(ingredient_usages),
                        "pricing_status": menu_pricing_status,
                    }
                )

            for ingredient_cost in ingredient_costs:
                total_ingredient_costs += 1

                ingredient_status = ingredient_cost.get("pricing_status")
                ingredient_pricing_status_count[ingredient_status] += 1

                if ingredient_status == "calculated":
                    calculated_ingredient_costs += 1

                if ingredient_cost.get("lowest_price") is not None:
                    priced_ingredient_costs += 1

                if ingredient_status != "calculated":
                    unit = ingredient_cost.get("unit")
                    ingredient_name = ingredient_cost.get("ingredient_name")

                    standard_unit_type = ingredient_cost.get("standard_unit_type")
                    e_commerce_market_count = ingredient_cost.get(
                        "e_commerce_market_count"
                    )

                    issue_unit_count[unit] += 1
                    issue_ingredient_name_count[ingredient_name] += 1
                    issue_status_unit_count[(ingredient_status, unit)] += 1
                    issue_status_ingredient_count[(ingredient_status, ingredient_name)] += 1
                    issue_status_standard_unit_count[
                        (ingredient_status, standard_unit_type)
                    ] += 1
                    issue_unit_standard_unit_count[
                        (unit, standard_unit_type)
                    ] += 1
                    issue_status_market_count[
                        (ingredient_status, e_commerce_market_count)
                    ] += 1

                    if ingredient_status == "price_not_found":
                        price_not_found_market_count[e_commerce_market_count] += 1

                    if len(issue_examples) < 10:
                        issue_examples.append(
                            {
                                "day": day.get("day"),
                                "meal_order": meal.get("meal_order"),
                                "menu_id": selected_menu.get("menu_id"),
                                "menu_name": selected_menu.get("name"),
                                "ingredient_id": ingredient_cost.get("ingredient_id"),
                                "ingredient_name": ingredient_name,
                                "display_amount": ingredient_cost.get("display_amount"),
                                "unit": unit,
                                "standard_amount": ingredient_cost.get("standard_amount"),
                                "standard_unit_type": standard_unit_type,
                                "e_commerce_market_count": e_commerce_market_count,
                                "e_commerce_markets": ingredient_cost.get("e_commerce_markets"),
                                "pricing_status": ingredient_status,
                                "lowest_price": ingredient_cost.get("lowest_price"),
                                "lowest_market": ingredient_cost.get("lowest_market"),
                                "product_title": ingredient_cost.get("product_title"),
                            }
                        )

    return {
        "total_days": total_days,
        "total_meals": total_meals,
        "menus_with_ingredient_usages": menus_with_ingredient_usages,
        "menus_with_ingredient_costs": menus_with_ingredient_costs,
        "menu_ingredient_usages_coverage": round(
            menus_with_ingredient_usages / total_meals, 4
        )
        if total_meals
        else 0,
        "menu_ingredient_costs_coverage": round(
            menus_with_ingredient_costs / total_meals, 4
        )
        if total_meals
        else 0,
        "total_ingredient_costs": total_ingredient_costs,
        "calculated_ingredient_costs": calculated_ingredient_costs,
        "priced_ingredient_costs": priced_ingredient_costs,
        "calculated_ingredient_cost_rate": round(
            calculated_ingredient_costs / total_ingredient_costs, 4
        )
        if total_ingredient_costs
        else 0,
        "priced_ingredient_cost_rate": round(
            priced_ingredient_costs / total_ingredient_costs, 4
        )
        if total_ingredient_costs
        else 0,
        "menu_pricing_status_count": dict(menu_pricing_status_count),
        "ingredient_pricing_status_count": dict(ingredient_pricing_status_count),
        "top_issue_units": [
            {"unit": unit, "count": count}
            for unit, count in issue_unit_count.most_common(20)
        ],
        "top_issue_ingredient_names": [
            {"ingredient_name": name, "count": count}
            for name, count in issue_ingredient_name_count.most_common(20)
        ],
        "top_issue_status_units": [
            {
                "pricing_status": status,
                "unit": unit,
                "count": count,
            }
            for (status, unit), count in issue_status_unit_count.most_common(20)
        ],
        "top_issue_status_ingredients": [
            {
                "pricing_status": status,
                "ingredient_name": name,
                "count": count,
            }
            for (status, name), count in issue_status_ingredient_count.most_common(20)
        ],
        "top_issue_status_standard_units": [
            {
                "pricing_status": status,
                "standard_unit_type": standard_unit_type,
                "count": count,
            }
            for (status, standard_unit_type), count
            in issue_status_standard_unit_count.most_common(20)
        ],
        "top_issue_unit_standard_units": [
            {
                "unit": unit,
                "standard_unit_type": standard_unit_type,
                "count": count,
            }
            for (unit, standard_unit_type), count
            in issue_unit_standard_unit_count.most_common(20)
        ],
        "top_issue_status_market_counts": [
            {
                "pricing_status": status,
                "e_commerce_market_count": market_count,
                "count": count,
            }
            for (status, market_count), count
            in issue_status_market_count.most_common(20)
        ],
        "price_not_found_market_count": dict(price_not_found_market_count),
        "empty_cost_examples": empty_cost_examples,
        "issue_examples": issue_examples,
    }


def main() -> None:
    request_data = load_request_fixture()
    response = create_monthly_plan(request_data)
    report = analyze_monthly_plan_shopping_coverage(response)

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
