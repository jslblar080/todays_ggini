# 🧪 Modeling Test Guide

오늘의 끼니 Modeling 영역의 자동화 테스트, API 계약 검증, HTTP Smoke Test와 품질 실험의 역할을 정리한 문서입니다.

테스트는 빠르게 반복 실행할 수 있는 Pytest 기반 검증과 실제 실행 중인 FastAPI 컨테이너를 호출하는 HTTP Smoke Test, 전체 추천 품질을 평가하는 Experiment Validation으로 구분합니다.

```text
Source Code
    ↓
Pytest Unit / API / Contract Test
    ↓
Docker Build
    ↓
Container Health & Metrics Check
    ↓
HTTP Smoke Test
    ↓
Experiment Validation Pipeline
```

<br>

## 목차

1. [테스트 목적](#1-테스트-목적)
2. [테스트 전략](#2-테스트-전략)
3. [디렉터리 구조](#3-디렉터리-구조)
4. [현재 테스트 현황](#4-현재-테스트-현황)
5. [API Request Validation 테스트](#5-api-request-validation-테스트)
6. [API 인증 테스트](#6-api-인증-테스트)
7. [Prometheus Metrics 테스트](#7-prometheus-metrics-테스트)
8. [RAG 오류 상태 매핑 테스트](#8-rag-오류-상태-매핑-테스트)
9. [Backend 응답 Contract 테스트](#9-backend-응답-contract-테스트)
10. [Optimizer 결과 매핑 테스트](#10-optimizer-결과-매핑-테스트)
11. [Persona 테스트](#11-persona-테스트)
12. [Fixture](#12-fixture)
13. [Monkeypatch 사용](#13-monkeypatch-사용)
14. [전체 Pytest 실행](#14-전체-pytest-실행)
15. [범주별 테스트 실행](#15-범주별-테스트-실행)
16. [HTTP Smoke Test](#16-http-smoke-test)
17. [Smoke Test 검증 범위](#17-smoke-test-검증-범위)
18. [Docker 통합 검증](#18-docker-통합-검증)
19. [CI 테스트 흐름](#19-ci-테스트-흐름)
20. [Pytest와 Experiment의 차이](#20-pytest와-experiment의-차이)
21. [Experiment Validation 도구](#21-experiment-validation-도구)
22. [테스트 실패 해석](#22-테스트-실패-해석)
23. [테스트 작성 규칙](#23-테스트-작성-규칙)
24. [현재 테스트 공백](#24-현재-테스트-공백)
25. [권장 보강 순서](#25-권장-보강-순서)
26. [관련 문서](#26-관련-문서)

<br>

## 1. 테스트 목적

Modeling 테스트는 다음 문제를 조기에 발견하는 것을 목표로 합니다.

```text
API 요청 Schema 변경
API Key 인증 누락
Backend 응답 Contract 변경
RAG 오류 상태 코드 오분류
Prometheus Metric 누락
Optimizer 결과 매핑 오류
대체 메뉴 중복
Persona 생성 회귀
Docker 이미지 실행 실패
실행 서버와 코드 간 통합 오류
```

모델링 품질은 단순히 함수가 오류 없이 실행되는 것만으로 보장되지 않습니다.

따라서 테스트를 다음 두 축으로 나눕니다.

```text
기능·계약 안정성
→ Pytest / Contract / HTTP Smoke Test

추천 결과 품질
→ Scenario / Replay / Experiment Validation
```

<br>

## 2. 테스트 전략

### 1단계: 정적 검증

```text
Python 문법 오류
Import 오류
잘못된 모듈 경로
```

대표 명령:

```bash
python -m py_compile \
  modeling/api/server.py \
  modeling/api/metrics.py
```

### 2단계: 빠른 단위·API 테스트

```text
Pydantic Validation
API Key
오류 상태 매핑
Metrics
응답 Contract
결과 Mapper
```

대표 도구:

```text
pytest
FastAPI TestClient
monkeypatch
고정 JSON Fixture
```

### 3단계: 실행 서버 Smoke Test

```text
Docker Container
Uvicorn
HTTP Port
API Key
Health Endpoint
실제 HTTP 요청
```

### 4단계: 품질 검증

```text
RAG 후보 품질
Recommendation 점수
Optimizer 성공률
중복률
Style Validation
Runtime
Fallback
```

이 단계는 `modeling/experiments`의 Pipeline과 Replay 도구가 담당합니다.

<br>

## 3. 디렉터리 구조

```text
modeling/
├── tests/
│   ├── __init__.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── test_modeling_api_metrics.py
│   │   ├── test_modeling_api_rag_error_status.py
│   │   └── test_modeling_api_request_validation.py
│   │
│   ├── contract/
│   │   ├── __init__.py
│   │   └── test_optimizer_failure_response_contract.py
│   │
│   ├── optimizer/
│   │   ├── __init__.py
│   │   └── test_ortools_alternative_menus.py
│   │
│   ├── persona/
│   │   ├── __init__.py
│   │   └── test_persona_profile_build.py
│   │
│   └── README.md
│
├── experiments/
│   ├── fixtures/
│   ├── contract/
│   ├── pipelines/
│   ├── runners/
│   ├── tuning/
│   └── analysis/
│
└── api/
    ├── server.py
    └── metrics.py
```

<br>

## 4. 현재 테스트 현황

### 테스트 파일 수

| 범주 | 테스트 파일 수 |
|---|---:|
| API | 3 |
| Contract | 1 |
| Optimizer | 1 |
| Persona | 1 |
| 합계 | 6 |

### 확인된 Pytest 함수 수

| 범주 | 테스트 함수 수 |
|---|---:|
| API Metrics | 10 |
| API Request Validation | 12 |
| RAG Error Mapping | 5 |
| Contract | 4 |
| Optimizer | 2 |
| 합계 | 33 + Persona 테스트 |

Persona 테스트의 세부 함수 수는 파일 내용 변경에 따라 달라질 수 있으므로 다음 명령으로 최신 상태를 확인합니다.

```bash
grep -nE '^def test_|^class Test' \
  modeling/tests/persona/test_persona_profile_build.py
```

### 전체 테스트 목록 확인

```bash
grep -RInE \
  --include='*.py' \
  --exclude-dir='__pycache__' \
  '^def test_|^async def test_|^class Test' \
  modeling/tests
```

<br>

## 5. API Request Validation 테스트

관련 파일:

```text
modeling/tests/api/test_modeling_api_request_validation.py
```

FastAPI `TestClient`를 사용해 HTTP 요청 검증과 Service 연결을 확인합니다.

```python
client = TestClient(server.app)
```

### Monthly Plan 요청 검증

현재 확인된 테스트:

```text
빈 요청 → HTTP 422
id 누락 → HTTP 422
잘못된 request_type → HTTP 422
profile 누락 → HTTP 422
selected_style 누락 → HTTP 422
selected_style.style_id 누락 → HTTP 422
monthly_budget = 0 → HTTP 422
정상 요청 → create_monthly_plan() 호출
API Key 누락 → HTTP 401
```

### Meal Style Candidates 요청 검증

```text
빈 요청 → HTTP 422
잘못된 request_type → HTTP 422
정상 요청 → create_meal_style_candidates() 호출
```

### 검증 목적

이 테스트는 단순히 Pydantic Model이 생성되는지만 확인하지 않습니다.

실제 Endpoint에 HTTP 요청을 보내 다음 전체 흐름을 확인합니다.

```text
JSON 요청
→ Pydantic 검증
→ API 인증
→ Payload 변환
→ Service 함수 전달
→ HTTP 응답
```

<br>

## 6. API 인증 테스트

테스트용 Header:

```python
TEST_API_KEY = "ci-secret-key"

AUTH_HEADERS = {
    "X-API-Key": TEST_API_KEY,
}
```

대표 검증:

```text
정상 API Key
→ Endpoint Service까지 요청 전달

API Key 누락
→ HTTP 401

잘못된 API Key
→ HTTP 401
```

API Key 자체가 Git에 저장된 운영 Secret을 의미하지는 않습니다.

`ci-secret-key`, `metrics-test-key`와 같은 값은 테스트 격리용 고정 문자열입니다.

운영 Secret은 GitHub Actions Secret, EC2 환경 변수 또는 Secret Manager를 통해 관리해야 합니다.

<br>

## 7. Prometheus Metrics 테스트

관련 파일:

```text
modeling/tests/api/test_modeling_api_metrics.py
```

현재 테스트 함수:

```text
test_metrics_requires_api_key_in_prod
test_metrics_returns_prometheus_content
test_business_request_is_recorded_in_metrics
test_unknown_paths_use_bounded_label
test_health_and_metrics_requests_are_not_recorded
test_validation_error_is_recorded
test_authentication_error_is_recorded
test_rag_timeout_error_is_recorded
test_rag_upstream_error_is_recorded
test_unexpected_error_is_recorded
```

### `/metrics` 인증

```text
ENV=prod
+ API Key 없음
→ HTTP 401
```

정상 API Key가 있으면 Prometheus Text 형식의 응답을 반환합니다.

### 요청 Count 기록

예를 들어 잘못된 Monthly Request를 보내 HTTP `422`가 발생하면 다음 Label을 가진 Metric이 증가하는지 확인합니다.

```text
method="POST"
path="/monthly-plan"
status_code="422"
```

대상 Metric:

```text
modeling_http_requests_total
```

### 알 수 없는 Path 정규화

임의 사용자 입력 Path를 Metric Label로 직접 사용하지 않습니다.

```text
/arbitrary-user-controlled-path
→ /unmatched
```

테스트는 원본 임의 Path가 Metrics 응답에 나타나지 않는지 확인합니다.

### 집계 제외 Path

```text
/health
/metrics
```

위 요청은 비즈니스 요청 Metric에 기록되지 않아야 합니다.

### 오류 유형

현재 테스트하는 의미 기반 오류 유형:

| Error Type | HTTP Status |
|---|---:|
| `validation` | 422 |
| `authentication` | 401 |
| `rag_timeout` | 504 |
| `rag_upstream` | 502 |
| `unexpected` | 500 |

<br>

## 8. RAG 오류 상태 매핑 테스트

관련 파일:

```text
modeling/tests/api/test_modeling_api_rag_error_status.py
```

검증 함수:

```python
get_rag_error_status_code(
    error: RagRequestError
) -> int
```

현재 테스트 Cases:

| Failure Reason | 예상 HTTP Status |
|---|---:|
| `rag_read_timeout` | 504 |
| `rag_timeout` | 504 |
| `rag_connection_error` | 502 |
| `rag_request_error` | 502 |
| `rag_http_error` | 502 |

### 의미

```text
504 Gateway Timeout
→ 외부 RAG Service가 제한 시간 내 응답하지 않음

502 Bad Gateway
→ RAG 연결, 요청 또는 Upstream HTTP 오류
```

RAG 원본 상태가 `500`이어도 Modeling API는 외부 의존성 장애라는 의미를 유지하기 위해 `502`로 반환합니다.

### Pytest 없이 독립 실행

해당 파일에는 `main()`도 포함되어 있습니다.

```bash
PYTHONPATH=modeling \
python \
  modeling/tests/api/test_modeling_api_rag_error_status.py
```

정상 결과:

```text
rag_read_timeout: 504
rag_timeout: 504
rag_connection_error: 502
rag_request_error: 502
rag_http_error: 502
RAG error status mapping check passed.
```

<br>

## 9. Backend 응답 Contract 테스트

관련 파일:

```text
modeling/tests/contract/test_optimizer_failure_response_contract.py
```

Contract Test는 내부 구현 방식보다 Backend와 약속한 응답 필드를 우선 검증합니다.

### UNKNOWN 실패 응답

```text
request_type = monthly_plan
success = False
failure_reason = optimizer_unknown
optimizer.solver_status = UNKNOWN
monthly_plan.days = []
```

### INFEASIBLE 실패 응답

```text
failure_reason = optimizer_infeasible
optimizer.solver_status = INFEASIBLE
```

### Dispatcher 검증

```text
UNKNOWN
→ build_optimizer_unknown_monthly_response()

INFEASIBLE
→ build_optimizer_infeasible_monthly_response()
```

잘못된 Builder가 호출되면 즉시 `AssertionError`가 발생하도록 구성합니다.

### 성공 응답

```text
id 유지
request_type = monthly_plan
success = True
failure_reason = None
```

### 중요성

Optimizer 내부 Policy가 변경되더라도 Backend가 해석하는 다음 계약은 유지되어야 합니다.

```text
success
failure_reason
request_type
monthly_plan
optimizer.solver_status
days
```

<br>

## 10. Optimizer 결과 매핑 테스트

관련 파일:

```text
modeling/tests/optimizer/test_ortools_alternative_menus.py
```

테스트 대상:

```python
build_ortools_monthly_plan()
```

### 대체 메뉴 정상 생성

검증 내용:

```text
OR-Tools 선택 메뉴 유지
대체 메뉴 2개 생성
선택 메뉴 ID 제외
대체 메뉴 ID 중복 방지
```

### 대체 후보 없음

Recommendation에 대표 메뉴만 존재하면:

```json
{
  "alternative_menus": []
}
```

빈 List를 유지하는지 확인합니다.

### 현재 범위

이 테스트는 OR-Tools Solver 자체보다 Solver 결과를 Plan 구조로 변환하는 `result_mapper`의 후처리를 검증합니다.

다음 Solver 핵심 Constraint는 현재 별도 단위 테스트 보강 대상입니다.

```text
각 Slot에 정확히 한 메뉴
월 예산 상한
동일 메뉴 최대 반복
Objective 가중치
Solver Status 처리
```

<br>

## 11. Persona 테스트

관련 파일:

```text
modeling/tests/persona/test_persona_profile_build.py
```

Persona 테스트는 초기 온보딩 데이터를 기반으로 Persona Profile과 후보 Style을 생성하는 흐름의 회귀를 확인합니다.

최신 테스트 이름 확인:

```bash
grep -nE '^def test_|^class Test|assert ' \
  modeling/tests/persona/test_persona_profile_build.py
```

실행:

```bash
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/persona \
  -q
```

Persona Profile Build의 상세 입력과 출력 구조는 다음 문서를 참고합니다.

```text
modeling/services/persona/README.md
modeling/services/profile/README.md
```

<br>

## 12. Fixture

Fixture 위치:

```text
modeling/experiments/fixtures/
```

현재 Fixture:

```text
backend_monthly_plan_request.json
backend_monthly_plan_success_response.json
backend_monthly_plan_failure_response.json
backend_style_candidates_request.json
backend_style_candidates_response.json
```

### 요청 Fixture

```text
backend_monthly_plan_request.json
backend_style_candidates_request.json
```

실제 Backend가 Modeling API에 보내는 요청 구조를 고정합니다.

사용 위치:

```text
API Request Validation Test
API Metrics Test
HTTP Smoke Test
Contract Validation
```

### 응답 Fixture

```text
backend_monthly_plan_success_response.json
backend_monthly_plan_failure_response.json
backend_style_candidates_response.json
```

Backend와 Modeling의 응답 계약을 비교하거나 문서 예시로 사용할 수 있습니다.

### Fixture 사용 원칙

```text
실제 Backend 계약과 최대한 동일하게 유지
테스트 전용 임의 필드 추가 최소화
Secret 포함 금지
실행 결과 전체 Dump를 Fixture로 사용하지 않음
변경 시 Backend 영향 확인
```

### Fixture와 Artifact 차이

```text
Fixture
→ 테스트 입력·기대값으로 Git에 저장
→ 작고 안정적이며 반복 사용

Artifact
→ 실험 실행 결과
→ 크고 실행마다 달라질 수 있음
→ 일반적으로 Git 추적 대상에서 제외하거나 선별 보관
```

<br>

## 13. Monkeypatch 사용

API와 Contract 테스트에서는 실제 외부 Service 호출을 막고 전달 Payload를 검증하기 위해 `monkeypatch`를 사용합니다.

예시:

```python
monkeypatch.setattr(
    server,
    "create_monthly_plan",
    fake_create_monthly_plan,
)
```

### 목적

```text
실제 RAG API 호출 방지
테스트 속도 향상
네트워크 상태와 테스트 분리
Service 전달 Payload 확인
특정 오류를 재현
```

### 주의점

Monkeypatch 기반 테스트가 성공해도 실제 RAG 연결과 Docker 네트워크가 정상이라는 뜻은 아닙니다.

실제 실행 환경은 HTTP Smoke Test로 별도 검증해야 합니다.

<br>

## 14. 전체 Pytest 실행

프로젝트 루트에서 실행합니다.

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests \
  -q
```

### 옵션 설명

```text
ENV=prod
→ 운영 인증·문서 비활성화 조건으로 테스트

MODELING_API_KEY=ci-secret-key
→ 보호 Endpoint 테스트용 Key

PYTHONPATH=modeling
→ api, services, schemas를 최상위 Package처럼 Import

python -m pytest
→ 현재 Python 가상환경의 Pytest 실행

-q
→ 간략한 결과 출력
```

### Cache Provider 비활성화

CI에서는 다음 옵션을 사용할 수 있습니다.

```bash
python -m pytest \
  -q \
  -p no:cacheprovider \
  modeling/tests
```

`.pytest_cache`를 생성하지 않고 테스트합니다.

<br>

## 15. 범주별 테스트 실행

### API 전체

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/api \
  -q
```

### Contract

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/contract \
  -q
```

### Optimizer

```bash
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/optimizer \
  -q
```

### Persona

```bash
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/persona \
  -q
```

### 특정 파일

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/api/test_modeling_api_metrics.py \
  -q
```

### 특정 함수

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/api/test_modeling_api_metrics.py::test_rag_timeout_error_is_recorded \
  -q
```

<br>

## 16. HTTP Smoke Test

관련 파일:

```text
modeling/experiments/contract/run_modeling_api_http_smoke.py
```

Pytest의 `TestClient`가 아니라 `requests`를 이용해 실제 실행 중인 Modeling API Server를 호출합니다.

### 기본 실행

```bash
python \
  modeling/experiments/contract/run_modeling_api_http_smoke.py \
  --base-url http://127.0.0.1:8001 \
  --api-key local-secret-key
```

기본값:

```text
base-url = http://localhost:8001
api-key = local-secret-key
timeout = 60초
monthly fixture = backend_monthly_plan_request.json
```

### Monthly API 생략

외부 RAG 의존성을 피해야 하는 CI에서는 다음 옵션을 사용합니다.

```bash
python \
  modeling/experiments/contract/run_modeling_api_http_smoke.py \
  --base-url http://127.0.0.1:8001 \
  --api-key local-secret-key \
  --skip-monthly
```

<br>

## 17. Smoke Test 검증 범위

### Health Check

```text
GET /health
→ HTTP 200
→ status = ok
→ service = todays-ggini-modeling
```

### 잘못된 API Key

```text
POST /monthly-plan
X-API-Key = wrong-key
→ HTTP 401
```

### Docs 상태

```text
GET /docs

Local
→ 200 가능

Docker / Prod
→ 404 예상
```

Smoke Test는 실행 환경을 모두 지원하기 위해 `200` 또는 `404`를 허용합니다.

### Monthly Plan

허용 상태:

```text
200
→ RAG와 전체 Modeling 파이프라인 성공

504
→ RAG Timeout이 Gateway Timeout으로 정상 분리됨
```

HTTP `200`이면 다음을 추가 검증합니다.

```text
monthly_plan.days 길이 > 0
```

### Smoke Test 성공

모든 검증이 통과하면 다음 메시지가 출력됩니다.

```text
Modeling API HTTP smoke test completed successfully.
```

<br>

## 18. Docker 통합 검증

Docker 통합 테스트는 다음 요소를 함께 확인합니다.

```text
Docker Image Build
Container 실행
Uvicorn 기동
환경 변수 주입
Port Mapping
Health Check
Metrics Endpoint
API Key
HTTP Request
```

### Container 실행

```bash
MODELING_API_KEY=local-secret-key \
docker compose \
  -f docker-compose.modeling.yml \
  up \
  --build \
  -d
```

### Health 확인

```bash
curl -fsS \
  http://127.0.0.1:8001/health \
  | python -m json.tool
```

### Metrics 확인

```bash
curl -fsS \
  -H "X-API-Key: local-secret-key" \
  http://127.0.0.1:8001/metrics
```

### Smoke Test

```bash
python \
  modeling/experiments/contract/run_modeling_api_http_smoke.py \
  --base-url http://127.0.0.1:8001 \
  --api-key local-secret-key
```

### 종료

```bash
docker compose \
  -f docker-compose.modeling.yml \
  down
```

<br>

## 19. CI 테스트 흐름

관련 Workflow:

```text
.github/workflows/modeling-docker-build.yml
```

현재 확인된 주요 단계:

```text
1. RAG 오류 상태 Mapping 독립 실행
2. API Request Validation Pytest
3. API Metrics Pytest
4. Docker Image Build
5. Container 실행
6. /health 확인
7. /metrics 확인
8. HTTP Smoke Test
```

### RAG 오류 Mapping

```bash
python \
  modeling/tests/api/test_modeling_api_rag_error_status.py
```

### API Pytest

```bash
python -m pytest \
  -q \
  -p no:cacheprovider \
  modeling/tests/api/test_modeling_api_request_validation.py \
  modeling/tests/api/test_modeling_api_metrics.py
```

### Container Health

```text
http://localhost:8001/health
```

응답 가능 상태가 될 때까지 반복 확인합니다.

### HTTP Smoke

```text
modeling/experiments/contract/run_modeling_api_http_smoke.py
```

실제 Container를 대상으로 네트워크 수준의 검증을 수행합니다.

### 현재 CI 범위 주의

확인된 Workflow 명령 기준으로 API 테스트는 자동 실행되지만, 모든 `modeling/tests` 디렉터리가 CI에서 실행되는 것은 아닐 수 있습니다.

다음 범주는 별도 전체 Pytest 단계 추가를 검토할 수 있습니다.

```text
contract
optimizer
persona
```

<br>

## 20. Pytest와 Experiment의 차이

### Pytest

목적:

```text
함수 동작
경계값
응답 계약
오류 매핑
회귀 방지
```

특징:

```text
빠른 실행
결과가 결정적이어야 함
네트워크 의존성 최소화
작은 Fixture 사용
Pass / Fail 중심
```

### Experiment Validation

목적:

```text
추천 품질
시나리오별 안정성
Optimizer 성능
정책 비교
가중치 튜닝
```

특징:

```text
실제 또는 Snapshot 후보 사용
실행 시간이 김
JSON / CSV Artifact 생성
Pass / Warning / Fail 분석
여러 지표를 함께 비교
```

### 역할 관계

```text
Pytest 통과
≠ 추천 품질 보장

Experiment 성공
≠ API Contract 안정성 보장
```

두 검증 체계가 모두 필요합니다.

<br>

## 21. Experiment Validation 도구

### Pipeline

```text
run_final_validation_pipeline.py
run_optimizer_full_validation.py
run_optimizer_validation_pipeline.py
```

전체 시나리오 실행, 분석과 Summary 생성을 자동화합니다.

### Runner

```text
run_baseline_mmr.py
run_least_cost_baseline.py
```

MMR 또는 최저가 Baseline을 생성해 Optimizer 결과와 비교합니다.

### Tuning

```text
extract_optimizer_snapshots.py
grid_search_optimizer_tuning.py
replay_optimizer_policy.py
replay_optimizer_snapshots.py
```

동일 Snapshot에 서로 다른 Optimizer Policy를 적용해 결과를 비교합니다.

### Analysis

```text
analyze_cost_distribution.py
analyze_difficulty_component_replay.py
analyze_difficulty_feasibility.py
analyze_final_validation_result.py
analyze_nutrition_outlier_penalty.py
analyze_rag_difficulty_mapping.py
analyze_style_validation_result.py
analyze_tuning_candidates.py
compare_least_cost_vs_ortools.py
compare_rag_request_results.py
compare_validation_summaries.py
evaluate_baseline_result.py
```

실험 결과에서 비용, 난이도, 중복, RAG 품질과 Validation 상태를 추출합니다.

### Contract 도구

```text
run_backend_contract_validation.py
run_modeling_api_http_smoke.py
run_modeling_service_contract_smoke.py
validate_backend_contract_requests.py
validate_backend_contract_responses.py
analyze_shopping_ingredient_coverage.py
```

Backend 요청·응답 구조와 장보기 재료 Coverage를 검증합니다.

<br>

## 22. 테스트 실패 해석

### Import Error

예시:

```text
ModuleNotFoundError: No module named 'services'
```

원인:

```text
PYTHONPATH=modeling 누락
프로젝트 루트가 아닌 위치에서 실행
가상환경 비활성화
```

해결:

```bash
source .venv/bin/activate

PYTHONPATH=modeling \
python -m pytest modeling/tests -q
```

### HTTP 401

확인 항목:

```text
ENV 값
MODELING_API_KEY 값
X-API-Key Header
TestClient가 사용하는 server 전역 변수
```

### HTTP 422

응답 Body의 `detail`에서 다음을 확인합니다.

```text
필드 누락
잘못된 Literal
숫자 범위
허용 목록
List 중복
```

### HTTP 502

```text
RAG 연결 실패
RAG HTTP 오류
RAG 요청 오류
```

### HTTP 504

```text
RAG Read Timeout
외부 Service 응답 지연
```

### Metrics Count 불일치

Prometheus Counter는 Process 전역 상태를 가집니다.

테스트에서 Metric 값을 초기화하거나 테스트 시작 전 기준값을 저장하지 않으면 이전 테스트의 값이 남아 있을 수 있습니다.

### Smoke Test Monthly 실패

```text
200 또는 504는 현재 허용
401은 Key 설정 확인
422는 Fixture Schema 확인
502는 RAG Upstream 확인
500은 Server Log 확인
Connection Refused는 Container와 Port 확인
```

<br>

## 23. 테스트 작성 규칙

### 테스트 이름

```text
test_<대상>_<조건>_<기대결과>
```

예시:

```python
def test_rag_timeout_maps_to_504():
    ...
```

### Arrange · Act · Assert

```python
# Arrange
payload = read_valid_monthly_request()

# Act
response = client.post(
    "/monthly-plan",
    json=payload,
)

# Assert
assert response.status_code == 422
```

### 외부 의존성 격리

단위·API 테스트에서는 실제 RAG 호출을 피합니다.

```text
monkeypatch
fake function
고정 Fixture
```

실제 네트워크는 HTTP Smoke Test에서 검증합니다.

### 명확한 Assertion

가능하면 다음을 함께 확인합니다.

```text
HTTP Status
Response Field
Service 전달 Payload
Failure Reason
Solver Status
List 길이
중복 여부
```

### 테스트용 Secret

실제 운영 Secret을 사용하지 않습니다.

```text
ci-secret-key
metrics-test-key
local-secret-key
```

### Artifact 생성 금지

Pytest는 Repository에 대형 JSON 결과를 생성하지 않도록 합니다.

결과 파일이 필요한 검증은 Experiment 영역에서 수행합니다.

<br>

## 24. 현재 테스트 공백

현재 확인된 테스트 기준으로 다음 영역은 전용 단위 테스트가 부족합니다.

### Profile

```text
목표별 Weight 계산
예산 환산
Cooking Skill Mapping
Diversity Level Mapping
```

### RAG Mapper

```text
가격 Mapping
영양소 누락
재료군 Mapping
Quality Penalty
Nutrition Outlier
```

### Recommendation

```text
각 Score 공식
가중합 Final Score
Soft Constraint
Quality Penalty
정렬 Tie Breaker
```

### MMR 및 Plan

```text
Lambda 경계값 0.4 / 0.6
유사도 경계값 0.6
메뉴명 Prefix 정규화
Jaccard Similarity
최근 Day Window
대표 메뉴 Fallback
대체 메뉴 조건 완화
사용 횟수 1 / 0.5
Plan Summary
Back Payload 경량화
```

### OR-Tools

```text
Slot당 정확히 한 메뉴
월 예산 Constraint
최대 반복 Constraint
Linear Repeat Penalty
Quadratic Repeat Penalty
Protein Bonus Cap
Difficulty Bonus
Nutrition Outlier Penalty
OPTIMAL / FEASIBLE 처리
후보 부족 사전 검사
예산 불가능 사전 검사
Retry 후보 확장
```

### Validation

```text
Style별 Pass / Warning / Fail 경계
Secondary Warning
Duplicate Rate
Difficulty Feasibility
Budget Feasibility
Recommendation Hint
```

<br>

## 25. 권장 보강 순서

### 1순위: OR-Tools Hard Constraint

잘못된 결과가 사용자 예산과 식단 개수에 직접 영향을 주므로 가장 먼저 보강합니다.

```text
월 예산 초과 금지
Slot 누락 금지
반복 상한 초과 금지
```

### 2순위: Recommendation Score

가중치 또는 필드 Source 변경 시 전체 결과가 달라지므로 Score별 단위 테스트가 필요합니다.

### 3순위: MMR·유사도 경계

```text
0.4 / 0.6 Lambda 경계
0.6 유사도 판정
사용 횟수 Penalty
```

### 4순위: Plan Summary와 Payload

Backend 계약과 Validation 입력에 사용되므로 계산 필드와 제거 필드를 고정합니다.

### 5순위: Style Validation Threshold

Threshold 변경이 Pass·Warning·Fail 결과에 미치는 영향을 명시적으로 검증합니다.

### 6순위: Optimizer Retry

추가 RAG 후보 요청, 병합, 재추천과 재실행을 Mock 기반 통합 테스트로 검증합니다.

<br>

## 26. 관련 문서

### Repository 문서

- [`../README.md`](../README.md)  
  Modeling 전체 아키텍처, 실행과 검증 방법

- [`../api/README.md`](../api/README.md)  
  FastAPI Endpoint, 인증, 오류 처리와 Prometheus Metrics

- [`../services/persona/README.md`](../services/persona/README.md)  
  Persona Profile Build 로직

- [`../services/optimizer/README.md`](../services/optimizer/README.md)  
  OR-Tools Constraint, Objective와 Retry 정책

- [`../services/plan/README.md`](../services/plan/README.md)  
  MMR, 대체 메뉴, Plan Summary와 Payload

- [`../experiments/README.md`](../experiments/README.md)  
  Scenario, Replay, Pipeline과 Artifact 관리

- [`../deploy/README.md`](../deploy/README.md)  
  Docker Build, CI, EC2 배포와 운영 검증

### Contract 및 운영 가이드

- [`../docs/modeling_serving_guide.md`](../docs/modeling_serving_guide.md)  
  로컬·Docker Modeling API 실행 및 Smoke Test

- [`../docs/backend_modeling_api_client_guide.md`](../docs/backend_modeling_api_client_guide.md)  
  Backend 요청 Header, Timeout과 API 계약

- [`../docs/modeling_serving_pr_checklist.md`](../docs/modeling_serving_pr_checklist.md)  
  서빙 코드 PR 전 확인 항목
