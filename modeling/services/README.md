# 🧩 Modeling Services

오늘의 끼니 Modeling 영역의 서비스 계층과 전체 데이터 흐름을 설명하는 인덱스 문서입니다.

각 하위 Service는 사용자 입력 가공, RAG 후보 수집, 추천 점수 계산, 식단 Style 적용, OR-Tools 최적화와 월간 Plan 생성처럼 하나의 책임을 담당합니다.

`modeling_service.py`는 이 Service들을 요청 목적에 맞게 조합하는 Orchestrator 역할을 합니다.

```text
API Request
    ↓
Modeling Service Orchestrator
    ↓
Profile / Persona
    ↓
RAG Candidate Retrieval
    ↓
Recommendation Scoring
    ↓
Style Selection
    ↓
Optimizer
    ↓
Plan / Validation / Payload
    ↓
Backend Response
```

<br>

## 목차

1. [Services 계층 역할](#1-services-계층-역할)
2. [전체 데이터 흐름](#2-전체-데이터-흐름)
3. [디렉터리 구조](#3-디렉터리-구조)
4. [Modeling Service Orchestrator](#4-modeling-service-orchestrator)
5. [Data Service](#5-data-service)
6. [Persona Service](#6-persona-service)
7. [Profile Service](#7-profile-service)
8. [RAG Service](#8-rag-service)
9. [Recommendation Service](#9-recommendation-service)
10. [Style Service](#10-style-service)
11. [Optimizer Service](#11-optimizer-service)
12. [Plan Service](#12-plan-service)
13. [Persona Profile 생성 흐름](#13-persona-profile-생성-흐름)
14. [Meal Style Candidates 생성 흐름](#14-meal-style-candidates-생성-흐름)
15. [Monthly Plan 생성 흐름](#15-monthly-plan-생성-흐름)
16. [후보 부족과 Fallback](#16-후보-부족과-fallback)
17. [Optimizer 실패 처리](#17-optimizer-실패-처리)
18. [데이터 전달 구조](#18-데이터-전달-구조)
19. [Service 간 의존성](#19-service-간-의존성)
20. [실행 및 테스트](#20-실행-및-테스트)
21. [새 Service 추가 원칙](#21-새-service-추가-원칙)
22. [현재 구조상 주의사항](#22-현재-구조상-주의사항)
23. [관련 문서](#23-관련-문서)

<br>

## 1. Services 계층 역할

Services 계층은 API 요청을 실제 Modeling 결과로 변환하는 비즈니스 로직을 담당합니다.

주요 책임:

```text
사용자 입력 정규화
Persona 후보 생성
Modeling Profile 계산
외부 RAG 후보 요청
RAG 응답 Mapping 및 품질 검증
메뉴 적합도 점수 계산
식단 Style 후보 생성
선택 Style의 가중치 적용
OR-Tools 월간 조합 최적화
MMR 기반 다양성 후처리
월간 Plan Summary 및 Validation
Backend 전달용 Payload 생성
```

API 계층은 요청 검증과 HTTP 처리를 담당하고, 실제 도메인 로직은 Services 계층으로 위임합니다.

<br>

## 2. 전체 데이터 흐름

```text
Front / Backend 입력
        ↓
API Schema Validation
        ↓
modeling_service.py
        ↓
Profile 생성
        ↓
RAG Request 생성
        ↓
외부 후보 메뉴 조회
        ↓
RAG Response Mapping
        ↓
Recommendation Score 계산
        ↓
Style 가중치 적용
        ↓
Optimizer Input 생성
        ↓
OR-Tools Solver
        ↓
Plan Mapping 및 대체 메뉴
        ↓
Summary / Validation
        ↓
Backend Payload 경량화
```

서비스별 핵심 흐름:

```text
Persona
→ 초기 온보딩 조건을 Persona 후보로 변환

Profile
→ 사용자 입력을 추천 계산용 수치 Profile로 변환

RAG
→ 외부 메뉴 후보를 요청하고 Modeling Menu로 Mapping

Recommendation
→ 메뉴별 적합도 점수와 추천 이유 생성

Style
→ 후보 Style 생성 및 선택 Style의 Weight 적용

Optimizer
→ 월간 Slot에 메뉴를 제약 기반으로 배치

Plan
→ 식단 구조, 대체 메뉴, Summary와 응답 Payload 생성
```

<br>

## 3. 디렉터리 구조

```text
modeling/
└── services/
    ├── __init__.py
    ├── modeling_service.py
    │
    ├── data/
    │   └── menu_data_service.py
    │
    ├── persona/
    │   ├── persona_catalog.py
    │   ├── persona_service.py
    │   └── README.md
    │
    ├── profile/
    │   ├── profile_service.py
    │   ├── user_input_service.py
    │   ├── weight_service.py
    │   └── README.md
    │
    ├── rag/
    │   ├── rag_client.py
    │   ├── rag_request_service.py
    │   ├── rag_response_mapper.py
    │   ├── rag_candidate_diagnostics.py
    │   ├── ingredient_group_mapper.py
    │   └── README.md
    │
    ├── recommendation/
    │   ├── recommendation_service.py
    │   ├── scoring_service.py
    │   └── README.md
    │
    ├── style/
    │   ├── meal_style_service.py
    │   ├── style_selection_service.py
    │   └── README.md
    │
    ├── optimizer/
    │   ├── optimizer_input_builder.py
    │   ├── optimizer_metrics_service.py
    │   ├── baselines/
    │   ├── ortools/
    │   └── README.md
    │
    ├── plan/
    │   ├── mmr_service.py
    │   ├── menu_similarity_service.py
    │   ├── meal_selector_service.py
    │   ├── period_plan_service.py
    │   ├── plan_summary_service.py
    │   ├── plan_validation_service.py
    │   ├── plan_payload_service.py
    │   └── README.md
    │
    └── README.md
```

### Service별 대표 역할

| Service | 역할 |
|---|---|
| `data` | 로컬 메뉴 데이터 조회 |
| `persona` | 초기 온보딩 기반 Persona 후보 생성 |
| `profile` | 추천 계산용 사용자 Profile 생성 |
| `rag` | 후보 메뉴 요청, Mapping 및 품질 진단 |
| `recommendation` | 메뉴 적합도 점수와 이유 생성 |
| `style` | 식단 Style 후보 생성과 선택 Style 반영 |
| `optimizer` | OR-Tools 기반 월간 조합 최적화 |
| `plan` | MMR, 대체 메뉴, Summary, Validation, Payload |

<br>

## 4. Modeling Service Orchestrator

관련 파일:

```text
modeling/services/modeling_service.py
```

이 파일은 각 도메인 Service를 순서대로 호출하고 성공·실패 응답을 조립합니다.

주요 공개 진입 함수:

```python
create_persona_profile(request_data: dict) -> dict

create_meal_style_candidates(request_data: dict) -> dict

create_monthly_plan(request_data: dict) -> dict
```

### Orchestrator의 책임

```text
요청 목적에 맞는 Service 선택
Profile 생성
RAG 후보 요청
후보 부족 진단 및 추가 요청
Recommendation 실행
Optimizer 실행
Solver 재시도
Plan 및 Validation 생성
실패 응답 유형 결정
최종 Payload 반환
```

### Orchestrator에 포함된 보조 기능

```text
예산 실현 가능성 진단
Optimizer Input Snapshot 생성
Style 후보 Fallback Profile 생성
월간 후보 Fallback Profile 생성
후보 없음 응답 생성
후보 부족 응답 생성
예산 불가능 응답 생성
Optimizer INFEASIBLE 안내 생성
Optimizer UNKNOWN 응답 생성
```

`modeling_service.py`는 비즈니스 흐름을 연결하지만, 개별 계산 공식은 하위 Service로 위임하는 구조입니다.

<br>

## 5. Data Service

관련 파일:

```text
modeling/services/data/menu_data_service.py
```

Data Service는 로컬 파일 또는 내부 데이터 Source에서 메뉴 데이터를 읽는 역할을 담당합니다.

현재 주요 서비스 흐름은 외부 RAG 후보를 사용하지만, 다음 용도로 로컬 데이터 Service를 활용할 수 있습니다.

```text
샘플 실행
로컬 개발
Baseline 실험
RAG 장애 시 제한된 Fallback
정적 Fixture 기반 검증
```

Data Service가 실제 운영 월간 흐름에서 사용되는지는 `modeling_service.py`의 호출 경로를 기준으로 판단해야 합니다.

<br>

## 6. Persona Service

관련 디렉터리:

```text
modeling/services/persona/
```

대표 진입 함수:

```python
build_persona_profile_response(
    request_data: dict[str, Any]
) -> dict[str, Any]
```

주요 처리:

```text
활동량 정규화
가구원 수 구간 계산
한 끼 예산 Band 계산
가구원별 BMR 계산
목표별 권장 칼로리 보정
가구 전체 권장 칼로리 계산
Persona Catalog와 조건 비교
Persona Match Score 계산
상위 Persona 후보 생성
```

대표 함수:

```text
normalize_activity_level()
get_family_count_group()
get_meal_budget_band()
calculate_bmr()
apply_goal_calorie_adjustment()
calculate_member_recommended_calorie()
calculate_recommended_calories()
calculate_persona_match_score()
build_persona_candidates()
```

상세 문서:

```text
modeling/services/persona/README.md
```

<br>

## 7. Profile Service

관련 디렉터리:

```text
modeling/services/profile/
```

대표 진입 함수:

```python
build_user_profile(
    user_input: UserProfileInput
) -> dict
```

주요 처리:

```text
월 예산을 한 끼 예산으로 환산
목표별 Weight 계산
조리 실력 Mapping
다양성 강도 Mapping
기간과 식사 수 정규화
추천 계산용 파생 값 생성
```

대표 함수:

```text
get_weights_by_goals()
get_diversity_penalty_strength()
build_user_profile()
build_user_profile_response()
```

Profile 결과에는 다음과 같은 계산값이 포함될 수 있습니다.

```text
meal_budget
weights
max_difficulty
diversity_penalty_strength
budget_period_days
sample_period_days
period_days
```

상세 문서:

```text
modeling/services/profile/README.md
```

<br>

## 8. RAG Service

관련 디렉터리:

```text
modeling/services/rag/
```

RAG Service는 외부 추천 API와 Modeling 내부 Menu 구조 사이의 Adapter 역할을 합니다.

### 요청 생성

대표 함수:

```python
build_rag_request(...)
calculate_candidate_count(...)
```

사용자 Profile과 필요 식사 수를 바탕으로 외부 RAG 요청 Payload와 후보 수를 계산합니다.

### 외부 API 호출

대표 함수:

```python
request_candidate_menus_from_rag(
    rag_request: dict
) -> dict
```

외부 호출 실패는 `RagRequestError`로 변환됩니다.

### 응답 Mapping

대표 함수:

```python
map_rag_response_to_candidate_menus(
    rag_response: dict
) -> list[dict]
```

주요 처리:

```text
메뉴 필드 정규화
가격 계산
상품 가격 이상치 제거
재료 사용량 단위 변환
조리 난이도 계산
재료군 추론
영양 이상치 분석
RAG 품질 점수 계산
후보 유효성 검증
```

### 후보 진단

대표 함수:

```text
diagnose_monthly_candidate_pool()
calculate_additional_candidate_count()
merge_candidate_menus()
```

후보 수, 고유 메뉴 수와 반복 가능성을 진단하고 추가 후보 요청량을 계산합니다.

상세 문서:

```text
modeling/services/rag/README.md
```

<br>

## 9. Recommendation Service

관련 디렉터리:

```text
modeling/services/recommendation/
```

대표 진입 함수:

```python
recommend_menus(
    menus: list,
    profile: dict,
    top_n: int = 5
) -> list
```

각 후보 메뉴에 다음 점수를 계산합니다.

```text
budget
nutrition
preference
difficulty
diversity
```

주요 처리:

```text
알레르기·제외 재료 필터
개별 Score 계산
Profile Weight 적용
Style Soft Constraint
RAG 품질 감점
영양 누락 감점
영양 이상치 감점
Final Score 계산
추천 이유 생성
점수 순 정렬
```

대표 함수:

```text
calculate_budget_score()
calculate_nutrition_score()
calculate_preference_score()
calculate_difficulty_score()
calculate_diversity_score()
calculate_style_soft_constraint_score()
calculate_final_score()
build_recommendation_reasons()
```

상세 문서:

```text
modeling/services/recommendation/README.md
```

<br>

## 10. Style Service

관련 디렉터리:

```text
modeling/services/style/
```

Style Service는 두 가지 역할을 담당합니다.

```text
식단 Style 후보 생성
사용자가 선택한 Style을 월간 Profile에 적용
```

### Style 후보 생성

대표 함수:

```python
build_meal_style_candidates(...)
```

주요 처리:

```text
사용자 목표별 Style Meta 선택
Style별 Weight 강화
Style 전용 Recommendation 실행
Sample Plan 생성
표시용 점수 계산
메뉴 중복 완화
```

### 선택 Style 반영

대표 함수:

```python
apply_selected_style_to_profile(...)
```

주요 처리:

```text
선택 Style 요약
Weight 재정규화
Nutrition Detail Weight 적용
selected_style_goal 기록
focus_key 반영
```

상세 문서:

```text
modeling/services/style/README.md
```

<br>

## 11. Optimizer Service

관련 디렉터리:

```text
modeling/services/optimizer/
```

대표 흐름:

```text
Recommendation 후보
→ Optimizer 후보 선택
→ Optimizer Config 생성
→ Slot·Menu Input 생성
→ OR-Tools Solver 실행
→ Solver 결과 Mapping
```

### Input Builder

대표 함수:

```python
build_optimizer_input(...)
```

주요 처리:

```text
고유 메뉴 병합
Optimizer 후보 수 제한
난이도 Score 원천 통일
환경 변수 Tuning Override
월 예산과 반복 상한 설정
Objective Weight 구성
```

### OR-Tools Solver

대표 함수:

```python
solve_monthly_plan_with_ortools(
    optimizer_input: dict
) -> dict
```

Hard Constraint:

```text
각 Slot에 정확히 한 메뉴
동일 메뉴 최대 반복 수
월 예산 상한
```

Objective:

```text
Recommendation Score
- Cost Penalty
- Repeat Penalty
+ Protein Bonus
+ Difficulty Bonus
- Nutrition Outlier Penalty
```

### 실패 Policy

대표 함수:

```text
build_optimizer_infeasible_policy()
build_optimizer_infeasible_user_guidance_from_policy()
```

INFEASIBLE 발생 시 활성 Constraint와 완화 가능 Action을 진단합니다.

### Baseline

```text
least_cost_baseline.py
```

최저가 중심 결과를 OR-Tools 결과와 비교하는 실험용 Baseline을 제공합니다.

상세 문서:

```text
modeling/services/optimizer/README.md
```

<br>

## 12. Plan Service

관련 디렉터리:

```text
modeling/services/plan/
```

Plan Service는 선택된 메뉴들을 사용자가 사용할 수 있는 기간별 식단 구조로 변환합니다.

주요 처리:

```text
MMR 재랭킹
메뉴 유사도 계산
최근 노출 메뉴 관리
대표 메뉴 선택
대체 메뉴 선택
Day / Meal 구조 생성
비용·영양 Summary 계산
Style Validation
Backend Payload 경량화
```

대표 함수:

```text
rerank_menus_by_mmr()
calculate_menu_similarity_score()
select_menu_for_meal()
select_alternative_menus()
build_period_meal_plan()
calculate_monthly_plan_summary()
build_style_validation()
enrich_style_validation()
build_modeling_to_back_monthly_response()
```

### OR-Tools 경로

대표 메뉴는 Solver가 결정하고 Plan에서는 대체 메뉴와 응답 구조를 추가합니다.

```text
OR-Tools selected_items
→ build_ortools_monthly_plan()
→ 대체 메뉴
→ Summary
→ Validation
```

### 비-OR-Tools 경로

```text
Recommendation 후보
→ MMR
→ Style Priority
→ 대표 메뉴
→ 대체 메뉴
→ Period Plan
```

상세 문서:

```text
modeling/services/plan/README.md
```

<br>

## 13. Persona Profile 생성 흐름

API 또는 내부 호출:

```python
create_persona_profile(request_data)
```

전체 흐름:

```text
가구 및 가구원 입력
        ↓
Persona Request 조건 생성
        ↓
가구원별 BMR 계산
        ↓
목표별 권장 칼로리 보정
        ↓
Persona Catalog 비교
        ↓
Match Score 계산
        ↓
상위 Persona 후보 반환
```

결과에는 Persona 후보와 계산된 권장 칼로리 정보가 포함될 수 있습니다.

<br>

## 14. Meal Style Candidates 생성 흐름

진입 함수:

```python
create_meal_style_candidates(request_data)
```

전체 흐름:

```text
사용자 Profile 입력
        ↓
build_user_profile()
        ↓
목표 기반 Style Meta 생성
        ↓
Style별 Profile Weight 적용
        ↓
RAG 후보 요청
        ↓
후보 부족 시 Fallback Profile 재요청
        ↓
RAG Mapping
        ↓
Style별 Recommendation
        ↓
다양한 Sample Menu 선택
        ↓
Sample Plan 및 표시 점수 생성
        ↓
Meal Style Candidates 응답
```

이 단계는 월간 식단을 확정하지 않고 사용자가 선택할 Style 후보를 제공합니다.

<br>

## 15. Monthly Plan 생성 흐름

진입 함수:

```python
create_monthly_plan(request_data)
```

전체 흐름:

```text
요청 Profile 검증 완료
        ↓
Base Profile 생성
        ↓
선택 Style 적용
        ↓
Monthly Profile 생성
        ↓
RAG 후보 요청
        ↓
후보 Mapping 및 품질 진단
        ↓
Recommendation 실행
        ↓
Optimizer Input 생성
        ↓
예산·후보 실현 가능성 사전 진단
        ↓
OR-Tools 실행
        ↓
필요 시 후보 확장 및 Retry
        ↓
OR-Tools 결과를 Plan으로 Mapping
        ↓
Plan Summary
        ↓
Style Validation
        ↓
Difficulty Feasibility 진단
        ↓
Backend Payload 변환
```

핵심 호출 위치:

```text
recommend_menus()
solve_monthly_plan_with_ortools()
build_ortools_monthly_plan()
build_style_validation()
build_modeling_to_back_monthly_response()
```

<br>

## 16. 후보 부족과 Fallback

Modeling Service는 후보가 부족하거나 없는 상황을 별도로 처리합니다.

### Style 후보 Fallback

```python
build_style_candidate_fallback_profiles(
    profile: dict
) -> list[tuple[str, dict]]
```

Style Candidate 생성 단계에서 RAG 결과가 부족하면 조건을 점진적으로 완화한 Profile로 재요청할 수 있습니다.

### Monthly 후보 Fallback

```python
build_monthly_candidate_fallback_profiles(...)
```

월간 식단에 필요한 후보 수가 부족하면 다음과 같은 완화가 사용될 수 있습니다.

```text
선호 카테고리 완화
선호 재료군 확장
다양성 수준 완화
요청 후보 수 증가
```

### 후보 없음 응답

```python
build_candidate_empty_monthly_response(...)
```

유효한 후보가 전혀 없으면 Solver를 실행하지 않고 명시적인 실패 응답을 생성합니다.

### 후보 부족 응답

```python
build_candidate_insufficient_monthly_response(...)
```

후보 수와 반복 상한으로 필요한 식사 수를 채울 수 없으면 별도 실패 원인을 반환합니다.

<br>

## 17. Optimizer 실패 처리

Optimizer 실패 상태는 같은 오류로 합치지 않고 원인별로 분리합니다.

### 예산 절대 불가능

```python
build_budget_infeasible_monthly_response(...)
```

최저 비용 후보만 사용해도 월 예산을 초과하면 Solver 실행 전 실패할 수 있습니다.

### INFEASIBLE

```python
build_optimizer_infeasible_monthly_response(...)
```

제약 조건을 만족하는 해가 없을 때 사용합니다.

### UNKNOWN

```python
build_optimizer_unknown_monthly_response(...)
```

제한 시간 내 해를 찾지 못했거나 Solver 상태가 불명확할 때 사용합니다.

### Dispatcher

```python
build_optimizer_failure_monthly_response(...)
```

Solver Status에 따라 적절한 실패 Builder를 선택합니다.

대표 Failure Reason:

```text
candidate_empty
candidate_insufficient
budget_infeasible
optimizer_infeasible
optimizer_unknown
```

Backend가 실패 유형을 구분할 수 있도록 `success`, `failure_reason`, `monthly_plan.optimizer` 구조를 유지합니다.

<br>

## 18. 데이터 전달 구조

### User Input

```text
API Request
→ UserProfileRequest
→ UserProfileInput
```

주요 입력:

```text
goals
monthly_budget
meal_count_per_day
cooking_skill
preferred_categories
diversity_level
ingredient_preferences
allergy_ingredients
period_days
```

### Modeling Profile

Profile Service가 계산한 내부 구조입니다.

```text
meal_budget
weights
max_difficulty
diversity_penalty_strength
selected_style_goal
nutrition_detail_weights
```

### RAG Candidate

외부 응답을 Mapping하기 전의 원본 후보입니다.

### Modeling Menu

RAG Mapper와 Recommendation을 거친 내부 메뉴 구조입니다.

```text
가격
영양 정보
재료
조리 난이도
RAG 품질 진단
개별 Score
Final Score
추천 이유
```

### Optimizer Input

```text
slots
candidate_menus
monthly_budget
max_repeat_per_menu
solver_time_limit_seconds
objective weights
```

### Monthly Plan

```text
period_days
meal_count_per_day
optimizer
warnings
fallback
summary
style_validation
days
```

### Backend Response

내부 진단 필드를 줄이고 화면 및 저장에 필요한 필드를 유지합니다.

```text
id
request_type
success
failure_reason
selected_style
meta
modeling_profile
applied_style_adjustment
monthly_plan
```

<br>

## 19. Service 간 의존성

주요 의존 방향:

```text
modeling_service
 ├── persona
 ├── profile
 ├── rag
 ├── recommendation
 ├── style
 ├── optimizer
 └── plan
```

세부 의존:

```text
Recommendation
→ Profile Weight와 RAG Mapping 결과 사용

Style
→ Recommendation과 Plan Sample 생성 사용

Optimizer
→ Recommendation 결과 사용

Plan
→ Recommendation 또는 Optimizer 결과 사용

Validation
→ Plan Summary와 후보 Diagnostics 사용
```

### 권장 의존 원칙

```text
하위 Service가 modeling_service를 Import하지 않음
도메인 Service 간 순환 Import 금지
API 객체를 Service 내부로 전달하지 않음
Service 함수는 dict 또는 명시적 Model을 입력받음
외부 네트워크 호출은 RAG Client에 집중
최종 HTTP Status 처리는 API 계층에서 담당
```

<br>

## 20. 실행 및 테스트

프로젝트 루트에서 실행합니다.

### 전체 테스트

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests \
  -q
```

### Persona

```bash
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/persona \
  -q
```

### Optimizer

```bash
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/optimizer \
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

### API

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/api \
  -q
```

### 주요 Service 문법 검사

```bash
python -m py_compile \
  modeling/services/modeling_service.py \
  modeling/services/persona/persona_service.py \
  modeling/services/profile/profile_service.py \
  modeling/services/rag/rag_client.py \
  modeling/services/rag/rag_response_mapper.py \
  modeling/services/recommendation/recommendation_service.py \
  modeling/services/style/meal_style_service.py \
  modeling/services/optimizer/optimizer_input_builder.py \
  modeling/services/optimizer/ortools/monthly_plan_optimizer.py \
  modeling/services/plan/period_plan_service.py \
  modeling/services/plan/plan_payload_service.py
```

<br>

## 21. 새 Service 추가 원칙

### 책임을 하나로 제한

예시:

```text
가격 계산
→ RAG Mapper 또는 별도 Pricing Service

HTTP 오류 반환
→ API 계층

월간 조합 최적화
→ Optimizer

응답 필드 경량화
→ Plan Payload Service
```

한 Service에 네트워크, 점수 계산, HTTP 응답 생성을 모두 넣지 않습니다.

### 대표 진입 함수 제공

외부 Module이 내부 보조 함수를 여러 개 조합하지 않도록 대표 함수를 제공합니다.

```python
def process_domain_request(...) -> dict:
    ...
```

### 순수 함수 우선

가능하면 입력값을 변경하지 않고 새 결과를 반환합니다.

```text
입력 dict 직접 수정 최소화
전역 상태 최소화
환경 변수 접근 위치 제한
```

### 오류 책임 분리

```text
외부 API 오류
→ Domain Exception

HTTP Status 변환
→ api/server.py
```

### README 갱신

새 Service를 추가하면 다음도 함께 수정합니다.

```text
modeling/services/README.md
modeling/README.md
관련 테스트
관련 Architecture Diagram
```

<br>

## 22. 현재 구조상 주의사항

### `modeling_service.py`가 큼

현재 Orchestrator에는 다음 로직이 함께 존재합니다.

```text
후보 진단
Fallback Profile 생성
실패 응답 Builder
Optimizer Retry
Profiling
최종 흐름 제어
```

기능이 더 늘어나면 다음 단위로 분리할 수 있습니다.

```text
candidate_fallback_service.py
optimizer_retry_service.py
failure_response_service.py
pipeline_profiling_service.py
```

단, 현재 흐름을 충분히 이해하지 않은 상태에서 단순히 파일만 분리하면 추적이 더 어려워질 수 있으므로 책임 경계를 먼저 확정해야 합니다.

### Plan에 유사 기능 파일이 여러 개 존재

현재 다음 파일들에 유사도·다양성 관련 기능이 중복되어 있습니다.

```text
mmr_service.py
menu_similarity_service.py
menu_diversity_service.py
diversity_service.py
```

실제 현재 흐름은 주로 다음 조합을 사용합니다.

```text
mmr_service.py
menu_similarity_service.py
meal_selector_service.py
period_plan_service.py
```

`menu_diversity_service.py`와 `diversity_service.py`가 레거시 또는 별도 경로인지 호출 위치를 확인한 뒤 정리해야 합니다.

확인 명령:

```bash
grep -RInE \
  --include='*.py' \
  --exclude-dir='__pycache__' \
  'menu_diversity_service|diversity_service' \
  modeling \
  | grep -v README
```

사용되지 않는 코드라면 즉시 삭제하기보다 다음 순서가 안전합니다.

```text
호출 경로 확인
실험 Script 의존성 확인
테스트 추가
Deprecated 표시
후속 PR에서 제거
```

### `meal_candidate_service.py` 존재

`meal_candidate_service.py`의 `select_menu_candidates_for_slot()`이 현재 OR-Tools 또는 기존 Plan 경로에서 사용하는지 확인이 필요합니다.

```bash
grep -RIn \
  --include='*.py' \
  --exclude-dir='__pycache__' \
  'select_menu_candidates_for_slot' \
  modeling \
  | grep -v README
```

### Data Service 문서 없음

`services/data`에는 별도 README가 없습니다.

현재 기능이 작고 `services/README.md`에서 설명 가능하므로 반드시 별도 문서를 만들 필요는 없습니다.

Data Service가 운영 Fallback, Cache 또는 DB Adapter로 확대되면 별도 README를 추가하는 것이 좋습니다.

### Dictionary 기반 경계가 많음

Service 간 입력과 반환이 대부분 `dict`이므로 다음 문제가 발생할 수 있습니다.

```text
필드 오타를 실행 시점까지 발견하기 어려움
Optional 필드의 의미 불명확
Service별 기대 구조 추적 어려움
```

외부 API 경계는 Pydantic Model을 사용하고 있지만 내부 주요 경계에도 TypedDict, dataclass 또는 Pydantic Model을 단계적으로 도입할 수 있습니다.

### 환경 변수 접근 위치

Optimizer Tuning Override와 RAG URL 등 일부 설정은 Service 내부에서 직접 환경 변수를 읽습니다.

환경 설정이 늘어나면 공통 Settings 객체로 통합하는 것이 좋습니다.

### Retry가 외부 호출을 증가시킴

후보 부족 또는 Solver 실패 시 RAG를 추가 호출하므로 다음 영향이 있습니다.

```text
응답 지연 증가
외부 API 부하 증가
Timeout 가능성 증가
비용 증가
```

Retry 횟수와 후보 확대량은 Metrics 및 Profiling으로 지속 관찰해야 합니다.

### 실험 코드와 운영 코드 경계

`experiments`는 운영 Service를 Import해 정책을 Replay하지만, 운영 Service가 `experiments`를 Import해서는 안 됩니다.

권장 방향:

```text
experiments → services
services -X→ experiments
```

<br>

## 23. 관련 문서

### Service 상세 문서

- [`persona/README.md`](persona/README.md)  
  가구원 정보, BMR, 권장 칼로리와 Persona 후보 생성

- [`profile/README.md`](profile/README.md)  
  사용자 입력 정규화, 예산 환산과 Weight 계산

- [`rag/README.md`](rag/README.md)  
  RAG 요청, 응답 Mapping, 가격·난이도·품질 진단

- [`recommendation/README.md`](recommendation/README.md)  
  메뉴별 Score, Final Score, Soft Constraint와 추천 이유

- [`style/README.md`](style/README.md)  
  Style 후보 생성, 선택 Style 적용과 Validation

- [`optimizer/README.md`](optimizer/README.md)  
  OR-Tools Input, Constraint, Objective, Retry와 실패 Policy

- [`plan/README.md`](plan/README.md)  
  MMR, 메뉴 유사도, 대체 메뉴, Summary와 Payload

### 상위 문서

- [`../README.md`](../README.md)  
  Modeling 전체 아키텍처와 실행 흐름

- [`../api/README.md`](../api/README.md)  
  FastAPI Endpoint, 인증, 오류 처리와 Metrics

- [`../tests/README.md`](../tests/README.md)  
  단위·API·Contract·Smoke Test 전략

- [`../experiments/README.md`](../experiments/README.md)  
  Scenario, Replay, Tuning과 Validation Pipeline

- [`../deploy/README.md`](../deploy/README.md)  
  Docker, CI/CD, EC2, Nginx와 Monitoring
