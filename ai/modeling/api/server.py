import logging
import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel

from services.modeling_service import (
    create_meal_style_candidates,
    create_monthly_plan,
)
from services.rag.rag_client import RagRequestError


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("todays_ggini.modeling_api")


ENV = os.getenv("ENV", "local")
MODELING_API_KEY = os.getenv("MODELING_API_KEY")


docs_url = None if ENV == "prod" else "/docs"
redoc_url = None if ENV == "prod" else "/redoc"
openapi_url = None if ENV == "prod" else "/openapi.json"


app = FastAPI(
    title="Todays Ggini Modeling Server",
    description="FastAPI server for Todays Ggini modeling service.",
    version="0.1.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
)


class MealStyleCandidatesRequest(BaseModel):
    """
    식단 스타일 후보 생성 요청 모델.

    현재는 Backend contract 호환성을 위해 extra field를 허용한다.
    추후 request contract가 더 고정되면 필수 필드를 명시한다.
    """

    class Config:
        extra = "allow"


class MonthlyPlanRequest(BaseModel):
    """
    월간 식단 생성 요청 모델.

    현재는 Backend contract 호환성을 위해 extra field를 허용한다.
    추후 user_id, budget, meal_count 등 필수 필드를 명시할 수 있다.
    """

    class Config:
        extra = "allow"


def model_to_payload(model: BaseModel) -> dict[str, Any]:
    """
    Pydantic v1/v2 양쪽에서 동작하도록 request model을 dict로 변환한다.
    """

    if hasattr(model, "model_dump"):
        return model.model_dump()

    return model.dict()


def verify_api_key(x_api_key: str | None) -> None:
    """
    Modeling API 호출용 API Key를 검증한다.

    local 환경에서는 MODELING_API_KEY가 설정되지 않은 경우 인증을 생략한다.
    prod 환경에서는 반드시 MODELING_API_KEY가 있어야 하고,
    요청 헤더의 X-API-Key 값과 일치해야 한다.
    """

    if ENV != "prod" and not MODELING_API_KEY:
        return

    if not MODELING_API_KEY:
        logger.error("MODELING_API_KEY is not configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error.",
        )

    if x_api_key != MODELING_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )


def build_error_detail(error: Exception, public_message: str) -> Any:
    """
    실행 환경에 따라 에러 응답 노출 수준을 조절한다.

    local 환경에서는 디버깅을 위해 타입과 메시지를 반환하고,
    prod 환경에서는 내부 구현 정보 노출을 줄인다.
    """

    if ENV == "prod":
        return public_message

    return {
        "type": type(error).__name__,
        "message": str(error),
    }


def get_rag_error_status_code(error: RagRequestError) -> int:
    """
    RAG 호출 실패를 HTTP 상태 코드로 변환한다.

    timeout 성격의 오류는 504로 반환하고,
    그 외 RAG 외부 의존성 실패는 502로 반환한다.
    """

    message = str(error).lower()

    if "timeout" in message or "시간이 초과" in message:
        return status.HTTP_504_GATEWAY_TIMEOUT

    return status.HTTP_502_BAD_GATEWAY


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    모델링 서버 상태 확인 API.

    prod 환경에서는 env 값을 반환하지 않아 내부 환경 정보 노출을 줄인다.
    """

    response = {
        "status": "ok",
        "service": "todays-ggini-modeling",
    }

    if ENV != "prod":
        response["env"] = ENV

    return response


@app.post("/meal-style-candidates")
def create_meal_style_candidates_endpoint(
    request_data: MealStyleCandidatesRequest,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict[str, Any]:
    """
    백엔드 1차 온보딩 입력을 받아 식단 스타일 후보를 생성한다.
    """

    verify_api_key(x_api_key)
    payload = model_to_payload(request_data)

    try:
        return create_meal_style_candidates(payload)
    except RagRequestError as error:
        logger.exception("RAG request failed while creating meal style candidates.")
        raise HTTPException(
            status_code=get_rag_error_status_code(error),
            detail=build_error_detail(error, "External recommendation service error."),
        ) from error
    except Exception as error:
        logger.exception("Unexpected error while creating meal style candidates.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=build_error_detail(error, "Internal server error."),
        ) from error


@app.post("/monthly-plan")
def create_monthly_plan_endpoint(
    request_data: MonthlyPlanRequest,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict[str, Any]:
    """
    백엔드 월간 식단 생성 요청을 받아 월간 식단을 생성한다.
    """

    verify_api_key(x_api_key)
    payload = model_to_payload(request_data)

    try:
        return create_monthly_plan(payload)
    except RagRequestError as error:
        logger.exception("RAG request failed while creating monthly plan.")
        raise HTTPException(
            status_code=get_rag_error_status_code(error),
            detail=build_error_detail(error, "External recommendation service error."),
        ) from error
    except Exception as error:
        logger.exception("Unexpected error while creating monthly plan.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=build_error_detail(error, "Internal server error."),
        ) from error
