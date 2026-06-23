# 📅 Monthly Meal Plan & Diversity Control

Recommendation 또는 OR-Tools Optimizer가 제공한 메뉴 후보를 실제 기간별 식단표로 구성하는 모듈입니다.

Plan 모듈은 메뉴를 단순히 순서대로 배치하지 않습니다. MMR 기반 재랭킹, 최근 노출 메뉴 유사도, 사용 횟수, 선택 Style 우선순위와 대체 메뉴 다양성을 함께 고려합니다. 식단 구성 후에는 비용·영양·반복·추천 점수 요약을 계산하고, Style Validation과 Back/Front 전달용 Payload를 생성합니다.

```text
Recommendation 후보
        ↓
MMR 기반 재랭킹
        ↓
Style Priority 적용
        ↓
대표 메뉴 및 대체 메뉴 선택
        ↓
최근 노출 메뉴와 사용 횟수 갱신
        ↓
Day / Meal 구조 생성
        ↓
Plan Summary 계산
        ↓
Style Validation
        ↓
Back/Front Payload 경량화
```

OR-Tools 사용 경로에서는 Solver가 대표 메뉴를 먼저 확정하고, Plan 모듈은 Day 구조와 대체 메뉴를 후처리합니다.

<br>

## 목차

1. [모듈 역할](#1-모듈-역할)
2. [전체 처리 흐름](#2-전체-처리-흐름)
3. [두 가지 Plan 생성 경로](#3-두-가지-plan-생성-경로)
4. [MMR 재랭킹](#4-mmr-재랭킹)
5. [MMR Lambda](#5-mmr-lambda)
6. [Relevance Score](#6-relevance-score)
7. [Similarity Penalty](#7-similarity-penalty)
8. [사용 횟수 Penalty](#8-사용-횟수-penalty)
9. [MMR 정렬 기준](#9-mmr-정렬-기준)
10. [메뉴 유사도 판정](#10-메뉴-유사도-판정)
11. [메뉴명 정규화](#11-메뉴명-정규화)
12. [재료 기반 유사도](#12-재료-기반-유사도)
13. [최근 노출 메뉴 관리](#13-최근-노출-메뉴-관리)
14. [Style Priority](#14-style-priority)
15. [대표 메뉴 선택](#15-대표-메뉴-선택)
16. [대체 메뉴 선택](#16-대체-메뉴-선택)
17. [비-OR-Tools 기간별 Plan 생성](#17-비-or-tools-기간별-plan-생성)
18. [OR-Tools 결과 매핑](#18-or-tools-결과-매핑)
19. [사용 횟수 관리](#19-사용-횟수-관리)
20. [일별 비용과 칼로리](#20-일별-비용과-칼로리)
21. [Plan Summary](#21-plan-summary)
22. [Style Validation 연동](#22-style-validation-연동)
23. [내부 Menu Payload](#23-내부-menu-payload)
24. [Back/Front 전달용 Payload](#24-backfront-전달용-payload)
25. [추천 이유 필터링](#25-추천-이유-필터링)
26. [최종 월간 응답 구조](#26-최종-월간-응답-구조)
27. [경고와 Fallback 정보](#27-경고와-fallback-정보)
28. [실행 및 테스트](#28-실행-및-테스트)
29. [파일 구조](#29-파일-구조)
30. [현재 구현상 주의사항](#30-현재-구현상-주의사항)
31. [관련 문서](#31-관련-문서)

<br>

## 1. 모듈 역할

Plan 모듈의 주요 역할은 다음과 같습니다.

### 메뉴 배치

- 기간과 하루 식사 수에 따라 Day·Meal 구조 생성
- MMR 점수 기반 후보 재정렬
- 선택 Style에 적합한 메뉴 우선 배치
- 최근 노출 메뉴와 유사한 메뉴 반복 억제

### 대체 메뉴 제공

- 대표 메뉴와 다른 후보 제공
- 대표 메뉴와 유사한 메뉴 제외
- 최근 노출 메뉴와 유사한 후보 억제
- 대체 메뉴끼리의 유사성 제거
- 후보 부족 시 일부 조건 완화

### 다양성 관리

- 최근 N일 동안 노출된 대표·대체 메뉴 추적
- 대표 메뉴 사용 횟수 `1` 증가
- 대체 메뉴 사용 횟수 `0.5` 증가
- 메뉴 사용 횟수를 다음 MMR 계산에 반영

### 결과 요약

- 총 비용 및 일평균 비용
- 평균 영양소
- 메뉴 중복 수
- 평균 Recommendation 세부 점수

### 응답 변환

- Modeling 내부 진단 필드 보존
- Back/Front 전달 단계에서는 핵심 필드만 유지
- 선택 Style의 `focus_key`에 맞는 추천 이유 노출

<br>

## 2. 전체 처리 흐름

### 일반 Plan 경로

```text
Recommendation 결과
        ↓
build_period_meal_plan()
        ↓
최근 노출 메뉴 조회
        ↓
select_menu_for_meal()
        ↓
MMR 재랭킹
        ↓
Style Priority 필터·정렬
        ↓
대표 메뉴 선택
        ↓
select_alternative_menus()
        ↓
대표·대체 메뉴 사용 횟수 갱신
        ↓
일자별 비용·칼로리 계산
        ↓
calculate_monthly_plan_summary()
```

### OR-Tools 경로

```text
Recommendation 결과
        ↓
OR-Tools Optimizer
        ↓
대표 메뉴 selected_items 확정
        ↓
build_ortools_monthly_plan()
        ↓
Day·Meal 구조로 변환
        ↓
대표 메뉴별 대체 메뉴 MMR 선택
        ↓
일자별 비용·칼로리 계산
        ↓
calculate_monthly_plan_summary()
```

공통 후처리:

```text
Plan Summary
→ Style Validation
→ Validation 보조 진단
→ Back/Front Payload 변환
→ 최종 monthly_plan 응답
```

<br>

## 3. 두 가지 Plan 생성 경로

현재 Plan 생성에는 두 경로가 존재합니다.

### 비-OR-Tools 경로

관련 함수:

```python
build_period_meal_plan(
    recommendations: list[dict],
    profile: dict,
    period_days: int,
    meal_count_per_day: int,
) -> dict
```

각 Meal Slot에서 MMR와 Style Priority를 이용해 대표 메뉴를 직접 선택합니다.

### OR-Tools 경로

관련 함수:

```python
build_ortools_monthly_plan(
    optimizer_result: dict,
    optimizer_input: dict,
    recommendations: list[dict],
    profile: dict,
) -> dict
```

대표 메뉴는 OR-Tools가 이미 선택한 상태입니다.

Plan Mapper는 다음 작업만 수행합니다.

```text
selected_items를 날짜별로 그룹화
→ meal_order 기준 정렬
→ 대표 메뉴 Payload 생성
→ 대체 메뉴 후처리
→ Summary 계산
```

### 경로별 차이

| 항목 | 비-OR-Tools | OR-Tools |
|---|---|---|
| 대표 메뉴 결정 | MMR + Style Priority | CP-SAT Solver |
| 대체 메뉴 결정 | MMR | MMR |
| 예산 전체 상한 | 별도 Hard Constraint 없음 | OR-Tools Hard Constraint |
| 동일 메뉴 절대 상한 | 없음 | `max_repeat_per_menu` |
| 최근 노출 유사도 | 대표·대체 모두 반영 | 대체 메뉴 후처리에 반영 |
| Summary | 공통 함수 사용 | 공통 함수 사용 |

<br>

## 4. MMR 재랭킹

관련 파일:

```text
modeling/services/plan/mmr_service.py
```

관련 함수:

```python
calculate_mmr_score(
    menu: dict,
    exposed_menus: list[dict],
    used_menu_count: dict,
    diversity_penalty_strength: float,
) -> float
```

MMR 점수는 다음 세 요소를 결합합니다.

```text
1. final_score
   → 사용자 조건에 대한 Recommendation 적합도

2. max_similarity
   → 최근 노출 메뉴 중 가장 유사한 메뉴와의 유사도

3. use_count
   → 해당 menu_id가 이미 사용된 정도
```

전체 계산식:

```text
MMR Score
= final_score × λ
- (max_similarity × 100) × (1 - λ)
- use_count × 8
```

코드 구조:

```python
mmr_score = (
    relevance_score * lambda_score
    - diversity_penalty * (1 - lambda_score)
    - use_count_penalty
)
```

<br>

## 5. MMR Lambda

관련 함수:

```python
get_mmr_lambda(
    diversity_penalty_strength: float,
) -> float
```

`λ`가 높을수록 Recommendation의 `final_score`를 더 중요하게 보고, 낮을수록 기존 노출 메뉴와의 차이를 더 중요하게 봅니다.

| Diversity Penalty Strength | Lambda |
|---:|---:|
| `0.6` 이상 | `0.55` |
| `0.4` 이상 `0.6` 미만 | `0.65` |
| `0.4` 미만 | `0.80` |

### 해석

#### 다양성 강도가 높은 경우

```text
λ = 0.55

Recommendation 적합도 비중 = 55%
유사도 감점 비중 = 45%
```

#### 다양성 강도가 낮은 경우

```text
λ = 0.80

Recommendation 적합도 비중 = 80%
유사도 감점 비중 = 20%
```

`diversity_penalty_strength` 자체를 MMR 공식에 직접 곱하지 않고, 구간별 Lambda로 변환해 적용합니다.

<br>

## 6. Relevance Score

MMR의 Relevance는 Recommendation의 최종 점수를 그대로 사용합니다.

```text
relevance_score
= menu.final_score
```

`final_score`에는 이미 다음 요소가 반영되어 있습니다.

```text
예산 적합도
영양 적합도
선호 적합도
조리 적합도
다양성 점수
Style Soft Constraint
RAG 품질 감점
영양 누락 감점
```

따라서 MMR은 Recommendation 점수를 다시 계산하는 것이 아니라, 기존 적합도와 최근 노출 다양성을 재조정합니다.

<br>

## 7. Similarity Penalty

최근 노출 메뉴들과 현재 후보의 유사도를 모두 계산한 뒤 최댓값을 사용합니다.

```text
max_similarity
= max(
    현재 후보와 각 노출 메뉴의 similarity
)
```

MMR에서 사용하는 감점 기준:

```text
diversity_penalty
= max_similarity × 100
```

최종 감점:

```text
diversity_penalty × (1 - λ)
```

예시:

```text
max_similarity = 0.8
λ = 0.55

Similarity Penalty
= 0.8 × 100 × 0.45
= 36
```

노출 메뉴가 없다면 `max_similarity`는 `0`입니다.

<br>

## 8. 사용 횟수 Penalty

동일 `menu_id`가 이미 노출된 정도를 별도 감점으로 사용합니다.

```text
use_count_penalty
= use_count × 8
```

대표 메뉴는 사용 시 `1`이 증가하고, 대체 메뉴는 `0.5`가 증가합니다.

예시:

| 사용 이력 | Count | Penalty |
|---|---:|---:|
| 미사용 | 0 | 0 |
| 대체 메뉴 1회 | 0.5 | 4 |
| 대표 메뉴 1회 | 1 | 8 |
| 대표 메뉴 2회 | 2 | 16 |

유사도 Penalty와 별개이므로, 같은 메뉴가 최근 노출 Window 밖으로 빠져도 누적 사용 횟수에 따른 감점은 유지됩니다.

<br>

## 9. MMR 정렬 기준

`rerank_menus_by_mmr()`는 각 메뉴에 `mmr_score`를 추가한 뒤 다음 순서로 정렬합니다.

```text
1. mmr_score 높은 순
2. 사용 횟수 적은 순
3. final_score 높은 순
```

코드상 정렬 Key:

```python
(
    menu.get("mmr_score", 0),
    -used_menu_count.get(menu.get("menu_id"), 0),
    menu.get("final_score", 0),
)
```

전체 정렬은 내림차순입니다.

`used_menu_count`에 음수를 적용하므로 사용량이 적은 메뉴가 먼저 배치됩니다.

<br>

## 10. 메뉴 유사도 판정

관련 파일:

```text
modeling/services/plan/menu_similarity_service.py
```

두 메뉴의 유사도는 `0~1` 범위로 계산합니다.

### 즉시 동일 메뉴로 판정하는 조건

다음 중 하나를 만족하면 유사도 `1`을 반환합니다.

```text
동일한 menu_id
상대 menu_id가 similar_menu_ids에 포함
스타일 수식어를 제거한 메뉴명이 동일
```

### 일반 유사도 계산

위 조건에 해당하지 않으면 다음 값 중 가장 큰 값을 사용합니다.

```text
max(
    재료 Jaccard 유사도,
    재료군 Jaccard 유사도 × 0.8,
    동일 카테고리 보정값 0.2
)
```

### 최종 유사 메뉴 기준

```text
similarity_score ≥ 0.6
→ 유사 메뉴
```

관련 함수:

```python
are_menus_similar(
    first_menu: dict,
    second_menu: dict,
) -> bool
```

<br>

## 11. 메뉴명 정규화

관련 함수:

```python
normalize_menu_name(
    name: str | None,
) -> str
```

메뉴 이름 앞의 Style 수식어를 제거한 뒤 비교합니다.

현재 제거 대상:

```text
담백한
매콤
간장
저칼로리
고단백
든든한
가벼운
프리미엄
간편
건강한
저염
다이어트
구운
라이트
```

예시:

```text
"고단백 닭가슴살 덮밥"
→ "닭가슴살 덮밥"

"저칼로리 닭가슴살 덮밥"
→ "닭가슴살 덮밥"
```

정규화된 이름이 같으면 두 메뉴의 유사도를 `1`로 처리합니다.

현재 구현은 목록의 Prefix 하나를 제거한 뒤 다음 Prefix를 계속 확인하므로 여러 수식어가 순차적으로 붙은 경우도 일부 제거될 수 있습니다.

<br>

## 12. 재료 기반 유사도

재료와 재료군은 각각 Set으로 변환한 뒤 Jaccard Similarity를 계산합니다.

```text
Jaccard Similarity
= 교집합 원소 수 ÷ 합집합 원소 수
```

### 재료 유사도

```python
calculate_ingredient_similarity(
    first_menu,
    second_menu,
)
```

입력:

```text
menu.ingredients
```

### 재료군 유사도

```python
calculate_ingredient_group_similarity(
    first_menu,
    second_menu,
)
```

입력:

```text
menu.ingredient_groups
```

최종 유사도에서는 재료군 유사도에 `0.8`을 곱합니다.

```text
weighted_ingredient_group_similarity
= ingredient_group_similarity × 0.8
```

### 빈 재료 목록

둘 중 하나의 Set이 비어 있으면 Jaccard Similarity는 `0`입니다.

따라서 재료 데이터가 누락된 메뉴는 이름, `similar_menu_ids`, 카테고리 중심으로만 비교될 수 있습니다.

<br>

## 13. 최근 노출 메뉴 관리

관련 함수:

```python
get_recent_exposed_menus(
    days: list[dict],
    recent_day_window: int,
) -> list[dict]
```

최근 N일의 다음 메뉴를 모두 노출 메뉴로 간주합니다.

```text
selected_menu
alternative_menus
```

대체 메뉴 역시 사용자 화면에 노출되므로 이후 추천의 유사도 계산 대상에 포함됩니다.

### 비-OR-Tools 경로의 Window

관련 함수:

```python
get_recent_day_window(
    diversity_penalty_strength: float,
) -> int
```

| Diversity Strength | Recent Day Window |
|---:|---:|
| `0.1` 이하 | 0일 |
| `0.3` 이하 | 1일 |
| `0.3` 초과 | 2일 |

### OR-Tools Mapper의 Window

기본값:

```text
recent_day_window = 3
```

Profile에 값이 있으면 해당 값을 우선합니다.

따라서 비-OR-Tools 경로와 OR-Tools 경로의 기본 Window 정책은 동일하지 않습니다.

<br>

## 14. Style Priority

관련 파일:

```text
modeling/services/plan/meal_selector_service.py
```

MMR 재랭킹 이후 일부 Style에 대해 조건부 후보 우선 정책을 적용합니다.

### 고단백

다음 순서로 충분한 후보가 있는지 확인합니다.

```text
단백질 30g 이상 후보가 20개 이상
→ 해당 후보만 우선

부족하면 25g 이상 후보가 20개 이상
→ 해당 후보만 우선

부족하면 22g 이상 후보가 20개 이상
→ 해당 후보만 우선

모두 부족
→ 전체 후보 유지
```

### 간편식

```text
difficulty score 70 이상 후보가 20개 이상
→ 해당 후보만 우선

부족하면 difficulty score 60 이상 후보가 20개 이상
→ 해당 후보만 우선

후보 부족
→ 전체 후보 유지
```

이는 Hard Filter가 아닙니다. Style에 적합한 후보 수가 충분한 경우에만 우선 풀을 좁힙니다.

### Style 우선 후보 정렬

고단백:

```text
mmr_score
→ protein
→ final_score
```

간편식:

```text
mmr_score
→ scores.difficulty
→ final_score
```

내림차순으로 정렬합니다.

현재 Plan 단계에서 별도 후보 필터·정렬을 제공하는 Style은 고단백과 간편식입니다.

<br>

## 15. 대표 메뉴 선택

관련 함수:

```python
select_menu_for_meal(
    recommendations: list[dict],
    exposed_menus: list[dict],
    used_menu_count: dict,
    diversity_penalty_strength: float,
    profile: dict,
) -> dict
```

선택 순서:

```text
1. 전체 후보 MMR 재랭킹
2. Style Priority 후보 필터
3. Style별 우선순위 정렬
4. 최근 노출 메뉴와 유사하지 않은 첫 후보 선택
```

### 첫 번째 Fallback

Style 우선 후보가 모두 최근 노출 메뉴와 유사해도 목록이 비어 있지 않으면 첫 번째 후보를 선택합니다.

```text
style_priority_menus[0]
```

따라서 유사도 회피보다 Style Priority와 MMR 순위를 우선하는 Fallback입니다.

### 두 번째 Fallback

Style 후보 목록이 비어 있으면 전체 MMR 결과에서 최근 노출 메뉴와 유사하지 않은 후보를 찾습니다.

### 최종 Fallback

모든 후보가 최근 노출 메뉴와 유사하면 전체 MMR 결과의 첫 번째 메뉴를 선택합니다.

```text
reranked_menus[0]
```

<br>

## 16. 대체 메뉴 선택

관련 함수:

```python
select_alternative_menus(
    recommendations: list[dict],
    selected_menu: dict,
    exposed_menus: list[dict],
    used_menu_count: dict,
    diversity_penalty_strength: float,
    alternative_count: int = 2,
) -> list[dict]
```

대체 메뉴는 사용자 다양성 설정이 낮더라도 최소 `0.8`의 다양성 강도를 사용합니다.

```text
alternative_diversity_strength
= max(diversity_penalty_strength, 0.8)
```

대표 메뉴를 `local_exposed_menus`에 먼저 포함한 뒤 MMR을 계산합니다.

### 1차 선택 조건

다음 조건을 모두 만족해야 합니다.

```text
대표 메뉴와 다른 menu_id
대표 메뉴와 유사하지 않음
최근 노출 메뉴와 유사하지 않음
이미 선택된 다른 대체 메뉴와 유사하지 않음
```

### 2차 선택 조건

대체 후보가 부족하면 최근 노출 메뉴와의 유사성 제한만 완화합니다.

계속 유지되는 조건:

```text
대표 메뉴와 다른 menu_id
대표 메뉴와 유사하지 않음
기존 대체 메뉴와 중복되지 않음
대체 메뉴끼리 유사하지 않음
```

### 후보 부족

조건을 만족하는 메뉴가 없으면 요청 개수보다 적은 대체 메뉴를 반환할 수 있습니다.

후보가 전혀 없으면:

```json
{
  "alternative_menus": []
}
```

<br>

## 17. 비-OR-Tools 기간별 Plan 생성

관련 파일:

```text
modeling/services/plan/period_plan_service.py
```

대표 함수:

```python
build_period_meal_plan(
    recommendations: list[dict],
    profile: dict,
    period_days: int,
    meal_count_per_day: int,
) -> dict
```

필요 식사 수:

```text
required_meal_count
= period_days × meal_count_per_day
```

### 반복 구조

```text
각 Day
    ↓
최근 Day Window의 노출 메뉴 조회
    ↓
각 Meal Order
    ↓
대표 메뉴 선택
    ↓
대체 메뉴 최대 2개 선택
    ↓
사용 횟수와 노출 목록 갱신
```

### 후보 수 경고

Recommendation 수가 필요한 식사 수보다 적으면 Warning을 추가합니다.

```text
available_recommendation_count
< required_meal_count
```

이 경고는 반드시 메뉴가 반복된다는 뜻은 아니지만, 장기간 Plan에서 반복 가능성이 높다는 의미입니다.

### 호환 Wrapper

```python
build_monthly_plan(...)
```

은 기존 코드 호환을 위해 `build_period_meal_plan()`을 그대로 호출합니다.

<br>

## 18. OR-Tools 결과 매핑

관련 파일:

```text
modeling/services/optimizer/ortools/result_mapper.py
```

OR-Tools의 `selected_items`를 Day별로 그룹화합니다.

```text
selected_items
→ day 기준 그룹화
→ meal_order 기준 정렬
```

대표 메뉴는 Solver가 선택한 원본 메뉴를 그대로 사용합니다.

```text
item.selected_menu
```

각 대표 메뉴에 대해서만 Plan의 MMR 대체 메뉴 선택을 실행합니다.

### 기본 설정

```text
DEFAULT_DIVERSITY_PENALTY_STRENGTH = 0.5
DEFAULT_RECENT_DAY_WINDOW = 3
DEFAULT_ALTERNATIVE_MENU_COUNT = 2
```

Profile에 `diversity_penalty_strength` 또는 `recent_day_window`가 있으면 Profile 값을 우선합니다.

### Solver 진단 정보

Plan 반환값에는 다음 정보가 포함됩니다.

```text
optimizer.enabled
optimizer.solver
optimizer.solver_status
optimizer.objective_value
optimizer.message
optimizer.config
```

Solver 이름:

```text
OR-Tools CP-SAT
```

### 실패 상태 Warning

Mapper에 전달된 Solver Status가 다음 값이 아니면 Warning을 추가합니다.

```text
OPTIMAL
FEASIBLE
```

정상 서비스 흐름에서는 실패 상태가 Mapper 이전에 별도 실패 응답으로 처리되지만, Mapper 자체도 방어적으로 Warning을 생성합니다.

<br>

## 19. 사용 횟수 관리

관련 함수:

```python
increase_used_menu_count(
    used_menu_count: dict,
    menu: dict,
    amount: float = 1,
) -> None
```

### 대표 메뉴

```text
amount = 1
```

### 대체 메뉴

```text
amount = 0.5
```

대체 메뉴는 실제 식단에 확정된 메뉴는 아니지만 사용자에게 노출되므로 절반의 사용량으로 반영합니다.

`menu_id`가 `None`이면 사용 횟수를 기록하지 않습니다.

사용 횟수는 전체 기간 동안 누적되며, 다음 MMR 계산의 `use_count_penalty`에 사용됩니다.

<br>

## 20. 일별 비용과 칼로리

일별 합계는 대표 메뉴만 사용합니다.

### 일별 예상 비용

```python
calculate_day_total_estimated_cost(
    meals: list[dict],
) -> int
```

계산식:

```text
Σ selected_menu.estimated_cost
```

### 일별 칼로리

```python
calculate_day_total_calories(
    meals: list[dict],
) -> int
```

계산식:

```text
Σ selected_menu.calories
```

대체 메뉴는 일별 비용과 칼로리에 포함되지 않습니다.

<br>

## 21. Plan Summary

관련 파일:

```text
modeling/services/plan/plan_summary_service.py
```

관련 함수:

```python
calculate_monthly_plan_summary(
    days: list[dict],
) -> dict
```

Summary는 모든 Day의 `selected_menu`만 사용합니다. 대체 메뉴는 계산에서 제외됩니다.

### 메뉴 수

```text
selected_menu_count
= 선택된 대표 메뉴 총개수
```

```text
unique_menu_count
= menu_id Set의 크기
```

```text
duplicate_menu_count
= selected_menu_count - unique_menu_count
```

### 비용

```text
total_estimated_cost
= 모든 대표 메뉴 estimated_cost 합
```

```text
average_daily_cost
= total_estimated_cost ÷ Day 개수
```

일평균 비용은 `round()`로 정수 반올림합니다.

### 평균 영양 정보

각 값은 대표 메뉴 수로 나눕니다.

```text
average_calories
average_protein
average_carbohydrate
average_fat
```

소수점 둘째 자리까지 반올림합니다.

### 평균 Recommendation 점수

```text
average_nutrition_score
average_budget_score
average_preference_score
average_difficulty_score
average_diversity_score
```

데이터 원천:

```text
menu.scores.nutrition
menu.scores.budget
menu.scores.preference
menu.scores.difficulty
menu.scores.diversity
```

### 선택 메뉴가 없는 경우

모든 Summary 필드를 `0`으로 반환합니다.

### Menu ID가 없는 경우

`unique_menu_count`는 `menu_id`가 존재하는 메뉴만 집계합니다.

반면 `selected_menu_count`에는 ID가 없는 메뉴도 포함되므로, ID 누락이 있으면 `duplicate_menu_count`가 실제 반복 수보다 크게 계산될 수 있습니다.

<br>

## 22. Style Validation 연동

Plan Summary는 Style Validation 입력으로 사용됩니다.

호출 흐름:

```text
monthly_plan.summary
        ↓
build_style_validation()
        ↓
build_difficulty_feasibility_diagnostics()
        ↓
enrich_style_validation()
        ↓
monthly_plan.style_validation
```

### 기본 Validation

선택 Style에 따라 다음 Summary 지표를 사용합니다.

| Style | 주요 지표 |
|---|---|
| 고단백 | `average_protein` |
| 다이어트 | `average_calories`, `average_fat` |
| 영양 균형 | 탄수화물·단백질·지방 평균 |
| 식비 절약 | `total_estimated_cost`, 월 예산 |
| 간편식 | `average_difficulty_score` |
| 맛 중심 | `average_preference_score` |

### 보조 경고

```text
average_difficulty_score
average_preference_score
average_diversity_score
duplicate_menu_count
selected_menu_count
```

를 사용해 `secondary_warnings`를 생성합니다.

### 간편식 후보 진단

Optimizer Snapshot의 후보 난이도 분포를 분석해 다음을 구분합니다.

```text
Optimizer 선택 문제
후보 풀 자체의 쉬운 메뉴 부족
Difficulty Score Mapping 문제
Validation Threshold 문제
```

자세한 Style별 기준은 [`../style/README.md`](../style/README.md)를 참고합니다.

<br>

## 23. 내부 Menu Payload

관련 파일:

```text
modeling/services/plan/meal_payload_service.py
```

관련 함수:

```python
build_menu_payload(
    menu: dict,
) -> dict
```

Plan 내부에서는 화면 데이터뿐 아니라 검증과 디버깅에 필요한 필드도 보존합니다.

대표 필드:

```text
menu_id
name
category
final_score
estimated_cost
rag_estimated_cost
pricing_status

calories
carbohydrate
protein
fat
nutrient_summary

ingredients
ingredient_groups
ingredient_usages
ingredient_costs
recipe

scores
reasons

rag_data_quality_score
rag_data_quality_issues
rag_data_quality_penalty

nutrition_missing_penalty
total_quality_penalty

nutrition_outlier_issues
nutrition_outlier_penalty
is_extreme_nutrition_outlier
```

### 영양소 Fallback

탄수화물·단백질·지방은 최상위 필드가 없으면 `nutrient_summary`를 사용합니다.

```text
menu.protein
→ 없으면 nutrient_summary.protein
```

칼로리는 최상위 `calories`만 사용합니다.

<br>

## 24. Back/Front 전달용 Payload

관련 파일:

```text
modeling/services/plan/plan_payload_service.py
```

내부 Plan 메뉴를 Back/Front 전달용으로 경량화합니다.

### 유지되는 메뉴 필드

```text
menu_id
name
category
final_score

estimated_cost
rag_estimated_cost
pricing_status

calories
protein
carbohydrate
fat
nutrient_summary

difficulty

ingredients
ingredient_groups
ingredient_usages
ingredient_costs

recipe
reasons
allergy_ingredients
```

### Recipe 요약

최종 응답의 Recipe에는 다음 항목만 유지합니다.

```text
serving_size
cooking_time
required_ingredients
```

### 제거되는 내부 진단 필드

대표적으로 다음 필드는 최종 메뉴 Payload에 포함되지 않습니다.

```text
scores 전체
mmr_score

rag_data_quality_score
rag_data_quality_issues
rag_data_quality_penalty

nutrition_missing_penalty
total_quality_penalty

nutrition_outlier_issues
nutrition_outlier_penalty
is_extreme_nutrition_outlier
```

다만 Summary와 Style Validation은 Payload 경량화 전에 계산되므로 내부 점수는 검증에 사용할 수 있습니다.

<br>

## 25. 추천 이유 필터링

관련 함수:

```python
filter_reasons_by_focus_key(
    reasons: list[dict],
    focus_key: str | None,
) -> list[dict]
```

선택 Style의 핵심 Focus와 일치하는 추천 이유를 우선 노출합니다.

### Focus Key가 없는 경우

```text
전체 reasons 반환
```

### 일치 이유가 있는 경우

```text
reason.type == focus_key
```

인 이유만 반환합니다.

예시:

```text
focus_key = budget
→ type이 budget인 이유만 반환
```

### 일치 이유가 없는 경우

```text
reasons[:1]
```

첫 번째 이유 하나만 반환합니다.

이 로직은 내부 추천 계산을 바꾸는 것이 아니라 사용자 화면에 표시되는 설명을 정리하는 역할입니다.

<br>

## 26. 최종 월간 응답 구조

관련 함수:

```python
build_modeling_to_back_monthly_response(
    user_id: str,
    selected_style: dict,
    base_profile: dict,
    monthly_profile: dict,
    monthly_plan: dict,
    actual_recommendation_count: int,
) -> dict
```

대표 구조:

```json
{
  "id": "user-001",
  "request_type": "monthly_plan",
  "success": true,
  "failure_reason": null,
  "selected_style": {},
  "meta": {
    "period_days": 30,
    "meal_count_per_day": 3,
    "required_meal_count": 90,
    "available_recommendation_count": 120,
    "generated_at": "2026-06-24T05:00:00Z",
    "warnings": [],
    "fallback": {}
  },
  "modeling_profile": {},
  "applied_style_adjustment": {},
  "monthly_plan": {
    "period_days": 30,
    "meal_count_per_day": 3,
    "required_meal_count": 90,
    "optimizer": {},
    "summary": {},
    "style_validation": {},
    "days": []
  }
}
```

### Modeling Profile

원본 사용자 조건과 Modeling 계산값을 요약합니다.

```text
goals
monthly_budget
period_days
meal_count_per_day
cooking_skill
preferred_categories
diversity_level
ingredient_preferences
allergy_ingredients

budget_period_days
sample_period_days
meal_budget
weights
max_difficulty
diversity_penalty_strength
```

### Applied Style Adjustment

선택 Style 적용 전후의 가중치를 제공합니다.

```text
applied_style_focus_key
base_weights
applied_monthly_weights
applied_nutrition_detail_weights
```

<br>

## 27. 경고와 Fallback 정보

Plan에는 다음 진단 정보가 유지됩니다.

```text
warnings
fallback
profiling
optimizer
```

### 일반 Plan 후보 부족 경고

```text
available_recommendation_count
< required_meal_count
```

이면 일부 메뉴가 반복될 수 있다는 Warning을 추가합니다.

### OR-Tools 실패 Warning

Result Mapper에 전달된 Solver Status가 `OPTIMAL` 또는 `FEASIBLE`이 아니면 Warning을 추가합니다.

### Fallback

Optimizer 재시도 과정에서 다음 정보가 포함될 수 있습니다.

```text
fallback_used
fallback_steps
final_candidate_count
candidate_diagnostics
warnings
```

### Profiling

파이프라인 단계별 실행 시간 측정값이 포함될 수 있습니다.

```text
RAG 요청 시간
Recommendation 시간
Optimizer Input 생성 시간
OR-Tools Solver 시간
Retry Solver 시간
Plan Mapping 시간
```

<br>

## 28. 실행 및 테스트

프로젝트 루트에서 실행합니다.

### MMR Lambda 확인

```bash
PYTHONPATH=modeling \
python - <<'PY'
from services.plan.mmr_service import get_mmr_lambda

for strength in [0.0, 0.2, 0.4, 0.6, 0.8]:
    print(strength, get_mmr_lambda(strength))
PY
```

예상 결과:

```text
0.0 0.8
0.2 0.8
0.4 0.65
0.6 0.55
0.8 0.55
```

### MMR Score 확인

```bash
PYTHONPATH=modeling \
python - <<'PY'
from services.plan.mmr_service import calculate_mmr_score

menu = {
    "menu_id": 1,
    "name": "닭가슴살 덮밥",
    "final_score": 90,
    "ingredients": ["닭가슴살", "쌀"],
    "ingredient_groups": ["닭고기", "곡류"],
    "similar_menu_ids": [],
}

exposed = [{
    "menu_id": 2,
    "name": "고단백 닭가슴살 덮밥",
    "final_score": 80,
    "ingredients": ["닭가슴살", "쌀"],
    "ingredient_groups": ["닭고기", "곡류"],
    "similar_menu_ids": [],
}]

score = calculate_mmr_score(
    menu=menu,
    exposed_menus=exposed,
    used_menu_count={1: 1},
    diversity_penalty_strength=0.6,
)

print(score)
PY
```

정규화된 메뉴명이 같으므로 유사도는 `1`로 계산됩니다.

### 메뉴 유사도 확인

```bash
PYTHONPATH=modeling \
python - <<'PY'
from services.plan.menu_similarity_service import (
    calculate_menu_similarity_score,
    are_menus_similar,
)

first = {
    "menu_id": 1,
    "name": "고단백 닭가슴살 덮밥",
    "ingredients": ["닭가슴살", "쌀"],
    "ingredient_groups": ["닭고기", "곡류"],
    "category": "밥",
    "similar_menu_ids": [],
}

second = {
    "menu_id": 2,
    "name": "저칼로리 닭가슴살 덮밥",
    "ingredients": ["닭가슴살", "현미"],
    "ingredient_groups": ["닭고기", "곡류"],
    "category": "밥",
    "similar_menu_ids": [],
}

print(calculate_menu_similarity_score(first, second))
print(are_menus_similar(first, second))
PY
```

Style Prefix 제거 후 이름이 같아 유사도 `1`, 유사 메뉴 `True`가 예상됩니다.

### 짧은 Period Plan 실행

```bash
PYTHONPATH=modeling \
python - <<'PY'
from services.plan.period_plan_service import build_period_meal_plan

def menu(menu_id, name, score):
    return {
        "menu_id": menu_id,
        "name": name,
        "category": "밥",
        "final_score": score,
        "estimated_cost": 3000,
        "calories": 500,
        "protein": 25,
        "carbohydrate": 60,
        "fat": 15,
        "ingredients": [name],
        "ingredient_groups": [name],
        "similar_menu_ids": [],
        "scores": {
            "nutrition": 80,
            "budget": 80,
            "preference": 80,
            "difficulty": 80,
            "diversity": 80,
        },
        "reasons": [],
    }

recommendations = [
    menu(1, "메뉴 A", 90),
    menu(2, "메뉴 B", 85),
    menu(3, "메뉴 C", 80),
    menu(4, "메뉴 D", 75),
]

result = build_period_meal_plan(
    recommendations=recommendations,
    profile={
        "diversity_penalty_strength": 0.5,
        "selected_style_goal": "영양 균형",
    },
    period_days=2,
    meal_count_per_day=1,
)

print(result["summary"])
print(result["days"])
PY
```

### Plan 관련 테스트

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/optimizer/test_ortools_alternative_menus.py \
  modeling/tests/contract/test_optimizer_failure_response_contract.py \
  -q
```

### 문법 검사

```bash
python -m py_compile \
  modeling/services/plan/mmr_service.py \
  modeling/services/plan/menu_similarity_service.py \
  modeling/services/plan/meal_selector_service.py \
  modeling/services/plan/period_plan_service.py \
  modeling/services/plan/plan_summary_service.py \
  modeling/services/plan/meal_payload_service.py \
  modeling/services/plan/plan_payload_service.py \
  modeling/services/plan/plan_validation_service.py
```

### 전체 Modeling 테스트

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest modeling/tests -q
```

### 현재 확인된 전용 테스트

```text
OR-Tools 대표 메뉴 유지
대체 메뉴 두 개 생성
대표 메뉴 ID 제외
대체 메뉴 ID 중복 방지
대체 후보가 없으면 빈 배열 유지
```

현재 MMR 수식, 메뉴 유사도 경계값, 기간별 Plan과 Summary를 직접 검증하는 전용 단위 테스트는 별도로 확인되지 않았습니다.

<br>

## 29. 파일 구조

```text
modeling/
├── services/
│   ├── plan/
│   │   ├── __init__.py
│   │   ├── mmr_service.py
│   │   ├── menu_similarity_service.py
│   │   ├── meal_selector_service.py
│   │   ├── period_plan_service.py
│   │   ├── plan_summary_service.py
│   │   ├── meal_payload_service.py
│   │   ├── plan_payload_service.py
│   │   ├── plan_validation_service.py
│   │   └── README.md
│   │
│   ├── optimizer/
│   │   └── ortools/
│   │       └── result_mapper.py
│   │
│   └── recommendation/
│       └── recommendation_service.py
│
├── experiments/
│   ├── analysis/
│   ├── flows/
│   ├── scenarios/
│   └── tuning/
│
└── tests/
    ├── contract/
    └── optimizer/
```

### 파일별 역할

| 파일 | 역할 |
|---|---|
| `mmr_service.py` | MMR 점수 계산과 후보 재정렬 |
| `menu_similarity_service.py` | 메뉴명·재료·재료군·카테고리 기반 유사도 |
| `meal_selector_service.py` | Style Priority, 대표 메뉴와 대체 메뉴 선택 |
| `period_plan_service.py` | 비-OR-Tools 기간별 식단 생성 |
| `plan_summary_service.py` | 비용·영양·중복·평균 점수 계산 |
| `meal_payload_service.py` | 내부 Plan Menu 공통 구조 생성 |
| `plan_payload_service.py` | Back/Front 전달용 경량 Payload 생성 |
| `plan_validation_service.py` | Style Validation과 보조 경고 |
| `optimizer/ortools/result_mapper.py` | OR-Tools 결과를 Plan 구조로 변환 |

<br>

## 30. 현재 구현상 주의사항

### 비-OR-Tools와 OR-Tools의 Recent Window 정책 차이

비-OR-Tools 경로:

```text
Diversity Strength 기준 0~2일
```

OR-Tools Result Mapper:

```text
Profile 값이 없으면 기본 3일
```

같은 사용자 조건에서도 실행 경로에 따라 대체 메뉴 선택 결과가 달라질 수 있습니다.

### OR-Tools 대표 메뉴는 MMR로 다시 선택하지 않음

Solver가 확정한 대표 메뉴는 그대로 유지합니다.

```text
OR-Tools selected_menu
→ Plan에서 교체하지 않음
```

MMR은 대체 메뉴 후처리에만 사용됩니다.

### 비-OR-Tools 대표 메뉴는 MMR로 선택

비-OR-Tools 경로에서는 모든 Meal Slot마다 MMR과 Style Priority를 다시 계산합니다.

두 경로의 대표 메뉴 다양성 제어 방식은 구조적으로 다릅니다.

### 카테고리 일치만으로는 유사 메뉴가 아님

동일 카테고리 보정값은 `0.2`이고 유사 메뉴 기준은 `0.6`입니다.

```text
카테고리만 같음
→ similarity = 0.2
→ are_menus_similar = False
```

### 재료군 유사도는 0.8 배율

재료군이 완전히 같아도 최종 후보 값은 `0.8`입니다.

이는 유사 기준 `0.6`을 넘으므로 완전히 같은 재료군은 유사 메뉴로 판정됩니다.

### 대체 메뉴도 반복 감점에 영향

대체 메뉴는 대표 메뉴의 절반인 `0.5` 사용량으로 누적됩니다.

대체 후보에 자주 노출된 메뉴는 향후 대표 메뉴 MMR 점수도 낮아질 수 있습니다.

### 동일 메뉴명 Prefix 목록은 수동 관리

새로운 표현이 Prefix 목록에 없으면 같은 메뉴가 서로 다른 이름으로 인식될 수 있습니다.

예시:

```text
"헬시 닭가슴살 덮밥"
```

`헬시`가 목록에 없다면 자동 제거되지 않습니다.

### Summary의 Duplicate 계산은 Menu ID 품질에 의존

```text
duplicate_menu_count
= selected_menu_count - unique menu_id count
```

`menu_id`가 누락된 메뉴가 있으면 해당 메뉴도 Duplicate처럼 집계될 수 있습니다.

### 평균은 대표 메뉴만 사용

다음은 Summary에 포함되지 않습니다.

```text
alternative_menus
```

따라서 사용자가 실제로 대체 메뉴를 선택한 이후의 영양·비용은 현재 생성 시점 Summary와 달라질 수 있습니다.

### Back Payload에서도 final_score 유지

내부 상세 점수인 `scores`는 제거하지만 최종 종합 점수인 `final_score`는 유지합니다.

Front에서 이 점수를 직접 표시하지 않는다면 API 노출 필요성을 별도로 검토할 수 있습니다.

### Recipe 전체 정보는 경량화됨

Plan 내부에서는 전체 `recipe`를 보존할 수 있지만 최종 Back 응답에서는 다음만 유지합니다.

```text
serving_size
cooking_time
required_ingredients
```

조리 단계 등 추가 정보가 필요하다면 별도 상세 API 또는 Payload 확장이 필요합니다.

### 전용 테스트 부족

현재 다음 영역에 대한 직접 단위 테스트는 확인되지 않았습니다.

```text
MMR Lambda 경계값
MMR Score 공식
메뉴명 Prefix 정규화
Jaccard 유사도
유사도 0.6 경계
Recent Day Window
대표 메뉴 Fallback
대체 메뉴 2차 완화
사용 횟수 1 / 0.5 반영
Summary 중복 계산
Focus Key 추천 이유 필터
Back Payload 필드 제거
```

정책 변경 시 회귀를 막기 위해 경계값 테스트를 추가하는 것이 좋습니다.

<br>

## 31. 관련 문서

### 프로젝트 설계 및 고도화

- [📘 MMR + 제약 기반 재랭킹 + 월간 배치 다양성 제어](https://app.notion.com/p/MMR-35e9e3e335cc806897c9d4adc1e827c4?source=copy_link)  
  Recommendation 결과에 MMR과 유사도 제어를 적용하고 월간 식단 반복을 줄인 설계 및 구현 과정

- [🔍 중복 메뉴 및 다양성 개선 분석](https://app.notion.com/p/3829e3e335cc80fa8a4aca2435b2aca4?source=copy_link)  
  동일 메뉴 반복률, 후보 풀 크기, Repeat Penalty와 다양성 개선 실험 분석

### 참고 자료

- [📚 MMR / Re-ranking 참고 자료](https://app.notion.com/p/MMR-Re-ranking-3629e3e335cc80f88109d2cd6f6855ad?source=copy_link)  
  Relevance와 Novelty를 함께 고려하는 MMR 개념과 Re-ranking 학습 자료

### Repository 문서

- [`../style/README.md`](../style/README.md)  
  선택 Style의 월간 Profile 반영과 Style Validation 기준

- [`../optimizer/README.md`](../optimizer/README.md)  
  OR-Tools 월간 조합 최적화, 반복 제한, 예산 제약과 Retry 정책

- [`../../experiments/docs/modeling_validation_optimizer_report.md`](../../experiments/docs/modeling_validation_optimizer_report.md)  
  Validation, 후보 풀 품질, Optimizer 및 다양성 정책의 통합 검증 결과
