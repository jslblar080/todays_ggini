import json
from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from api import server


MONTHLY_FIXTURE_PATH = Path(
    "modeling/experiments/fixtures/"
    "backend_monthly_plan_request.json"
)

STYLE_FIXTURE_PATH = Path(
    "modeling/experiments/fixtures/"
    "backend_style_candidates_request.json"
)

client = TestClient(server.app)

TEST_API_KEY = "ci-secret-key"
AUTH_HEADERS = {
    "X-API-Key": TEST_API_KEY,
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_valid_monthly_request() -> dict:
    return read_json(MONTHLY_FIXTURE_PATH)


def read_valid_style_request() -> dict:
    return read_json(STYLE_FIXTURE_PATH)


def assert_monthly_validation_error(payload: dict) -> None:
    response = client.post(
        "/monthly-plan",
        json=payload,
    )

    assert response.status_code == 422, (
        f"expected HTTP 422, got {response.status_code}: {response.text}"
    )


def assert_style_validation_error(payload: dict) -> None:
    response = client.post(
        "/meal-style-candidates",
        json=payload,
    )

    assert response.status_code == 422, (
        f"expected HTTP 422, got {response.status_code}: {response.text}"
    )


def test_empty_monthly_request_returns_422() -> None:
    assert_monthly_validation_error({})


def test_monthly_request_without_id_returns_422() -> None:
    payload = read_valid_monthly_request()
    payload.pop("id")

    assert_monthly_validation_error(payload)


def test_monthly_request_with_invalid_request_type_returns_422() -> None:
    payload = read_valid_monthly_request()
    payload["request_type"] = "meal_style_candidates"

    assert_monthly_validation_error(payload)


def test_monthly_request_without_profile_returns_422() -> None:
    payload = read_valid_monthly_request()
    payload.pop("profile")

    assert_monthly_validation_error(payload)


def test_monthly_request_without_selected_style_returns_422() -> None:
    payload = read_valid_monthly_request()
    payload.pop("selected_style")

    assert_monthly_validation_error(payload)


def test_monthly_request_with_incomplete_selected_style_returns_422() -> None:
    payload = read_valid_monthly_request()
    payload["selected_style"].pop("style_id")

    assert_monthly_validation_error(payload)


def test_monthly_request_with_invalid_profile_returns_422() -> None:
    payload = read_valid_monthly_request()
    payload["profile"]["monthly_budget"] = 0

    assert_monthly_validation_error(payload)


def test_valid_monthly_request_reaches_service(monkeypatch) -> None:
    payload = read_valid_monthly_request()
    captured_payload: dict = {}

    def fake_create_monthly_plan(request_data: dict) -> dict:
        captured_payload.update(deepcopy(request_data))

        return {
            "id": request_data["id"],
            "request_type": "monthly_plan",
            "success": True,
        }

    monkeypatch.setattr(
        server,
        "create_monthly_plan",
        fake_create_monthly_plan,
    )

    response = client.post(
        "/monthly-plan",
        json=payload,
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200, response.text
    assert response.json()["success"] is True
    assert captured_payload["id"] == payload["id"]
    assert captured_payload["request_type"] == "monthly_plan"
    assert captured_payload["selected_style"] == payload["selected_style"]


def test_empty_style_request_returns_422() -> None:
    assert_style_validation_error({})


def test_style_request_with_invalid_request_type_returns_422() -> None:
    payload = read_valid_style_request()
    payload["request_type"] = "monthly_plan"

    assert_style_validation_error(payload)


def test_valid_style_request_reaches_service(monkeypatch) -> None:
    payload = read_valid_style_request()
    captured_payload: dict = {}

    def fake_create_meal_style_candidates(request_data: dict) -> dict:
        captured_payload.update(deepcopy(request_data))

        return {
            "id": request_data["id"],
            "request_type": "meal_style_candidates",
            "meal_style_candidates": [],
        }

    monkeypatch.setattr(
        server,
        "create_meal_style_candidates",
        fake_create_meal_style_candidates,
    )

    response = client.post(
        "/meal-style-candidates",
        json=payload,
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200, response.text
    assert captured_payload["id"] == payload["id"]
    assert captured_payload["request_type"] == "meal_style_candidates"


def test_valid_monthly_request_without_api_key_returns_401() -> None:
    payload = read_valid_monthly_request()

    response = client.post(
        "/monthly-plan",
        json=payload,
    )

    assert response.status_code == 401, (
        f"expected HTTP 401, got {response.status_code}: {response.text}"
    )
