from __future__ import annotations

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)


METRICS_REGISTRY = CollectorRegistry()

HTTP_REQUESTS_TOTAL = Counter(
    "modeling_http_requests_total",
    "Total number of HTTP requests handled by the modeling API.",
    labelnames=("method", "path", "status_code"),
    registry=METRICS_REGISTRY,
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "modeling_http_request_duration_seconds",
    "HTTP request processing duration in seconds.",
    labelnames=("method", "path"),
    buckets=(
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
        60.0,
    ),
    registry=METRICS_REGISTRY,
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "modeling_http_requests_in_progress",
    "Current number of HTTP requests being processed.",
    labelnames=("method", "path"),
    registry=METRICS_REGISTRY,
)


API_ERRORS_TOTAL = Counter(
    "modeling_api_errors_total",
    "Total number of modeling API errors by semantic error type.",
    labelnames=("path", "error_type", "status_code"),
    registry=METRICS_REGISTRY,
)


MONITORED_PATHS = {
    "/meal-style-candidates",
    "/monthly-plan",
}

EXCLUDED_PATHS = {
    "/health",
    "/metrics",
}


def normalize_metrics_path(path: str) -> str | None:
    """
    요청 경로를 제한된 Prometheus label 값으로 변환한다.

    health와 metrics 요청은 비즈니스 트래픽 통계를 왜곡하므로 제외한다.
    등록되지 않은 경로는 원문을 사용하지 않고 /unmatched로 합쳐
    임의 경로 요청에 의한 label cardinality 증가를 방지한다.
    """

    if path in EXCLUDED_PATHS:
        return None

    if path in MONITORED_PATHS:
        return path

    return "/unmatched"


def record_api_error(
    path: str,
    error_type: str,
    status_code: int,
) -> None:
    """
    제한된 오류 유형과 상태 코드를 Prometheus Counter에 기록한다.

    실제 예외 메시지나 사용자 식별자는 label로 사용하지 않아
    시계열 수 증가와 내부 정보 노출을 방지한다.
    """

    API_ERRORS_TOTAL.labels(
        path=path,
        error_type=error_type,
        status_code=str(status_code),
    ).inc()


def render_metrics() -> bytes:
    """
    현재 모델링 API 지표를 Prometheus text exposition 형식으로 반환한다.
    """

    return generate_latest(METRICS_REGISTRY)
