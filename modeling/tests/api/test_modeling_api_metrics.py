from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api import server
from api.metrics import (
    API_ERRORS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_IN_PROGRESS,
    HTTP_REQUESTS_TOTAL,
)
from services.rag.rag_client import RagRequestError


client = TestClient(server.app)


MONTHLY_FIXTURE_PATH = Path(
    "modeling/experiments/fixtures/"
    "backend_monthly_plan_request.json"
)


def read_valid_monthly_request() -> dict:
    """
    Endpoint 함수까지 진입할 수 있는 유효한 월간 식단 요청을 읽는다.
    """

    return json.loads(
        MONTHLY_FIXTURE_PATH.read_text(encoding="utf-8")
    )



@pytest.fixture(autouse=True)
def reset_metrics() -> None:
    """
    각 테스트가 이전 테스트의 Prometheus 시계열 값에 의존하지 않도록
    전용 Collector의 내부 상태를 초기화한다.
    """

    for metric in (
        HTTP_REQUESTS_TOTAL,
        HTTP_REQUEST_DURATION_SECONDS,
        HTTP_REQUESTS_IN_PROGRESS,
        API_ERRORS_TOTAL,
    ):
        metric.clear()



def test_metrics_requires_api_key_in_prod(monkeypatch) -> None:
    monkeypatch.setattr(server, "ENV", "prod")
    monkeypatch.setattr(server, "MODELING_API_KEY", "metrics-test-key")

    response = client.get("/metrics")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing API key.",
    }


def test_metrics_returns_prometheus_content(monkeypatch) -> None:
    monkeypatch.setattr(server, "ENV", "prod")
    monkeypatch.setattr(server, "MODELING_API_KEY", "metrics-test-key")

    response = client.get(
        "/metrics",
        headers={
            "X-API-Key": "metrics-test-key",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/plain"
    )

    assert "modeling_http_requests_total" in response.text
    assert "modeling_http_request_duration_seconds" in response.text
    assert "modeling_http_requests_in_progress" in response.text


def test_business_request_is_recorded_in_metrics(monkeypatch) -> None:
    monkeypatch.setattr(server, "ENV", "prod")
    monkeypatch.setattr(server, "MODELING_API_KEY", "metrics-test-key")

    response = client.post(
        "/monthly-plan",
        json={},
    )

    assert response.status_code == 422

    metrics_response = client.get(
        "/metrics",
        headers={
            "X-API-Key": "metrics-test-key",
        },
    )

    assert metrics_response.status_code == 200

    expected_labels = (
        'method="POST",path="/monthly-plan",status_code="422"'
    )

    assert expected_labels in metrics_response.text


def test_unknown_paths_use_bounded_label(monkeypatch) -> None:
    monkeypatch.setattr(server, "ENV", "prod")
    monkeypatch.setattr(server, "MODELING_API_KEY", "metrics-test-key")

    response = client.get("/arbitrary-user-controlled-path")

    assert response.status_code == 404

    metrics_response = client.get(
        "/metrics",
        headers={
            "X-API-Key": "metrics-test-key",
        },
    )

    assert metrics_response.status_code == 200
    assert 'path="/unmatched"' in metrics_response.text
    assert "/arbitrary-user-controlled-path" not in metrics_response.text


def test_health_and_metrics_requests_are_not_recorded(monkeypatch) -> None:
    monkeypatch.setattr(server, "ENV", "prod")
    monkeypatch.setattr(server, "MODELING_API_KEY", "metrics-test-key")

    health_response = client.get("/health")
    metrics_response = client.get(
        "/metrics",
        headers={
            "X-API-Key": "metrics-test-key",
        },
    )

    assert health_response.status_code == 200
    assert metrics_response.status_code == 200

    assert 'path="/health"' not in metrics_response.text
    assert 'path="/metrics"' not in metrics_response.text


def test_validation_error_is_recorded(monkeypatch) -> None:
    monkeypatch.setattr(server, "ENV", "prod")
    monkeypatch.setattr(server, "MODELING_API_KEY", "metrics-test-key")

    response = client.post(
        "/monthly-plan",
        json={},
    )

    assert response.status_code == 422

    metrics_response = client.get(
        "/metrics",
        headers={
            "X-API-Key": "metrics-test-key",
        },
    )

    assert metrics_response.status_code == 200

    assert (
        'modeling_api_errors_total{'
        'error_type="validation",'
        'path="/monthly-plan",'
        'status_code="422"} 1.0'
    ) in metrics_response.text


def test_authentication_error_is_recorded(monkeypatch) -> None:
    monkeypatch.setattr(server, "ENV", "prod")
    monkeypatch.setattr(server, "MODELING_API_KEY", "metrics-test-key")

    payload = read_valid_monthly_request()

    response = client.post(
        "/monthly-plan",
        json=payload,
        headers={
            "X-API-Key": "wrong-key",
        },
    )

    assert response.status_code == 401

    metrics_response = client.get(
        "/metrics",
        headers={
            "X-API-Key": "metrics-test-key",
        },
    )

    assert metrics_response.status_code == 200

    assert (
        'modeling_api_errors_total{'
        'error_type="authentication",'
        'path="/monthly-plan",'
        'status_code="401"} 1.0'
    ) in metrics_response.text


def test_rag_timeout_error_is_recorded(monkeypatch) -> None:
    monkeypatch.setattr(server, "ENV", "prod")
    monkeypatch.setattr(server, "MODELING_API_KEY", "metrics-test-key")

    def raise_rag_timeout(_: dict) -> dict:
        raise RagRequestError(
            message="RAG request timed out",
            failure_reason="rag_timeout",
            error_type="TimeoutError",
            url="https://example.com/rag",
        )

    monkeypatch.setattr(
        server,
        "create_monthly_plan",
        raise_rag_timeout,
    )

    response = client.post(
        "/monthly-plan",
        json=read_valid_monthly_request(),
        headers={
            "X-API-Key": "metrics-test-key",
        },
    )

    assert response.status_code == 504

    metrics_response = client.get(
        "/metrics",
        headers={
            "X-API-Key": "metrics-test-key",
        },
    )

    assert metrics_response.status_code == 200

    assert (
        'modeling_api_errors_total{'
        'error_type="rag_timeout",'
        'path="/monthly-plan",'
        'status_code="504"} 1.0'
    ) in metrics_response.text


def test_rag_upstream_error_is_recorded(monkeypatch) -> None:
    monkeypatch.setattr(server, "ENV", "prod")
    monkeypatch.setattr(server, "MODELING_API_KEY", "metrics-test-key")

    def raise_rag_connection_error(_: dict) -> dict:
        raise RagRequestError(
            message="RAG connection failed",
            failure_reason="rag_connection_error",
            error_type="ConnectionError",
            url="https://example.com/rag",
        )

    monkeypatch.setattr(
        server,
        "create_monthly_plan",
        raise_rag_connection_error,
    )

    response = client.post(
        "/monthly-plan",
        json=read_valid_monthly_request(),
        headers={
            "X-API-Key": "metrics-test-key",
        },
    )

    assert response.status_code == 502

    metrics_response = client.get(
        "/metrics",
        headers={
            "X-API-Key": "metrics-test-key",
        },
    )

    assert metrics_response.status_code == 200

    assert (
        'modeling_api_errors_total{'
        'error_type="rag_upstream",'
        'path="/monthly-plan",'
        'status_code="502"} 1.0'
    ) in metrics_response.text


def test_unexpected_error_is_recorded(monkeypatch) -> None:
    monkeypatch.setattr(server, "ENV", "prod")
    monkeypatch.setattr(server, "MODELING_API_KEY", "metrics-test-key")

    def raise_unexpected_error(_: dict) -> dict:
        raise RuntimeError("unexpected modeling failure")

    monkeypatch.setattr(
        server,
        "create_monthly_plan",
        raise_unexpected_error,
    )

    response = client.post(
        "/monthly-plan",
        json=read_valid_monthly_request(),
        headers={
            "X-API-Key": "metrics-test-key",
        },
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Internal server error.",
    }

    metrics_response = client.get(
        "/metrics",
        headers={
            "X-API-Key": "metrics-test-key",
        },
    )

    assert metrics_response.status_code == 200

    assert (
        'modeling_api_errors_total{'
        'error_type="unexpected",'
        'path="/monthly-plan",'
        'status_code="500"} 1.0'
    ) in metrics_response.text
