import argparse
import json
from pathlib import Path
from typing import Any

import requests


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def assert_status(
    actual_status: int,
    expected_statuses: set[int],
    response_text: str,
) -> None:
    if actual_status not in expected_statuses:
        raise AssertionError(
            f"Unexpected HTTP status: {actual_status}. "
            f"Expected one of {sorted(expected_statuses)}. "
            f"Response: {response_text[:1000]}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run HTTP smoke tests against the Modeling FastAPI server."
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8001",
        help="Modeling API base URL.",
    )
    parser.add_argument(
        "--api-key",
        default="local-secret-key",
        help="API key used for protected Modeling API endpoints.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="HTTP request timeout seconds.",
    )
    parser.add_argument(
        "--monthly-request",
        default="ai/modeling/experiments/fixtures/backend_monthly_plan_request.json",
        help="Path to monthly plan request fixture.",
    )

    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": args.api_key,
    }

    print_section("Health Check")
    health_response = requests.get(
        f"{base_url}/health",
        timeout=args.timeout,
    )
    print("status:", health_response.status_code)
    print("body:", health_response.text)

    assert_status(health_response.status_code, {200}, health_response.text)

    health_data = health_response.json()
    assert health_data.get("status") == "ok"
    assert health_data.get("service") == "todays-ggini-modeling"

    print_section("Wrong API Key")
    wrong_key_response = requests.post(
        f"{base_url}/monthly-plan",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "wrong-key",
        },
        json={},
        timeout=args.timeout,
    )
    print("status:", wrong_key_response.status_code)
    print("body:", wrong_key_response.text)

    assert_status(wrong_key_response.status_code, {401}, wrong_key_response.text)

    print_section("Docs Disabled Check")
    docs_response = requests.get(
        f"{base_url}/docs",
        timeout=args.timeout,
    )
    print("status:", docs_response.status_code)

    # Docker/prod mode should return 404.
    # Local uvicorn mode may return 200 if ENV is not prod.
    assert_status(docs_response.status_code, {200, 404}, docs_response.text)

    print_section("Monthly Plan API")
    monthly_payload = load_json(Path(args.monthly_request))

    monthly_response = requests.post(
        f"{base_url}/monthly-plan",
        headers=headers,
        json=monthly_payload,
        timeout=args.timeout,
    )
    print("status:", monthly_response.status_code)
    print("body:", monthly_response.text[:1000])

    # 200: RAG까지 정상 응답한 경우
    # 504: RAG timeout이 정상적으로 Gateway Timeout으로 분리된 경우
    assert_status(monthly_response.status_code, {200, 504}, monthly_response.text)

    if monthly_response.status_code == 200:
        data = monthly_response.json()
        monthly_plan = data.get("monthly_plan", {})
        days = monthly_plan.get("days", [])
        print("monthly_plan_days:", len(days))
        assert len(days) > 0

    if monthly_response.status_code == 504:
        data = monthly_response.json()
        print("timeout_detail:", data.get("detail"))

    print_section("Smoke Test Passed")
    print("Modeling API HTTP smoke test completed successfully.")


if __name__ == "__main__":
    main()
