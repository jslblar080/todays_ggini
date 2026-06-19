# Modeling ↔ Backend Contract Validation

## 목적

Backend에서 Modeling 파이프라인을 호출할 때 사용하는 request 구조가 Modeling schema와 호환되는지 검증한다.
이 도구는 Backend 코드를 직접 실행하거나 수정하지 않고, Modeling 담당 범위에서 연동 계약을 검증하기 위한 용도다.

## 검증 대상

- ai/modeling/experiments/fixtures/backend_style_candidates_request.json
- ai/modeling/experiments/fixtures/backend_monthly_plan_request.json

## 검증 내용

1. 3일치 스타일 후보 생성 request가 UserProfileRequest schema와 호환되는지 확인
2. 월간 식단 생성 request가 UserProfileRequest schema와 호환되는지 확인
3. 월간 식단 생성 request에 selected_style 필드가 존재하는지 확인
4. selected_style에 필수 필드가 존재하는지 확인
5. Modeling 진입 함수가 import 가능하고 callable인지 확인

## Modeling 진입 함수

- create_meal_style_candidates(request_data: dict) -> dict
- create_monthly_plan(request_data: dict) -> dict

위 함수는 ai/modeling/services/modeling_service.py에 위치한다.

## 실행 방법

프로젝트 루트에서 아래 명령어를 실행한다.

PYTHONPATH=ai/modeling python ai/modeling/experiments/contract/validate_backend_contract_requests.py

정상 실행 시 style candidate request, monthly plan request, Modeling service entrypoint 검증이 모두 OK로 출력된다.

## 문법 검사

python -m py_compile ai/modeling/experiments/contract/validate_backend_contract_requests.py

## 주의사항

이 검증은 RAG API를 호출하지 않는다.
실제 식단 생성 결과를 검증하는 테스트가 아니라, Backend가 Modeling으로 전달할 request 구조와 Modeling 진입점이 유효한지만 확인하는 계약 검증 테스트다.

실제 RAG + Optimizer + Validation end-to-end 검증은 별도의 validation pipeline에서 수행한다.

## 담당 범위

### Modeling 담당

- request fixture 관리
- Modeling schema 호환성 검증
- Modeling 진입 함수 유지
- RAG/Optimizer/Validation pipeline 품질 관리

### Backend 담당

- FastAPI router 연결
- 인증 사용자 기반 request body 구성
- Celery/Redis 비동기 처리
- DB 저장 처리
- 프론트 응답 형태 가공
