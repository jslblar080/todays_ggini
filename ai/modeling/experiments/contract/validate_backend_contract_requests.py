import argparse
import json
import sys
from pathlib import Path
from typing import Any

MODELING_ROOT = Path(__file__).resolve().parents[2]

if str(MODELING_ROOT) not in sys.path:
    sys.path.append(str(MODELING_ROOT))

from schemas.user_profile_schema import UserProfileRequest
from services.modeling_service import (
    create_meal_style_candidates,
    create_monthly_plan,
)


DEFAULT_STYLE_REQUEST = (
    "ai/modeling/experiments/fixtures/backend_style_candidates_request.json"
)
DEFAULT_MONTHLY_REQUEST = (
    "ai/modeling/experiments/fixtures/backend_monthly_plan_request.json"
)


def read_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def validate_style_request(request_data: dict[str, Any]) -> None:
    parsed = UserProfileRequest.model_validate(request_data)

    if parsed.request_type != "meal_style_candidates":
        raise ValueError(
            "style candidate request_type은 meal_style_candidates여야 합니다."
        )


def validate_monthly_request(request_data: dict[str, Any]) -> None:
    parsed = UserProfileRequest.model_validate(request_data)

    if parsed.request_type != "monthly_plan":
        raise ValueError("monthly plan request_type은 monthly_plan이어야 합니다.")

    selected_style = request_data.get("selected_style")

    if not isinstance(selected_style, dict) or not selected_style:
        raise ValueError("monthly plan 요청에는 selected_style이 필요합니다.")

    required_style_fields = [
        "style_id",
        "style_name",
        "source_goal",
        "focus_key",
    ]

    missing_fields = [
        field
        for field in required_style_fields
        if not selected_style.get(field)
    ]

    if missing_fields:
        raise ValueError(
            f"selected_style 필수 필드가 누락되었습니다: {missing_fields}"
        )


def validate_entrypoints() -> None:
    if not callable(create_meal_style_candidates):
        raise TypeError("create_meal_style_candidates를 호출할 수 없습니다.")

    if not callable(create_monthly_plan):
        raise TypeError("create_monthly_plan을 호출할 수 없습니다.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Backend → Modeling 연동 request fixture와 Modeling 진입점 계약을 검증한다."
        )
    )
    parser.add_argument(
        "--style-request",
        default=DEFAULT_STYLE_REQUEST,
        help="3일치 스타일 후보 생성 request fixture 경로",
    )
    parser.add_argument(
        "--monthly-request",
        default=DEFAULT_MONTHLY_REQUEST,
        help="월간 식단 생성 request fixture 경로",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    style_request = read_json(args.style_request)
    monthly_request = read_json(args.monthly_request)

    validate_style_request(style_request)
    validate_monthly_request(monthly_request)
    validate_entrypoints()

    print("[OK] backend style candidate request fixture is valid.")
    print("[OK] backend monthly plan request fixture is valid.")
    print("[OK] modeling service entrypoints are importable and callable.")


if __name__ == "__main__":
    main()
