import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]
MODELING_ROOT = PROJECT_ROOT / "ai" / "modeling"

if str(MODELING_ROOT) not in sys.path:
    sys.path.append(str(MODELING_ROOT))

from services.modeling_service import (
    create_meal_style_candidates,
    create_monthly_plan,
)
from validate_backend_contract_responses import (
    validate_monthly_failure_response,
    validate_monthly_success_response,
    validate_style_candidates_response,
)


STYLE_REQUEST_FIXTURE = (
    PROJECT_ROOT
    / "ai"
    / "modeling"
    / "experiments"
    / "fixtures"
    / "backend_style_candidates_request.json"
)

MONTHLY_REQUEST_FIXTURE = (
    PROJECT_ROOT
    / "ai"
    / "modeling"
    / "experiments"
    / "fixtures"
    / "backend_monthly_plan_request.json"
)


def read_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def validate_monthly_response(response_data: dict[str, Any]) -> None:
    if response_data.get("success") is False or "failure_reason" in response_data:
        validate_monthly_failure_response(response_data)
        return

    validate_monthly_success_response(response_data)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Modeling service 진입 함수를 실제 호출해 Backend contract와 맞는지 확인한다."
    )
    parser.add_argument(
        "--run-service",
        action="store_true",
        help="실제 Modeling service 함수를 호출한다. RAG 호출이 발생할 수 있다.",
    )
    parser.add_argument(
        "--style-request",
        default=str(STYLE_REQUEST_FIXTURE),
        help="style candidate request fixture 경로",
    )
    parser.add_argument(
        "--monthly-request",
        default=str(MONTHLY_REQUEST_FIXTURE),
        help="monthly plan request fixture 경로",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.run_service:
        print("[SKIP] service smoke test was not executed.")
        print("[INFO] 실제 Modeling service 호출은 RAG 비용/시간이 발생할 수 있습니다.")
        print("[INFO] 실행하려면 --run-service 옵션을 추가하세요.")
        return

    style_request = read_json(Path(args.style_request))
    monthly_request = read_json(Path(args.monthly_request))

    print("[RUN] create_meal_style_candidates")
    style_response = create_meal_style_candidates(style_request)
    validate_style_candidates_response(style_response)
    print("[OK] create_meal_style_candidates response matches backend contract.")

    print("[RUN] create_monthly_plan")
    monthly_response = create_monthly_plan(monthly_request)
    validate_monthly_response(monthly_response)
    print("[OK] create_monthly_plan response matches backend contract.")


if __name__ == "__main__":
    main()
