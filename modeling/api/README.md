# 🚀 FastAPI Modeling API

오늘의 끼니 Modeling 파이프라인을 Backend에서 호출할 수 있도록 제공하는 FastAPI 기반 API 서버입니다.

사용자 Profile을 검증한 뒤 식단 Style 후보 생성 또는 월간 식단 생성 Service를 호출하며, 운영 환경에서는 API Key 인증, 내부 오류 정보 비노출, API 문서 비활성화와 Prometheus Metrics 수집 정책을 적용합니다.

```text
Backend / Client
        ↓
FastAPI Endpoint
        ↓
Pydantic Request Validation
        ↓
X-API-Key Authentication
        ↓
Modeling Service
        ↓
RAG / Recommendation / Optimizer / Plan
        ↓
HTTP Response
        ↓
Prometheus Metrics
```

<br>

## 목차

1. [API 모듈 역할](#1-api-모듈-역할)
2. [전체 요청 처리 흐름](#2-전체-요청-처리-흐름)
3. [파일 구조](#3-파일-구조)
4. [FastAPI Application](#4-fastapi-application)
5. [실행 환경](#5-실행-환경)
6. [API 문서 노출 정책](#6-api-문서-노출-정책)
7. [API Key 인증](#7-api-key-인증)
8. [Health Check](#8-health-check)
9. [Metrics Endpoint](#9-metrics-endpoint)
10. [Meal Style Candidates API](#10-meal-style-candidates-api)
11. [Monthly Plan API](#11-monthly-plan-api)
12. [공통 User Profile Schema](#12-공통-user-profile-schema)
13. [Profile 필드 검증](#13-profile-필드-검증)
14. [Meal Style 요청 Schema](#14-meal-style-요청-schema)
15. [Monthly Plan 요청 Schema](#15-monthly-plan-요청-schema)
16. [Selected Style Schema](#16-selected-style-schema)
17. [추가 필드 허용 정책](#17-추가-필드-허용-정책)
18. [Pydantic 호환 처리](#18-pydantic-호환-처리)
19. [HTTP 오류 처리](#19-http-오류-처리)
20. [RAG 오류 상태 매핑](#20-rag-오류-상태-매핑)
21. [운영 환경 오류 응답](#21-운영-환경-오류-응답)
22. [Prometheus Metrics](#22-prometheus-metrics)
23. [HTTP 요청 Middleware](#23-http-요청-middleware)
24. [Path Label 정규화](#24-path-label-정규화)
25. [오류 Metrics](#25-오류-metrics)
26. [Logging](#26-logging)
27. [로컬 실행](#27-로컬-실행)
28. [Docker 실행](#28-docker-실행)
29. [HTTP 호출 예시](#29-http-호출-예시)
30. [테스트](#30-테스트)
31. [현재 구현상 주의사항](#31-현재-구현상-주의사항)
32. [관련 문서](#32-관련-문서)

<br>

## 1. API 모듈 역할

API 모듈은 Modeling 내부 로직과 Backend 사이의 진입점 역할을 합니다.

주요 책임:

```text
요청 JSON 검증
API Key 인증
Modeling Service 호출
RAG 예외의 HTTP 상태 변환
운영 환경 오류 정보 비노출
HTTP 요청 수 및 처리 시간 기록
Prometheus Metrics 제공
```

API 계층에서는 Recommendation이나 Optimizer 로직을 직접 수행하지 않습니다.

실제 비즈니스 로직은 다음 Service에 위임합니다.

```python
create_meal_style_candidates(payload)
create_monthly_plan(payload)
```

<br>

## 2. 전체 요청 처리 흐름

```text
HTTP 요청
   ↓
HTTP Metrics Middleware
   ↓
Pydantic Request Schema 검증
   ↓
Endpoint 함수 진입
   ↓
verify_api_key()
   ↓
Pydantic Model → dict 변환
   ↓
Modeling Service 호출
   ↓
성공 응답 반환
```

오류 발생 시:

```text
RagRequestError
   ├── Timeout 계열 → HTTP 504
   └── 기타 RAG 오류 → HTTP 502

기타 Exception
   └── HTTP 500
```

FastAPI 또는 Pydantic 요청 검증 실패는 Endpoint 함수가 실행되기 전에 HTTP `422`로 처리됩니다.

<br>

## 3. 파일 구조

```text
modeling/
├── api/
│   ├── __init__.py
│   ├── server.py
│   ├── metrics.py
│   └── README.md
│
├── schemas/
│   ├── user_profile_schema.py
│   └── persona_profile_schema.py
│
├── services/
│   ├── modeling_service.py
│   └── rag/
│       └── rag_client.py
│
└── tests/
    └── api/
        ├── test_modeling_api_request_validation.py
        ├── test_modeling_api_rag_error_status.py
        └── test_modeling_api_metrics.py
```

### 파일별 역할

| 파일 | 역할 |
|---|---|
| `server.py` | FastAPI App, Endpoint, 인증과 예외 처리 |
| `metrics.py` | Prometheus Metric 정의 및 Path 정규화 |
| `user_profile_schema.py` | 식단 생성용 사용자 Profile 검증 |
| `persona_profile_schema.py` | Persona Profile Build 요청 검증 |
| `rag_client.py` | RAG 호출 및 `RagRequestError` 정의 |
| `modeling_service.py` | 실제 Modeling 파이프라인 실행 |

<br>

## 4. FastAPI Application

FastAPI Application은 다음 설정으로 생성됩니다.

```python
app = FastAPI(
    title="Todays Ggini Modeling Server",
    description="FastAPI server for Todays Ggini modeling service.",
    version="0.1.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
)
```

현재 API Version:

```text
0.1.0
```

현재 제공되는 주요 Endpoint:

| Method | Path | 인증 | 역할 |
|---|---|---|---|
| `GET` | `/health` | 없음 | 서버 상태 확인 |
| `GET` | `/metrics` | 환경별 적용 | Prometheus Metrics |
| `POST` | `/meal-style-candidates` | 환경별 적용 | 식단 Style 후보 생성 |
| `POST` | `/monthly-plan` | 환경별 적용 | 월간 식단 생성 |

`/metrics`는 OpenAPI Schema에 포함되지 않습니다.

```python
include_in_schema=False
```

<br>

## 5. 실행 환경

실행 환경은 `ENV` 환경 변수로 구분합니다.

```python
ENV = os.getenv("ENV", "local")
```

기본값:

```text
local
```

대표 환경:

```text
local
prod
```

환경에 따라 다음 정책이 달라집니다.

| 항목 | local | prod |
|---|---|---|
| API Key 미설정 | 인증 생략 | 서버 설정 오류 |
| Swagger | 노출 | 비활성화 |
| ReDoc | 노출 | 비활성화 |
| OpenAPI JSON | 노출 | 비활성화 |
| `/health`의 `env` | 포함 | 제외 |
| 내부 Exception 정보 | 포함 | 공개용 메시지만 포함 |

<br>

## 6. API 문서 노출 정책

환경에 따라 API 문서 URL을 설정합니다.

```python
docs_url = None if ENV == "prod" else "/docs"
redoc_url = None if ENV == "prod" else "/redoc"
openapi_url = None if ENV == "prod" else "/openapi.json"
```

### Local

```text
/docs
/redoc
/openapi.json
```

접근 가능

### Production

세 Endpoint 모두 비활성화됩니다.

이는 외부에서 API 구조, Schema와 내부 Endpoint 정보를 쉽게 확인하지 못하도록 하기 위한 운영 보안 설정입니다.

<br>

## 7. API Key 인증

관련 함수:

```python
verify_api_key(
    x_api_key: str | None,
) -> None
```

API Key는 다음 환경 변수에서 읽습니다.

```text
MODELING_API_KEY
```

호출 Header:

```http
X-API-Key: <MODELING_API_KEY>
```

### Local 인증 정책

다음 조건이면 인증을 생략합니다.

```text
ENV != "prod"
AND
MODELING_API_KEY가 설정되지 않음
```

즉, 별도의 환경 변수 없이 로컬에서 실행하면 인증 없이 API를 호출할 수 있습니다.

### Local에서 API Key가 설정된 경우

`ENV`가 `local`이어도 `MODELING_API_KEY`가 설정되어 있으면 요청 Header와 Key를 비교합니다.

따라서 로컬에서 운영과 동일한 인증 흐름을 테스트할 수 있습니다.

### Production 인증 정책

`ENV=prod`에서는 `MODELING_API_KEY`가 반드시 설정되어야 합니다.

Key 자체가 설정되지 않은 경우:

```text
HTTP 500
Server configuration error.
```

Key가 누락되거나 값이 다른 경우:

```text
HTTP 401
Invalid or missing API key.
```

### 인증 적용 Endpoint

```text
GET  /metrics
POST /meal-style-candidates
POST /monthly-plan
```

### 인증이 적용되지 않는 Endpoint

```text
GET /health
```

`/health`는 Docker Health Check와 Nginx, 배포 검증에서 사용할 수 있도록 인증 없이 접근 가능합니다.

<br>

## 8. Health Check

Endpoint:

```http
GET /health
```

### Local 응답

```json
{
  "status": "ok",
  "service": "todays-ggini-modeling",
  "env": "local"
}
```

### Production 응답

```json
{
  "status": "ok",
  "service": "todays-ggini-modeling"
}
```

운영 환경에서는 `env`를 반환하지 않아 내부 실행 환경 정보의 외부 노출을 줄입니다.

### 확인 명령

```bash
curl -fsS http://127.0.0.1:8001/health \
  | python -m json.tool
```

<br>

## 9. Metrics Endpoint

Endpoint:

```http
GET /metrics
```

Prometheus Text Exposition 형식으로 Metric을 반환합니다.

응답 Media Type:

```text
prometheus_client.CONTENT_TYPE_LATEST
```

운영 환경에서는 API Key 인증이 필요합니다.

```bash
curl -fsS \
  -H "X-API-Key: local-secret-key" \
  http://127.0.0.1:8001/metrics
```

`/metrics`는 자체 Metrics 집계 대상에서는 제외됩니다.

<br>

## 10. Meal Style Candidates API

Endpoint:

```http
POST /meal-style-candidates
```

역할:

```text
사용자의 초기 Profile 입력
→ 식단 Style 후보 3개 생성
→ 각 Style의 Sample Plan 반환
```

Request Model:

```python
MealStyleCandidatesRequest
```

허용되는 `request_type`:

```json
{
  "request_type": "meal_style_candidates"
}
```

다른 값이 들어오면 Pydantic 검증 단계에서 HTTP `422`가 반환됩니다.

### Service 연결

```python
create_meal_style_candidates(payload)
```

### 요청 예시

```json
{
  "id": 1,
  "request_type": "meal_style_candidates",
  "profile": {
    "goals": [
      "영양 균형",
      "고단백"
    ],
    "monthly_budget": 480000,
    "meal_count_per_day": 3,
    "cooking_skill": 3,
    "preferred_categories": [
      "한식"
    ],
    "diversity_level": "보통",
    "ingredient_preferences": [
      "육류"
    ],
    "allergy_ingredients": [],
    "sample_period_days": 3
  }
}
```

<br>

## 11. Monthly Plan API

Endpoint:

```http
POST /monthly-plan
```

역할:

```text
사용자 Profile
+ 선택한 식단 Style
→ 월간 후보 메뉴 조회
→ Recommendation
→ OR-Tools Optimization
→ Plan 및 Validation
→ 최종 월간 식단 반환
```

Request Model:

```python
MonthlyPlanRequest
```

허용되는 `request_type`:

```json
{
  "request_type": "monthly_plan"
}
```

### Service 연결

```python
create_monthly_plan(payload)
```

### OR-Tools 기본값

```text
use_ortools = True
```

따라서 별도 필드가 없으면 OR-Tools 기반 월간 최적화를 사용합니다.

### Optimizer Config

```python
optimizer_config: dict[str, Any] = Field(
    default_factory=dict
)
```

Optimizer 실험 또는 정책 Override를 요청 단위로 전달할 수 있습니다.

대표 예시:

```json
{
  "optimizer_config": {
    "repeat_penalty_weight": 4500,
    "repeat_penalty_growth": "quadratic",
    "solver_time_limit_seconds": 5
  }
}
```

운영 Backend가 임의의 Optimizer Config를 전달하도록 허용할지 여부는 별도 API 계약과 보안 정책으로 관리해야 합니다.

<br>

## 12. 공통 User Profile Schema

관련 파일:

```text
modeling/schemas/user_profile_schema.py
```

공통 Request 구조:

```python
class UserProfileRequest(BaseModel):
    id: int | str
    request_type: str
    profile: UserProfileInput
```

### ID

```text
int 또는 str
```

사용자 식별값으로 사용됩니다.

### Request Type

상위 공통 Schema에서는 문자열이지만 실제 Endpoint별 하위 Schema에서 `Literal`로 제한합니다.

### Profile

```python
UserProfileInput
```

사용자의 목표, 예산, 식사 수, 조리 실력, 선호와 알레르기 정보를 포함합니다.

<br>

## 13. Profile 필드 검증

### Goals

```python
goals: List[str] = Field(
    ...,
    min_length=1,
    max_length=3,
)
```

허용값:

```text
식비 절약
영양 균형
다이어트
고단백
간편식
맛 중심
```

조건:

```text
최소 1개
최대 3개
중복 금지
허용 목록 외 값 금지
```

### Monthly Budget

```python
monthly_budget: int = Field(..., gt=0)
```

`0` 이하이면 HTTP `422`가 반환됩니다.

### Meal Count Per Day

```python
meal_count_per_day: int = Field(
    ...,
    ge=1,
    le=5,
)
```

허용 범위:

```text
1~5끼
```

### Recommended Daily Calories

```python
recommended_daily_calories: Optional[int]
```

값이 있다면 `0`보다 커야 합니다.

### Cooking Skill

```python
cooking_skill: int = Field(
    ...,
    ge=1,
    le=5,
)
```

허용 범위:

```text
1~5
```

### Preferred Categories

최소 한 개가 필요합니다.

허용값:

```text
한식
양식
일식
중식
분식
샐러드/건강식
디저트
다 좋아요
```

중복 입력은 허용되지 않습니다.

### Diversity Level

허용값:

```text
낮음
보통
높음
```

### Ingredient Preferences

허용값:

```text
육류
해산물류
식물성 단백질류
채소류
계란 및 유제품류
```

빈 배열은 허용하지만 중복과 허용되지 않은 값은 거부합니다.

### Allergy Ingredients

문자열 List이며 중복 입력을 허용하지 않습니다.

현재 알레르기 재료 자체를 사전 허용 목록으로 제한하지는 않습니다.

### Sample Period Days

```python
sample_period_days: int = Field(
    default=3,
    ge=1,
    le=7,
)
```

허용 범위:

```text
1~7일
```

기본값:

```text
3일
```

### Period Days

```python
period_days: Optional[int] = Field(
    default=None,
    ge=1,
    le=31,
)
```

허용 범위:

```text
1~31일
```

값이 없으면 Profile 생성 단계에서 기본 기간을 적용할 수 있습니다.

<br>

## 14. Meal Style 요청 Schema

```python
class MealStyleCandidatesRequest(
    UserProfileRequest
):
    request_type: Literal[
        "meal_style_candidates"
    ]
```

공통 User Profile 검증을 재사용하고 `request_type`을 하나의 값으로 제한합니다.

필수 필드:

```text
id
request_type
profile
```

`selected_style`은 필요하지 않습니다.

<br>

## 15. Monthly Plan 요청 Schema

```python
class MonthlyPlanRequest(
    UserProfileRequest
):
    request_type: Literal["monthly_plan"]
    selected_style: SelectedStyleRequest
    use_ortools: bool = True
    optimizer_config: dict[str, Any]
```

필수 필드:

```text
id
request_type
profile
selected_style
```

선택 필드:

```text
use_ortools
optimizer_config
```

### Validation 실패 예시

```text
빈 요청
id 누락
request_type 불일치
profile 누락
selected_style 누락
selected_style 내부 필드 누락
monthly_budget = 0
```

위 요청은 모두 HTTP `422`를 반환합니다.

<br>

## 16. Selected Style Schema

```python
class SelectedStyleRequest(BaseModel):
    style_id: str
    style_name: str
    source_goal: str
    focus_key: str
```

필수 필드:

```text
style_id
style_name
source_goal
focus_key
```

예시:

```json
{
  "style_id": "high_protein",
  "style_name": "고단백 관리식",
  "source_goal": "고단백",
  "focus_key": "nutrition"
}
```

현재 API Schema에서는 `source_goal`과 `focus_key`를 별도의 `Literal` 또는 허용 목록으로 제한하지 않습니다.

내부 Style Service에서 생성한 값을 그대로 전달하는 것을 전제로 합니다.

<br>

## 17. 추가 필드 허용 정책

두 Endpoint Request Model과 `SelectedStyleRequest`는 다음 설정을 사용합니다.

```python
model_config = ConfigDict(
    extra="allow"
)
```

즉, Schema에 선언되지 않은 추가 필드가 들어와도 요청을 거부하지 않습니다.

장점:

```text
Backend와 Modeling 계약 확장 시
기존 API가 즉시 깨질 가능성을 줄임
```

주의점:

```text
오타 필드가 있어도 검증 오류가 발생하지 않을 수 있음
사용하지 않는 입력이 조용히 전달될 수 있음
공개 API에서는 예상하지 못한 데이터가 내부로 전달될 수 있음
```

현재 API는 내부 Backend와 Modeling 사이의 Service API를 전제로 한 유연한 계약입니다.

<br>

## 18. Pydantic 호환 처리

관련 함수:

```python
model_to_payload(
    model: BaseModel,
) -> dict[str, Any]
```

Pydantic Version에 따라 다음 메서드를 선택합니다.

```text
Pydantic v2
→ model.model_dump()

Pydantic v1
→ model.dict()
```

현재 Schema에서는 Pydantic v2의 `field_validator`와 `ConfigDict`를 사용하지만, Payload 변환 함수는 두 Version의 Model 변환 방식에 대응합니다.

<br>

## 19. HTTP 오류 처리

### 요청 검증 실패

```text
HTTP 422
```

FastAPI와 Pydantic이 자동으로 처리합니다.

예시:

```text
필수 필드 누락
Literal 불일치
예산 범위 오류
목표 허용값 오류
중복 입력
```

### API Key 오류

```text
HTTP 401
```

상세 메시지:

```text
Invalid or missing API key.
```

### 서버 인증 설정 오류

```text
HTTP 500
```

운영 환경에서 `MODELING_API_KEY` 자체가 설정되지 않은 경우입니다.

### RAG Timeout

```text
HTTP 504
```

### 기타 RAG Upstream 오류

```text
HTTP 502
```

### 예상하지 못한 내부 오류

```text
HTTP 500
```

<br>

## 20. RAG 오류 상태 매핑

관련 함수:

```python
get_rag_error_status_code(
    error: RagRequestError,
) -> int
```

Timeout Failure Reason:

```text
rag_read_timeout
rag_timeout
```

위 두 경우:

```text
HTTP 504 Gateway Timeout
```

그 외 RAG 외부 의존성 실패:

```text
HTTP 502 Bad Gateway
```

테스트된 Failure Reason:

| Failure Reason | HTTP Status |
|---|---:|
| `rag_read_timeout` | 504 |
| `rag_timeout` | 504 |
| `rag_connection_error` | 502 |
| `rag_request_error` | 502 |
| `rag_http_error` | 502 |

RAG 원본 HTTP Status가 `500`이어도 Modeling API는 외부 Upstream 실패를 의미하는 `502`로 변환합니다.

<br>

## 21. 운영 환경 오류 응답

관련 함수:

```python
build_error_detail(
    error: Exception,
    public_message: str,
) -> Any
```

### Local

디버깅을 위해 예외 Type과 메시지를 반환합니다.

```json
{
  "type": "RagRequestError",
  "message": "RAG request failed"
}
```

### Production

내부 구현 정보 대신 사전에 정의한 공개 메시지만 반환합니다.

RAG 오류:

```text
External recommendation service error.
```

내부 오류:

```text
Internal server error.
```

운영 환경에서는 Stack Trace나 외부 API URL, 응답 본문이 Client 응답에 직접 포함되지 않습니다.

단, 서버 Log에는 `logger.exception()`을 통해 Stack Trace가 기록됩니다.

<br>

## 22. Prometheus Metrics

관련 파일:

```text
modeling/api/metrics.py
```

독립 `CollectorRegistry`를 사용합니다.

```python
METRICS_REGISTRY = CollectorRegistry()
```

### HTTP 요청 수

Metric:

```text
modeling_http_requests_total
```

Type:

```text
Counter
```

Labels:

```text
method
path
status_code
```

예시:

```promql
modeling_http_requests_total{
  method="POST",
  path="/monthly-plan",
  status_code="200"
}
```

### HTTP 처리 시간

Metric:

```text
modeling_http_request_duration_seconds
```

Type:

```text
Histogram
```

Labels:

```text
method
path
```

Bucket:

```text
0.01
0.025
0.05
0.1
0.25
0.5
1.0
2.5
5.0
10.0
30.0
60.0
```

p95 예시:

```promql
histogram_quantile(
  0.95,
  sum by (le, path) (
    rate(
      modeling_http_request_duration_seconds_bucket[5m]
    )
  )
)
```

### 진행 중 요청 수

Metric:

```text
modeling_http_requests_in_progress
```

Type:

```text
Gauge
```

Labels:

```text
method
path
```

### API 오류 수

Metric:

```text
modeling_api_errors_total
```

Type:

```text
Counter
```

Labels:

```text
path
error_type
status_code
```

<br>

## 23. HTTP 요청 Middleware

관련 함수:

```python
@app.middleware("http")
async def observe_http_request(
    request: Request,
    call_next,
)
```

Middleware는 비즈니스 요청에 대해 다음을 기록합니다.

```text
요청 시작
→ in_progress +1

응답 또는 예외 처리
→ status_code 결정
→ 처리 시간 계산
→ in_progress -1
→ requests_total +1
→ duration Histogram 기록
```

기본 `status_code`는 `500`으로 시작합니다.

```python
status_code = (
    status.HTTP_500_INTERNAL_SERVER_ERROR
)
```

따라서 `call_next()` 실행 중 Middleware 밖으로 예외가 전파되더라도 `finally`에서 HTTP 요청 Metric은 `500`으로 기록될 수 있습니다.

### 401과 422

응답 상태가 다음 값이면 의미 기반 오류 Counter도 기록합니다.

```text
401 → authentication
422 → validation
```

RAG와 내부 실행 오류는 각 Endpoint의 Exception Handler에서 별도로 기록합니다.

<br>

## 24. Path Label 정규화

Prometheus Label Cardinality 증가를 막기 위해 요청 URL을 그대로 Label에 넣지 않습니다.

모니터링 대상:

```text
/meal-style-candidates
/monthly-plan
```

집계 제외:

```text
/health
/metrics
```

등록되지 않은 모든 경로:

```text
/unmatched
```

예시:

```text
/users/1
/users/2
/arbitrary-user-controlled-path
```

모두 다음 Label로 합쳐집니다.

```text
/unmatched
```

이를 통해 임의 경로 요청으로 Prometheus 시계열이 무한히 늘어나는 문제를 방지합니다.

<br>

## 25. 오류 Metrics

관련 함수:

```python
record_api_error(
    path: str,
    error_type: str,
    status_code: int,
) -> None
```

현재 사용되는 대표 `error_type`:

```text
authentication
validation
rag_timeout
rag_upstream
unexpected
```

### 인증 실패

```text
path = 정규화된 요청 Path
error_type = authentication
status_code = 401
```

### Validation 실패

```text
error_type = validation
status_code = 422
```

### RAG Timeout

```text
error_type = rag_timeout
status_code = 504
```

### RAG Upstream 오류

```text
error_type = rag_upstream
status_code = 502
```

### 예상하지 못한 오류

```text
error_type = unexpected
status_code = 500
```

실제 예외 메시지, User ID, API Key와 URL은 Metric Label에 사용하지 않습니다.

<br>

## 26. Logging

Logging Level:

```python
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO")
)
```

기본값:

```text
INFO
```

Logger 이름:

```text
todays_ggini.modeling_api
```

RAG 오류:

```python
logger.exception(
    "RAG request failed ..."
)
```

예상하지 못한 오류:

```python
logger.exception(
    "Unexpected error ..."
)
```

`logger.exception()`은 Exception 처리 Context에서 Stack Trace를 함께 남깁니다.

### 권장 운영 원칙

```text
API Key 로그 출력 금지
전체 요청 Body 로그 출력 주의
알레르기·신체정보 등 사용자 입력 최소 노출
RAG 응답 전체 Log 저장 주의
운영 LOG_LEVEL은 INFO 또는 WARNING 사용
```

<br>

## 27. 로컬 실행

프로젝트의 `modeling` 디렉터리를 Python Path로 사용합니다.

### 인증 없이 실행

```bash
PYTHONPATH=modeling \
python -m uvicorn api.server:app \
  --host 127.0.0.1 \
  --port 8001 \
  --reload
```

기본 `ENV=local`이고 `MODELING_API_KEY`가 없으므로 인증이 생략됩니다.

Swagger:

```text
http://127.0.0.1:8001/docs
```

### API Key를 적용한 로컬 실행

```bash
ENV=local \
MODELING_API_KEY=local-secret-key \
PYTHONPATH=modeling \
python -m uvicorn api.server:app \
  --host 127.0.0.1 \
  --port 8001 \
  --reload
```

이 경우 Local 환경이어도 보호 Endpoint 호출 시 `X-API-Key`가 필요합니다.

### Production Mode 실행

```bash
ENV=prod \
MODELING_API_KEY=local-secret-key \
PYTHONPATH=modeling \
python -m uvicorn api.server:app \
  --host 0.0.0.0 \
  --port 8000
```

Production에서는 API 문서가 비활성화됩니다.

<br>

## 28. Docker 실행

Docker Compose:

```bash
MODELING_API_KEY=local-secret-key \
docker compose \
  -f docker-compose.modeling.yml \
  up \
  --build \
  -d
```

포트 매핑:

```text
Host 8001
→ Container 8000
```

상태 확인:

```bash
docker compose \
  -f docker-compose.modeling.yml \
  ps
```

Log 확인:

```bash
docker compose \
  -f docker-compose.modeling.yml \
  logs \
  --tail=200 \
  modeling-api
```

종료:

```bash
docker compose \
  -f docker-compose.modeling.yml \
  down
```

Compose에서는 `MODELING_API_KEY`가 필수 환경 변수로 선언되어 있습니다.

```yaml
MODELING_API_KEY:
  ${MODELING_API_KEY:?MODELING_API_KEY is required}
```

<br>

## 29. HTTP 호출 예시

### Health Check

```bash
curl -fsS \
  http://127.0.0.1:8001/health \
  | python -m json.tool
```

### Meal Style Candidates

```bash
curl -fsS \
  -X POST \
  http://127.0.0.1:8001/meal-style-candidates \
  -H "Content-Type: application/json" \
  -H "X-API-Key: local-secret-key" \
  --data-binary \
  @modeling/experiments/fixtures/backend_style_candidates_request.json \
  | python -m json.tool
```

### Monthly Plan

```bash
curl -fsS \
  -X POST \
  http://127.0.0.1:8001/monthly-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: local-secret-key" \
  --data-binary \
  @modeling/experiments/fixtures/backend_monthly_plan_request.json \
  | python -m json.tool
```

### Metrics

```bash
curl -fsS \
  -H "X-API-Key: local-secret-key" \
  http://127.0.0.1:8001/metrics
```

### HTTP Status와 Body 분리 확인

```bash
curl \
  --silent \
  --show-error \
  --output /tmp/modeling_response.json \
  --write-out 'http_status=%{http_code}\n' \
  -X POST \
  http://127.0.0.1:8001/monthly-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: local-secret-key" \
  --data-binary \
  @modeling/experiments/fixtures/backend_monthly_plan_request.json

python -m json.tool \
  /tmp/modeling_response.json
```

<br>

## 30. 테스트

### Request Validation 테스트

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/api/test_modeling_api_request_validation.py \
  -q
```

검증 범위:

```text
빈 Monthly Request → 422
id 누락 → 422
잘못된 request_type → 422
profile 누락 → 422
selected_style 누락 → 422
selected_style 불완전 → 422
monthly_budget = 0 → 422
정상 Monthly Request → Service 호출
빈 Style Request → 422
잘못된 Style request_type → 422
정상 Style Request → Service 호출
API Key 누락 → 401
```

### RAG 상태 매핑 테스트

```bash
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/api/test_modeling_api_rag_error_status.py \
  -q
```

검증 범위:

```text
rag_read_timeout → 504
rag_timeout → 504
rag_connection_error → 502
rag_request_error → 502
rag_http_error → 502
```

독립 실행도 지원합니다.

```bash
PYTHONPATH=modeling \
python \
  modeling/tests/api/test_modeling_api_rag_error_status.py
```

### Metrics 테스트

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/api/test_modeling_api_metrics.py \
  -q
```

검증 범위:

```text
운영 /metrics API Key 인증
Prometheus Content 반환
비즈니스 요청 Metric 기록
알 수 없는 Path를 /unmatched로 집계
/health와 /metrics 집계 제외
422 Validation 오류 기록
401 인증 오류 기록
504 RAG Timeout 기록
502 RAG Upstream 오류 기록
500 내부 오류 기록
```

### API 전체 테스트

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/api \
  -q
```

### 문법 검사

```bash
python -m py_compile \
  modeling/api/server.py \
  modeling/api/metrics.py \
  modeling/schemas/user_profile_schema.py
```

### 전체 Modeling 테스트

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests \
  -q
```

<br>

## 31. 현재 구현상 주의사항

### Health Endpoint는 인증되지 않음

`/health`는 운영 환경에서도 인증 없이 접근 가능합니다.

현재 응답은 Service 이름과 `ok` 상태만 포함하므로 노출 위험이 제한적이지만, 상세 Dependency 상태를 추가할 때는 민감정보가 포함되지 않도록 해야 합니다.

### Production에서 API Key 누락은 요청 시점에 발견

`MODELING_API_KEY` 누락 여부를 App 시작 단계에서 즉시 종료시키는 것이 아니라 보호 Endpoint 호출 시 HTTP `500`으로 처리합니다.

Docker Compose에서는 변수 검증으로 실행 전 차단하지만, 직접 Uvicorn 실행 시에는 서버가 기동된 뒤 첫 요청에서 발견될 수 있습니다.

### API Key 단일 공유 Secret 방식

현재 인증은 단일 API Key 문자열 비교 방식입니다.

```text
X-API-Key == MODELING_API_KEY
```

다음 기능은 포함하지 않습니다.

```text
사용자별 Key
Key Rotation 자동화
만료 시간
요청 서명
권한 Scope
Rate Limit
```

Backend와 Modeling 사이의 내부 Service 인증 용도로 사용해야 합니다.

### HTTPS는 App 내부가 아닌 Proxy 계층에서 적용

FastAPI App 자체는 HTTP로 실행될 수 있습니다.

운영 환경에서는 Nginx 또는 Load Balancer에서 HTTPS를 종료하고 내부 FastAPI Port를 외부에 직접 노출하지 않는 구성이 필요합니다.

### CORS Middleware 없음

현재 `server.py`에는 CORS Middleware가 없습니다.

이 API는 Browser Frontend가 직접 호출하는 것이 아니라 Backend가 호출하는 내부 API를 전제로 합니다.

Frontend 직접 호출이 필요해지면 허용 Origin을 제한한 CORS 설정이 필요합니다.

### Request 추가 필드 허용

Endpoint Request Model의 `extra="allow"` 설정으로 선언되지 않은 필드가 허용됩니다.

내부 API 확장에는 유리하지만 오타나 예상하지 못한 입력을 조기에 발견하기 어렵습니다.

계약이 안정화된 뒤 `extra="forbid"` 전환 여부를 검토할 수 있습니다.

### Selected Style 허용값 미제한

`source_goal`과 `focus_key`는 필수 문자열이지만 허용 목록 검증은 없습니다.

Backend가 임의 값을 보내면 내부 Style 적용이 생략되거나 예상하지 못한 결과가 발생할 수 있습니다.

### Optimizer Config 임의 전달 가능

`optimizer_config`는 자유 형식 Dictionary입니다.

운영 요청에서 허용할 설정 목록을 제한하지 않으면 Solver 시간, Candidate 수와 가중치가 요청마다 달라질 수 있습니다.

### Metrics Path는 제한적으로 관리

현재 비즈니스 Path는 두 개만 명시적으로 모니터링합니다.

새 Endpoint를 추가하면 `MONITORED_PATHS`에 등록하지 않는 한 `/unmatched`로 집계됩니다.

### Metrics Registry가 독립적임

기본 Prometheus Registry가 아니라 별도 `CollectorRegistry`를 사용합니다.

다른 Library가 기본 Registry에 등록한 Process 또는 Python Runtime Metric은 현재 `/metrics`에 자동 포함되지 않습니다.

### Health와 Metrics 트래픽 제외

`/health`와 `/metrics`는 요청 수, 지연 시간과 진행 중 요청 Metric에서 제외됩니다.

운영 Monitoring Traffic이 비즈니스 요청 통계를 왜곡하지 않는 장점이 있지만, Health Endpoint 자체의 장애율은 이 Metric으로 확인할 수 없습니다.

### Histogram 최대 명시 Bucket

명시된 마지막 Bucket은 `60초`지만 Prometheus Histogram에는 기본적으로 `+Inf` Bucket도 생성됩니다.

월간 Plan이 60초를 초과하면 `+Inf`에만 포함될 수 있으므로 p95와 Timeout 정책을 함께 확인해야 합니다.

### 401·422 중복 기록 구조

`401`과 `422`는 Middleware에서 오류 Counter를 기록합니다.

RAG 및 예상하지 못한 오류는 Endpoint Exception Handler에서 기록합니다.

새 예외 처리 코드를 추가할 때 Middleware와 Endpoint 양쪽에서 같은 오류를 중복 기록하지 않도록 주의해야 합니다.

### 운영 오류는 Client에 축약됨

운영 응답에서는 상세 예외를 숨기므로 문제 분석 시 서버 Log와 Prometheus Metric을 함께 확인해야 합니다.

<br>

## 32. 관련 문서

### Repository 문서

- [`../README.md`](../README.md)  
  Modeling 전체 아키텍처, 실행 방법과 데이터 흐름

- [`../deploy/README.md`](../deploy/README.md)  
  Docker, EC2, Nginx, Prometheus와 Grafana 배포 구성

- [`../docs/modeling_serving_guide.md`](../docs/modeling_serving_guide.md)  
  FastAPI Modeling Server의 로컬·Docker 실행 및 운영 가이드

- [`../docs/backend_modeling_api_client_guide.md`](../docs/backend_modeling_api_client_guide.md)  
  Backend에서 Modeling API를 호출할 때 필요한 환경 변수, Header와 요청 예시

- [`../services/style/README.md`](../services/style/README.md)  
  식단 Style 후보 생성과 선택 Style 반영

- [`../services/optimizer/README.md`](../services/optimizer/README.md)  
  OR-Tools 월간 식단 최적화와 Retry 정책

- [`../services/plan/README.md`](../services/plan/README.md)  
  월간 Plan 매핑, MMR 다양성, Summary와 Payload

### 프로젝트 설계 및 배포

- [🚀 FastAPI 기반 모델링 서버 서빙 및 배포](https://app.notion.com/p/FastAPI-3859e3e335cc8000b0edeb7366ca5ccc?source=copy_link)  
  FastAPI 모델링 서버 구성, Docker 컨테이너화, EC2 배포와 Backend 연동 과정
