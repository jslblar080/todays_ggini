# Modeling ↔ Backend Contract Validation

## 목적

Backend와 Modeling이 연동될 때 주고받는 request/response 구조가 약속된 형태인지 검증한다.

이 도구는 Backend 코드를 직접 실행하거나 수정하지 않는다.
Modeling 담당 범위에서 Backend 연동 계약을 검증하기 위한 용도다.

## 왜 필요한가

Backend와 Modeling은 서로 다른 파트에서 개발되기 때문에 request/response 필드명이 어긋나면 연동 시점에 오류가 발생할 수 있다.

예를 들어 Backend는 user_id를 보냈는데 Modeling은 id를 기대하거나, Modeling 응답에 monthly_plan.days가 없으면 Backend 저장 로직이 실패할 수 있다.

따라서 fixture와 검증 스크립트를 통해 연동 전에 데이터 구조를 미리 확인한다.

## 검증 대상 fixture

### Request fixture

- ai/modeling/experiments/fixtures/backend_style_candidates_request.json
- ai/modeling/experiments/fixtures/backend_monthly_plan_request.json

### Response fixture

- ai/modeling/experiments/fixtures/backend_style_candidates_response.json
- ai/modeling/experiments/fixtures/backend_monthly_plan_success_response.json
- ai/modeling/experiments/fixtures/backend_monthly_plan_failure_response.json

## 검증 스크립트

- validate_backend_contract_requests.py
- validate_backend_contract_responses.py
- run_backend_contract_validation.py

## 검증 내용

### Request 검증

1. 3일치 스타일 후보 생성 request가 UserProfileRequest schema와 호환되는지 확인
2. 월간 식단 생성 request가 UserProfileRequest schema와 호환되는지 확인
3. 월간 식단 생성 request에 selected_style 필드가 존재하는지 확인
4. selected_style에 필수 필드가 존재하는지 확인
5. Modeling 진입 함수가 import 가능하고 callable인지 확인

### Response 검증

1. 스타일 후보 응답에 user_id, request_type, style_candidates, warnings가 있는지 확인
2. style_candidates 내부에 style_id, style_name, source_goal, focus_key가 있는지 확인
3. 월간 식단 성공 응답에 monthly_plan, summary, style_validation, warnings, fallback, profiling이 있는지 확인
4. monthly_plan.days와 meals 구조가 존재하는지 확인
5. 월간 식단 실패 응답에 success, failure_reason, message가 있는지 확인
6. failure_reason 값이 허용된 실패 사유인지 확인

## Modeling 진입 함수

- create_meal_style_candidates(request_data: dict) -> dict
- create_monthly_plan(request_data: dict) -> dict

위 함수는 ai/modeling/services/modeling_service.py에 위치한다.

## 통합 실행

프로젝트 루트에서 아래 명령어를 실행한다.

python ai/modeling/experiments/contract/run_backend_contract_validation.py

이 스크립트는 request contract와 response contract를 순서대로 검증한다.

## 개별 실행

request contract만 검증하려면 아래 명령어를 실행한다.

PYTHONPATH=ai/modeling python ai/modeling/experiments/contract/validate_backend_contract_requests.py

response contract만 검증하려면 아래 명령어를 실행한다.

python ai/modeling/experiments/contract/validate_backend_contract_responses.py

## 문법 검사

python -m py_compile ai/modeling/experiments/contract/validate_backend_contract_requests.py ai/modeling/experiments/contract/validate_backend_contract_responses.py ai/modeling/experiments/contract/run_backend_contract_validation.py

## 주의사항

이 검증은 RAG API를 호출하지 않는다.

실제 식단 생성 결과를 검증하는 테스트가 아니라, Backend가 Modeling으로 전달할 request 구조와 Modeling이 Backend로 반환할 response 구조가 유효한지만 확인하는 계약 검증 테스트다.

실제 RAG + Optimizer + Validation end-to-end 검증은 별도의 validation pipeline에서 수행한다.

## 담당 범위

### Modeling 담당

- request fixture 관리
- response fixture 관리
- Modeling schema 호환성 검증
- Modeling 진입 함수 유지
- RAG/Optimizer/Validation pipeline 품질 관리

### Backend 담당

- FastAPI router 연결
- 인증 사용자 기반 request body 구성
- Celery/Redis 비동기 처리
- DB 저장 처리
- 프론트 응답 형태 가공
