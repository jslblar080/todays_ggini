import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_STYLE_RESPONSE = (
    "modeling/experiments/fixtures/backend_style_candidates_response.json"
)
DEFAULT_MONTHLY_SUCCESS_RESPONSE = (
    "modeling/experiments/fixtures/backend_monthly_plan_success_response.json"
)
DEFAULT_MONTHLY_FAILURE_RESPONSE = (
    "modeling/experiments/fixtures/backend_monthly_plan_failure_response.json"
)

ALLOWED_FAILURE_REASONS = {
    "candidate_empty",
    "candidate_insufficient",
    "budget_infeasible",
    "optimizer_infeasible",
    "optimizer_unknown",
}


def read_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def require_fields(data: dict[str, Any], fields: list[str], label: str) -> None:
    missing_fields = [field for field in fields if field not in data]

    if missing_fields:
        raise ValueError(f"{label} 필수 필드가 누락되었습니다: {missing_fields}")


def validate_style_candidates_response(response_data: dict[str, Any]) -> None:
    require_fields(
        response_data,
        ["id", "request_type", "meta", "meal_style_candidates"],
        "style candidates response",
    )

    if response_data["request_type"] != "meal_style_candidates":
        raise ValueError("style candidates response request_type이 올바르지 않습니다.")

    meta = response_data["meta"]

    if not isinstance(meta, dict):
        raise ValueError("meta는 dict여야 합니다.")

    require_fields(meta, ["warnings"], "style candidates response meta")

    meal_style_candidates = response_data["meal_style_candidates"]

    if not isinstance(meal_style_candidates, list) or not meal_style_candidates:
        raise ValueError("meal_style_candidates는 비어 있지 않은 list여야 합니다.")

    required_candidate_fields = [
        "style_id",
        "style_name",
        "source_goal",
        "focus_key",
        "sample_plan",
    ]

    for index, candidate in enumerate(meal_style_candidates):
        if not isinstance(candidate, dict):
            raise ValueError(f"meal_style_candidates[{index}]는 dict여야 합니다.")

        require_fields(
            candidate,
            required_candidate_fields,
            f"meal_style_candidates[{index}]",
        )

        sample_plan = candidate["sample_plan"]

        if not isinstance(sample_plan, dict):
            raise ValueError(f"meal_style_candidates[{index}].sample_plan은 dict여야 합니다.")

        require_fields(
            sample_plan,
            ["period_days", "meal_count_per_day", "days"],
            f"meal_style_candidates[{index}].sample_plan",
        )

        days = sample_plan["days"]

        if not isinstance(days, list) or not days:
            raise ValueError(
                f"meal_style_candidates[{index}].sample_plan.days는 비어 있지 않은 list여야 합니다."
            )

def validate_monthly_success_response(response_data: dict[str, Any]) -> None:
    require_fields(
        response_data,
        [
            "id",
            "request_type",
            "success",
            "failure_reason",
            "selected_style",
            "meta",
            "modeling_profile",
            "applied_style_adjustment",
            "monthly_plan",
        ],
        "monthly success response",
    )

    if response_data["request_type"] != "monthly_plan":
        raise ValueError("monthly success response request_type이 올바르지 않습니다.")

    if response_data["success"] is not True:
        raise ValueError("success response의 success 값은 true여야 합니다.")

    if response_data["failure_reason"] is not None:
        raise ValueError(
            "success response의 failure_reason은 null이어야 합니다."
        )

    selected_style = response_data["selected_style"]

    if not isinstance(selected_style, dict):
        raise ValueError("selected_style은 dict여야 합니다.")

    require_fields(
        selected_style,
        ["style_id", "style_name", "source_goal", "focus_key"],
        "monthly success response selected_style",
    )

    meta = response_data["meta"]

    if not isinstance(meta, dict):
        raise ValueError("meta는 dict여야 합니다.")

    require_fields(
        meta,
        [
            "period_days",
            "meal_count_per_day",
            "required_meal_count",
            "available_recommendation_count",
            "warnings",
            "fallback",
        ],
        "monthly success response meta",
    )

    monthly_plan = response_data["monthly_plan"]

    if not isinstance(monthly_plan, dict):
        raise ValueError("monthly_plan은 dict여야 합니다.")

    require_fields(
        monthly_plan,
        [
            "period_days",
            "meal_count_per_day",
            "required_meal_count",
            "available_recommendation_count",
            "warnings",
            "optimizer",
        ],
        "monthly success response monthly_plan",
    )

    optimizer = monthly_plan["optimizer"]

    if not isinstance(optimizer, dict):
        raise ValueError("monthly_plan.optimizer는 dict여야 합니다.")

    require_fields(
        optimizer,
        ["enabled", "solver", "solver_status", "message", "config"],
        "monthly success response monthly_plan.optimizer",
    )

    require_fields(
        monthly_plan,
        ["days"],
        "monthly success response monthly_plan",
    )

    days = monthly_plan["days"]

    if not isinstance(days, list) or not days:
        raise ValueError("monthly_plan.days는 비어 있지 않은 list여야 합니다.")

    for day_index, day in enumerate(days):
        if not isinstance(day, dict):
            raise ValueError(f"monthly_plan.days[{day_index}]는 dict여야 합니다.")

        require_fields(
            day,
            ["day", "meals"],
            f"monthly_plan.days[{day_index}]",
        )

        meals = day["meals"]

        if not isinstance(meals, list) or not meals:
            raise ValueError(
                f"monthly_plan.days[{day_index}].meals는 비어 있지 않은 list여야 합니다."
            )

        for meal_index, meal in enumerate(meals):
            if not isinstance(meal, dict):
                raise ValueError(
                    f"monthly_plan.days[{day_index}].meals[{meal_index}]는 dict여야 합니다."
                )

            require_fields(
                meal,
                ["meal_order", "selected_menu"],
                f"monthly_plan.days[{day_index}].meals[{meal_index}]",
            )

            selected_menu = meal["selected_menu"]

            if not isinstance(selected_menu, dict):
                raise ValueError(
                    f"monthly_plan.days[{day_index}].meals[{meal_index}].selected_menu은 dict여야 합니다."
                )

            require_fields(
                selected_menu,
                ["menu_id", "name", "estimated_cost", "calories"],
                f"monthly_plan.days[{day_index}].meals[{meal_index}].selected_menu",
            )

            require_fields(
                selected_menu,
                ["ingredient_usages", "ingredient_costs", "pricing_status"],
                f"monthly_plan.days[{day_index}].meals[{meal_index}].selected_menu shopping fields",
            )

            ingredient_costs = selected_menu["ingredient_costs"]

            if not isinstance(ingredient_costs, list) or not ingredient_costs:
                raise ValueError(
                    f"monthly_plan.days[{day_index}].meals[{meal_index}].selected_menu.ingredient_costs는 비어 있지 않은 list여야 합니다."
                )

            for cost_index, ingredient_cost in enumerate(ingredient_costs):
                if not isinstance(ingredient_cost, dict):
                    raise ValueError(
                        f"monthly_plan.days[{day_index}].meals[{meal_index}].selected_menu.ingredient_costs[{cost_index}]는 dict여야 합니다."
                    )

                require_fields(
                    ingredient_cost,
                    [
                        "ingredient_id",
                        "ingredient_name",
                        "display_amount",
                        "estimated_cost",
                        "pricing_status",
                    ],
                    f"monthly_plan.days[{day_index}].meals[{meal_index}].selected_menu.ingredient_costs[{cost_index}]",
                )

def validate_monthly_failure_response(response_data: dict[str, Any]) -> None:
    require_fields(
        response_data,
        ["id", "request_type", "success", "failure_reason", "message"],
        "monthly failure response",
    )

    if response_data["request_type"] != "monthly_plan":
        raise ValueError("monthly failure response request_type이 올바르지 않습니다.")

    if response_data["success"] is not False:
        raise ValueError("failure response의 success 값은 false여야 합니다.")

    failure_reason = response_data["failure_reason"]

    if failure_reason not in ALLOWED_FAILURE_REASONS:
        raise ValueError(f"지원하지 않는 failure_reason입니다: {failure_reason}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Modeling → Backend response contract fixture를 검증한다."
    )
    parser.add_argument(
        "--style-response",
        default=DEFAULT_STYLE_RESPONSE,
        help="3일치 스타일 후보 생성 response fixture 경로",
    )
    parser.add_argument(
        "--monthly-success-response",
        default=DEFAULT_MONTHLY_SUCCESS_RESPONSE,
        help="월간 식단 생성 성공 response fixture 경로",
    )
    parser.add_argument(
        "--monthly-failure-response",
        default=DEFAULT_MONTHLY_FAILURE_RESPONSE,
        help="월간 식단 생성 실패 response fixture 경로",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    style_response = read_json(args.style_response)
    monthly_success_response = read_json(args.monthly_success_response)
    monthly_failure_response = read_json(args.monthly_failure_response)

    validate_style_candidates_response(style_response)
    validate_monthly_success_response(monthly_success_response)
    validate_monthly_failure_response(monthly_failure_response)

    print("[OK] backend style candidate response fixture is valid.")
    print("[OK] backend monthly plan success response fixture is valid.")
    print("[OK] backend monthly plan failure response fixture is valid.")


if __name__ == "__main__":
    main()
