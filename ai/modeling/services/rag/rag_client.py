import os

import requests


RAG_API_URL = os.getenv(
    "RAG_API_URL",
    "https://api.kkini.cloud/api/v1/meal-candidates",
)


class RagRequestError(RuntimeError):
    """
    RAG API 요청 실패를 모델링 파이프라인에서 구조적으로 구분하기 위한 예외이다.
    """

    def __init__(
        self,
        message: str,
        failure_reason: str,
        error_type: str,
        url: str,
        status_code: int | None = None,
        response_text: str | None = None,
    ):
        super().__init__(message)
        self.failure_stage = "rag_request"
        self.failure_reason = failure_reason
        self.error_type = error_type
        self.url = url
        self.status_code = status_code
        self.response_text = response_text

    def to_dict(self) -> dict:
        """
        실험 결과 JSON에 저장하기 쉬운 형태로 변환한다.
        """

        return {
            "failure_stage": self.failure_stage,
            "failure_reason": self.failure_reason,
            "type": self.error_type,
            "message": str(self),
            "url": self.url,
            "status_code": self.status_code,
            "response_text": self.response_text,
        }


def request_candidate_menus_from_rag(rag_request: dict) -> dict:
    """
    RAG 서버에 후보 메뉴를 요청한다.
    """

    try:
        response = requests.post(
            RAG_API_URL,
            json=rag_request,
            timeout=15,
        )
    except requests.exceptions.ReadTimeout as error:
        raise RagRequestError(
            message="RAG API 요청 시간이 초과되었습니다.",
            failure_reason="rag_read_timeout",
            error_type=type(error).__name__,
            url=RAG_API_URL,
        ) from error
    except requests.exceptions.Timeout as error:
        raise RagRequestError(
            message="RAG API 요청 제한 시간을 초과했습니다.",
            failure_reason="rag_timeout",
            error_type=type(error).__name__,
            url=RAG_API_URL,
        ) from error
    except requests.exceptions.ConnectionError as error:
        raise RagRequestError(
            message="RAG API에 연결하지 못했습니다.",
            failure_reason="rag_connection_error",
            error_type=type(error).__name__,
            url=RAG_API_URL,
        ) from error
    except requests.exceptions.RequestException as error:
        raise RagRequestError(
            message="RAG API 요청 중 오류가 발생했습니다.",
            failure_reason="rag_request_error",
            error_type=type(error).__name__,
            url=RAG_API_URL,
        ) from error

    if response.status_code >= 400:
        raise RagRequestError(
            message="RAG API 요청 실패",
            failure_reason="rag_http_error",
            error_type="HTTPError",
            url=RAG_API_URL,
            status_code=response.status_code,
            response_text=response.text,
        )

    return response.json()
