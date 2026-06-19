import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_STYLE_RESPONSE = (
    "ai/modeling/experiments/fixtures/backend_style_candidates_response.json"
)
DEFAULT_MONTHLY_SUCCESS_RESPONSE = (
    "ai/modeling/experiments/fixtures/backend_monthly_plan_success_response.json"
)
DEFAULT_MONTHLY_FAILURE_RESPONSE = (
    "ai/modeling/experiments/fixtures/backend_monthly_plan_failure_response.json"
)

ALLOWED_FAILURE_REASONS = {
    "candidate_empty",
    "candidate_insufficient",
    "budget_infeasible",
    "optimizer_infeasible",
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
        ["user_id", "request_type", "style_candidates", "warnings"],
        "style candidates response",
    )

    if response_data["request_type"] != "meal_style_candidates":
        raise ValueError("style candidates response request_type이 올바르지 않습니다.")

    style_candidates = response_data["style_candidates"]

    if not isinstance(style_candidates, list) or not style_candidates:
        raise ValueError("style_candidates는 비어 있지 않은 list여야 합니다.")

    required_candidate_fields = [
        "style_id",
        "style_name",
        "source_goal",
        "focus_key",
    ]

    for index, candidate in enumerate(style_candidates):
        if not isinstance(candidate, dict):
            raise ValueError(f"style_candidates[{index}]는 dict여야 합니다.")

        require_fields(
            candidate,
            required_candidate_fields,
            f"style_candidates[{index}]",
        )


def validate_monthly_success_response(response_data: dict[str, Any]) -> None:
    require_fields(
        response_data,
        [
            "user_id",
            "request_type",
            "monthly_plan",
            "summary",
            "style_validation",
            "warnings",
            "fallback",
            "profiling",
        ],
        "monthly success response",
    )

    if response_data["request_type"] != "monthly_plan":
        raise ValueError("monthly success response request_type이 올바르지 않습니다.")

    monthly_plan = response_data["monthly_plan"]

    if not isinstance(monthly_plan, dict):
        raise ValueError("monthly_plan은 dict여야 합니다.")

    days = monthly_plan.get("days")

    if not isinstance(days, list) or not days:
        raise ValueError("monthly_plan.days는 비어 있지 않은 list여야 합니다.")

    for index, day in enumerate(days):
        if not isinstance(day, dict):
            raise ValueError(f"monthly_plan.days[{index}]는 dict여야 합니다.")

        require_fields(day, ["day", "meals"], f"monthly_plan.days[{index}]")

        meals = day["meals"]

        if not isinstance(meals, list) or not meals:
            raise ValueError(
                f"monthly_plan.days[{index}].meals는 비어 있지 않은 list여야 합니다."
            )


def validate_monthly_failure_response(response_data: dict[str, Any]) -> None:
    require_fields(
        response_data,
        ["user_id", "request_type", "success", "failure_reason", "message"],
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
