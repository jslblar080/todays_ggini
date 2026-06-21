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


def test_rag_read_timeout_maps_to_504() -> None:
    error = build_rag_error("rag_read_timeout")

    assert get_rag_error_status_code(error) == status.HTTP_504_GATEWAY_TIMEOUT


def test_rag_timeout_maps_to_504() -> None:
    error = build_rag_error("rag_timeout")

    assert get_rag_error_status_code(error) == status.HTTP_504_GATEWAY_TIMEOUT


def test_rag_connection_error_maps_to_502() -> None:
    error = build_rag_error("rag_connection_error")

    assert get_rag_error_status_code(error) == status.HTTP_502_BAD_GATEWAY


def test_rag_request_error_maps_to_502() -> None:
    error = build_rag_error("rag_request_error")

    assert get_rag_error_status_code(error) == status.HTTP_502_BAD_GATEWAY


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
