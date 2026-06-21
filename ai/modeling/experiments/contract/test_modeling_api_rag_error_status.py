from fastapi import status

from api.server import get_rag_error_status_code
from services.rag.rag_client import RagRequestError


def build_rag_error(failure_reason: str) -> RagRequestError:
    return RagRequestError(
        message="RAG API test error",
        failure_reason=failure_reason,
        error_type="TestError",
        url="https://example.com/rag",
    )


def assert_rag_error_status(
    failure_reason: str,
    expected_status: int,
) -> None:
    error = build_rag_error(failure_reason)
    actual_status = get_rag_error_status_code(error)

    assert actual_status == expected_status, (
        f"{failure_reason} expected {expected_status}, got {actual_status}"
    )


def test_rag_read_timeout_maps_to_504() -> None:
    assert_rag_error_status(
        "rag_read_timeout",
        status.HTTP_504_GATEWAY_TIMEOUT,
    )


def test_rag_timeout_maps_to_504() -> None:
    assert_rag_error_status(
        "rag_timeout",
        status.HTTP_504_GATEWAY_TIMEOUT,
    )


def test_rag_connection_error_maps_to_502() -> None:
    assert_rag_error_status(
        "rag_connection_error",
        status.HTTP_502_BAD_GATEWAY,
    )


def test_rag_request_error_maps_to_502() -> None:
    assert_rag_error_status(
        "rag_request_error",
        status.HTTP_502_BAD_GATEWAY,
    )


def test_rag_http_error_maps_to_502() -> None:
    error = RagRequestError(
        message="RAG API request failed",
        failure_reason="rag_http_error",
        error_type="HTTPError",
        url="https://example.com/rag",
        status_code=500,
        response_text="server error",
    )

    assert get_rag_error_status_code(error) == status.HTTP_502_BAD_GATEWAY


def main() -> None:
    cases = [
        ("rag_read_timeout", status.HTTP_504_GATEWAY_TIMEOUT),
        ("rag_timeout", status.HTTP_504_GATEWAY_TIMEOUT),
        ("rag_connection_error", status.HTTP_502_BAD_GATEWAY),
        ("rag_request_error", status.HTTP_502_BAD_GATEWAY),
        ("rag_http_error", status.HTTP_502_BAD_GATEWAY),
    ]

    for failure_reason, expected_status in cases:
        assert_rag_error_status(failure_reason, expected_status)
        print(f"{failure_reason}: {expected_status}")

    print("RAG error status mapping check passed.")


if __name__ == "__main__":
    main()
