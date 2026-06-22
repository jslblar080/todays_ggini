import logging
import time
import httpx
import sys
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)
# Uvicorn의 콘솔 출력 흐름과 강제 동기화 및 INFO 레벨 활성화
logger.setLevel(logging.INFO)

# 이미 핸들러가 등록되어 있다면 중복 방지를 위해 초기화
if logger.hasHandlers():
    logger.handlers.clear()

# 표준 출력(터미널 화면)으로 로그를 쏴주는 스트림 핸들러 생성
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)

# 보기 편하게 한글 규격 커스텀 포매터 장착 (시간 | 레벨 | 메시지)
formatter = logging.Formatter(
    fmt="[%(asctime)s] %(levelname)s [%(name)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# ❌ Uvicorn의 상위 로거 필터에 막혀 증발하지 않도록 상위 전파 허용
logger.propagate = True

class ModelingApiClient:
    def __init__(self):
        self.base_url = settings.MODELING_API_BASE_URL
        self.api_key = settings.MODELING_API_KEY
        
        # Connection Timeout 10초, Read Timeout 120초 적용
        self.timeout = httpx.Timeout(
            connect=float(settings.MODELING_API_CONNECT_TIMEOUT_SECONDS),
            read=float(settings.MODELING_API_READ_TIMEOUT_SECONDS),
            write=30.0,
            pool=10.0
        )
        
        # 헤더 설정
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }

    async def health_check(self) -> bool:
        """
        모델링 서버의 연결 상태 및 API Key 인증을 검증합니다.
        Endpoint: GET /health
        """
        url = f"{self.base_url}/health"
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers)

            elapsed_ms = int((time.time() - start_time) * 1000)
            response_size = len(response.content)
            
            
            # 200 OK 일 때만 성공
            if response.status_code == 200:
                logger.info(
                    f"[Modeling API SUCCESS] Endpoint: /health | "
                    f"HTTP Status: {response.status_code} | "
                    f"Elapsed: {elapsed_ms}ms | Size: {response_size} bytes"
                )
                return True
                
            # API Key 오류 등으로 401 등이 반환될 때
            logger.error(
                f"Modeling API Health Check failed | "
                f"HTTP Status: {response.status_code} | "
                f"Elapsed: {elapsed_ms}ms | Size: {response_size} bytes"
            )
            return False
            
        except httpx.RequestError as exc:
            # 타임아웃이나 네트워크 차단으로 연결 실패 시
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Modeling API Health Check failed to connect | "
                f"Elapsed: {elapsed_ms}ms | Reason: {exc}"
            )
            return False
        
    async def create_meal_style_candidates(self, payload: dict) -> dict:
        """
        사용자의 신체 정보 및 선호도를 기반으로 식단 스타일 후보군을 가져옵니다.
        """
        url = f"{self.base_url}/meal-style-candidates"
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=self.headers, json=payload)
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            response_size = len(response.content)
            
            if response.status_code == 200:
                response_data = response.json()
                candidates_count = len(response_data.get("meal_style_candidates", []))
                
                # 핵심 메타데이터 요약 로그 추가
                logger.info(
                    f"[Modeling API SUCCESS] Endpoint: /meal-style-candidates | "
                    f"HTTP Status: {response.status_code} | "
                    f"Elapsed: {elapsed_ms}ms | Size: {response_size} bytes | "
                    f"Candidates Count: {candidates_count} styles"
                )
                return response_data
                
            elif response.status_code == 401:
                logger.error("Modeling API Error [401]: Invalid API Key.")
                raise HTTPException(status_code=status.status.HTTP_401_UNAUTHORIZED, detail="인증 오류로 인해 식단 스타일을 가져올 수 없습니다.")
            elif response.status_code == 422:
                logger.error(f"Modeling API Error [422]: Invalid Payload. Keys: {list(payload.keys())}")
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="요청 데이터 규격이 맞지 않습니다.")
            else:
                logger.error(f"Modeling API Unexpected Error [{response.status_code}]: {response.text[:200]}")
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="모델링 서버 응답 오류가 발생했습니다.")
                
        except httpx.TimeoutException:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="모델링 서버 응답 시간이 초과되었습니다.")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="모델링 서버와 통신할 수 없습니다.")

    async def create_monthly_plan(self, payload: dict) -> dict:
        """
        최종 선택된 식단 스타일을 바탕으로 한 달 치(30일) 식단을 생성합니다.
        """
        url = f"{self.base_url}/monthly-plan"
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # 메타데이터 추출
                response_size = len(response.content)
                solver_status = response_data.get("solver_status", "UNKNOWN")
                failure_reason = response_data.get("failure_reason")
                is_success = response_data.get("success", True)

                monthly_plan_layer = response_data.get("monthly_plan", {})
                days_count = len(monthly_plan_layer.get("days", []))

                summary_layer = monthly_plan_layer.get("summary", {})
                selected_menu_count = (
                    summary_layer.get("selected_menu_count")  # 1순위: monthly_plan.summary 내부
                    or response_data.get("selected_menu_count")  # 2순위: 최상위 루트 피드
                    or (days_count * response_data.get("meta", {}).get("meal_count_per_day", 3))  # 3순위: 연산 추정 폴백
                    or 0
                )

                logger.info(
                    f"[모델링 API 연동 성공] Endpoint: /monthly-plan | "
                    f"HTTP Status: {response.status_code} | "
                    f"소요 시간: {elapsed_ms}ms | 패킷 Size: {response_size} bytes | "
                    f"Solver Status: {solver_status} | 생성 일수: {days_count} days | "
                    f"확정 메뉴 수: {selected_menu_count} | "
                    f"Failure Reason: {failure_reason}"
                )
                
                if not is_success or failure_reason:
                    # 예외 조건: solver_status가 UNKNOWN이면서 동시에 억지로라도 뽑힌 식단 데이터가 존재하는 경우에만 폴백 허용
                    if solver_status == "UNKNOWN" and days_count > 0:
                        logger.warning(
                            f"[모델링 API 경고] solver status는 UNKNOWN이나 식단 데이터({days_count}일치)가 확인되어 "
                            f"비즈니스 실패 처리를 유예하고 데이터 Fallback 흐름을 적용합니다."
                        )
                        return response_data
                    
                    # 그 외의 모든 success: false 또는 failure_reason 명시 상황은 "순수 비즈니스 모델링 실패"로 정의
                    error_msg = failure_reason or f"모델링 제약 조건 충족 실패 (Solver: {solver_status})"
                    logger.warning(f"[모델링 비즈니스 실패 캐치] HTTP 상태는 200이지만 AI 연산 실패 원인: {error_msg}")
                    
                    # 프론트엔드 및 Celery 태스크가 인지하도록 명확한 400 Bad Request 에러로 치환하여 토스
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"모델링 비즈니스 연산 실패: {error_msg}"
                    )
                
                return response_data
                
            elif response.status_code == 401:
                logger.error("Modeling API Error [401]: Invalid API Key.")
                raise HTTPException(status_code=status.status.HTTP_401_UNAUTHORIZED, detail="인증 오류로 인해 식단을 생성할 수 없습니다.")
            elif response.status_code == 422:
                logger.error(f"Modeling API Error [422]: Invalid Payload sent to modeling /monthly-plan.")
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="식단 생성 요청 데이터 규격이 유효하지 않습니다.")
            else:
                logger.error(f"Modeling API Unexpected Error [{response.status_code}]")
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="모델링 서버로부터 올바른 식단 데이터를 받지 못했습니다.")
                
        except httpx.TimeoutException:
            logger.error(f"Core Modeling Timeout: /monthly-plan failed after {int((time.time() - start_time) * 1000)}ms due to Read Timeout.")
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="한 달 식단 생성 연산 시간이 너무 오래 걸려 타임아웃되었습니다.")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="모델링 서버가 다운되었거나 연결할 수 없습니다.")