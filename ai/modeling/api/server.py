import logging
import os
from typing import Any, Literal

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from services.modeling_service import (
    create_meal_style_candidates,
    create_monthly_plan,
)
from services.rag.rag_client import RagRequestError
from schemas.user_profile_schema import UserProfileRequest


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


class MealStyleCandidatesRequest(UserProfileRequest):
    """
    식단 스타일 후보 생성 요청 모델.

    기존 UserProfileRequest의 id, request_type, profile 검증을 재사용하고,
    request_type은 meal_style_candidates만 허용한다.
    """

    request_type: Literal["meal_style_candidates"]

    model_config = ConfigDict(extra="allow")


class SelectedStyleRequest(BaseModel):
    """
    월간 식단 생성 시 사용자가 선택한 식단 스타일 정보이다.
    """

    style_id: str
    style_name: str
    source_goal: str
    focus_key: str

    model_config = ConfigDict(extra="allow")


class MonthlyPlanRequest(UserProfileRequest):
    """
    월간 식단 생성 요청 모델.

    기존 UserProfileRequest의 id, request_type, profile 검증을 재사용하며,
    월간 식단 생성에 필요한 selected_style을 추가로 검증한다.
    """

    request_type: Literal["monthly_plan"]
    selected_style: SelectedStyleRequest
    use_ortools: bool = True
    optimizer_config: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


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

    failure_reason이 timeout 계열이면 504로 반환하고,
    그 외 RAG 외부 의존성 실패는 502로 반환한다.
    """

    timeout_failure_reasons = {
        "rag_read_timeout",
        "rag_timeout",
    }

    if error.failure_reason in timeout_failure_reasons:
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
