import pytest
import httpx
from respx import MockRouter
from fastapi import HTTPException

from app.clients.modeling_api_client import ModelingApiClient
from app.api.meal import map_modeling_monthly_plan_response

# pytest-asyncio가 비동기 테스트 함수를 인식하도록 설정
pytestmark = pytest.mark.asyncio

@pytest.fixture
def client():
    return ModelingApiClient()


# 시나리오 1: 3일치 식단 스타일 후보군 조회 성공 검증 (Happy Path)
async def test_create_meal_style_candidates_success(respx_mock: MockRouter, client):
    # 외부 API 응답 모킹 세팅
    mock_url = f"{client.base_url}/meal-style-candidates"
    mock_response = {
        "success": True,
        "meal_style_candidates": [{"style_id": "high_protein", "style_name": "고단백식"}]
    }
    respx_mock.post(mock_url).mock(return_value=httpx.Response(200, json=mock_response))

    # 실행
    result = await client.create_meal_style_candidates({"test": "payload"})

    # 검증
    assert result["success"] is True
    assert len(result["meal_style_candidates"]) == 1
    assert result["meal_style_candidates"][0]["style_id"] == "high_protein"


# 시나리오 2: 401 인증 실패 시 백엔드가 500 내부 에러로 변환하는지 검증
async def test_monthly_plan_auth_failure(respx_mock: MockRouter, client):
    mock_url = f"{client.base_url}/monthly-plan"
    # 모델링 서버가 401을 반환하는 상황 시뮬레이션
    respx_mock.post(mock_url).mock(return_value=httpx.Response(401, text="Unauthorized"))

    # 실행 및 검증 (클라이언트 코드가 401 HTTPException을 던져야 함)
    with pytest.raises(HTTPException) as exc_info:
        await client.create_monthly_plan({"test": "payload"})
    
    assert exc_info.value.status_code == 500
    assert "인증 오류" in exc_info.value.detail


# 시나리오 3: 외부 API가 120초 타임아웃 지연을 발생시킬 때 방어 로직 검증
async def test_monthly_plan_timeout(respx_mock: MockRouter, client):
    mock_url = f"{client.base_url}/monthly-plan"
    # 외부 통신 중 타임아웃 예외가 발생하는 상황 시뮬레이션
    respx_mock.post(mock_url).mock(side_effect=httpx.TimeoutException("Read timeout"))

    with pytest.raises(HTTPException) as exc_info:
        await client.create_monthly_plan({"test": "payload"})
        
    assert exc_info.value.status_code == 504
    assert "시간이 너무 오래 걸려" in exc_info.value.detail or "응답 시간이 초과" in exc_info.value.detail


# 시나리오 4: Solver status가 UNKNOWN이지만 데이터가 있을 때 매퍼 유연성 검증
def test_extract_days_from_modeling_response_unknown_but_valid():
    # solver_status는 UNKNOWN이고 success는 false이지만 데이터가 살아있는 폴백 페이로드
    mock_ai_response = {
        "success": False,
        "solver_status": "UNKNOWN",
        "monthly_plan": {
            "days": [{"day": 1, "meals": []}, {"day": 2, "meals": []}]
        }
    }
    
    # 매퍼 함수 실행 (infeasible로 깨지지 않고 데이터를 끄집어내야 함)
    days_data = map_modeling_monthly_plan_response(mock_ai_response)
    
    # 검증
    assert len(days_data) == 2
    assert days_data[0]["day"] == 1