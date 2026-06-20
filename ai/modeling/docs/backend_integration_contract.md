# Modeling ↔ Backend 연동 계약 문서

## 목적

Backend에서 Modeling 파이프라인을 호출할 때 필요한 요청/응답 구조를 정리한다.

Modeling 담당자는 FastAPI router, DB 저장, Redis/Celery 처리 등 Backend 영역을 직접 수정하지 않고, Backend가 호출할 수 있는 모델링 진입점과 데이터 계약을 제공한다.

## Modeling 진입점

| 용도 | 함수 |
|---|---|
| 3일치 식단 스타일 후보 생성 | create_meal_style_candidates(request_data: dict) -> dict |
| 선택 스타일 기반 월간 식단 생성 | create_monthly_plan(request_data: dict) -> dict |

위 함수는 다음 파일에 있다.

- ai/modeling/services/modeling_service.py

## 1. 3일치 식단 스타일 후보 생성

### 호출 함수

- create_meal_style_candidates(request_data: dict) -> dict

### Request 예시

{
  "id": 1,
  "request_type": "meal_style_candidates",
  "profile": {
    "goals": ["영양 균형"],
    "monthly_budget": 300000,
    "meal_count_per_day": 3,
    "recommended_daily_calories": 2100,
    "cooking_skill": 3,
    "preferred_categories": ["한식"],
    "diversity_level": "보통",
    "ingredient_preferences": ["채소류"],
    "allergy_ingredients": [],
    "sample_period_days": 3
  }
}

### Response 개요

주요 응답 필드는 다음과 같다.

| 필드 | 설명 |
|---|---|
| user_id | 사용자 id |
| request_type | 요청 타입 |
| style_candidates | 스타일 후보 리스트 |
| warnings | 후보 생성 중 발생한 주의사항 |

Backend는 style_candidates 중 사용자가 선택한 항목을 월간 식단 생성 요청의 selected_style로 전달한다.

## 2. 월간 식단 생성

### 호출 함수

- create_monthly_plan(request_data: dict) -> dict

### Request 예시

{
  "id": 1,
  "request_type": "monthly_plan",
  "profile": {
    "goals": ["고단백", "식비 절약", "간편식"],
    "monthly_budget": 250000,
    "meal_count_per_day": 3,
    "recommended_daily_calories": 2200,
    "cooking_skill": 2,
    "preferred_categories": ["한식"],
    "diversity_level": "보통",
    "ingredient_preferences": ["육류"],
    "allergy_ingredients": [],
    "period_days": 30
  },
  "selected_style": {
    "style_id": "high_protein_budget_easy",
    "style_name": "고단백 절약형",
    "source_goal": "고단백",
    "focus_key": "nutrition"
  },
  "use_ortools": true,
  "optimizer_config": {
    "enable_optimizer_retry_fallback": true
  }
}

## 3. selected_style 구조

| 필드 | 설명 |
|---|---|
| style_id | 스타일 식별자 |
| style_name | 사용자에게 보여줄 스타일명 |
| source_goal | 스타일의 기준 목표 |
| focus_key | 검증 및 최적화 기준 키 |

## 4. 옵션 필드

| 필드 | 설명 |
|---|---|
| use_ortools | OR-Tools optimizer 사용 여부 |
| optimizer_config | optimizer 세부 설정 |
| rag_candidate_multiplier | 월간 RAG 후보 요청 배수 override |

권장 optimizer_config는 다음과 같다.

{
  "enable_optimizer_retry_fallback": true
}

## 5. 실패 응답 케이스

| failure_reason | 의미 |
|---|---|
| candidate_empty | RAG 후보 메뉴가 비어 있음 |
| candidate_insufficient | optimizer가 필요한 식사 수를 채울 후보 수가 부족함 |
| budget_infeasible | 예산 조건상 가능한 조합이 없음 |
| optimizer_infeasible | OR-Tools가 feasible solution을 찾지 못함 |

Backend는 failure_reason이 존재할 경우 사용자에게 재입력 또는 조건 완화 안내를 제공할 수 있다.

## 6. Backend 저장 시 참고 필드

| 필드 | 설명 |
|---|---|
| monthly_plan.days | 날짜별 식단 데이터 |
| summary | 전체 요약 |
| style_validation | 선택 스타일 반영 검증 결과 |
| warnings | 생성 과정 경고 |
| fallback | RAG/optimizer fallback 사용 여부 |
| profiling | 단계별 실행 시간 |

## 7. 연동 책임 범위

### Modeling 담당

- 모델링 진입 함수 유지
- request/response 구조 문서화
- 샘플 request/response 제공
- 실험 및 validation 결과 제공

### Backend 담당

- FastAPI router 연결
- 인증 사용자 정보 기반 request 구성
- DB 저장 처리
- Redis/Celery 비동기 처리
- API response schema 확정
