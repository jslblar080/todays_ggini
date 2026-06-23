# ⚙️ OR-Tools Monthly Meal Plan Optimizer

Recommendation이 점수화한 후보 메뉴를 대상으로 월간 식단의 전체 슬롯을 구성하는 OR-Tools CP-SAT 기반 최적화 모듈입니다.

각 식사 슬롯에 메뉴를 정확히 하나씩 배치하면서 월 예산과 동일 메뉴 반복 상한을 Hard Constraint로 적용합니다. 그 안에서 추천 점수, 메뉴 비용, 반복 감점, 단백질 보상, 조리 적합도 보상과 영양 이상치 감점을 결합한 Objective를 최대화합니다.

```text
Recommendation 결과
→ Optimizer 후보 선별
→ 월간 식사 Slot 생성
→ CP-SAT 결정 변수 생성
→ Hard Constraint 적용
→ Objective 구성
→ Solver 실행
→ 실패 시 후보 확장 및 재시도
→ 결과를 월간 Plan으로 매핑
→ Validation 및 진단
```

<br>

## 목차

1. [모듈 역할](#1-모듈-역할)
2. [전체 처리 흐름](#2-전체-처리-흐름)
3. [파일 구조](#3-파일-구조)
4. [Optimizer 입력 데이터](#4-optimizer-입력-데이터)
5. [월간 Slot 생성](#5-월간-slot-생성)
6. [후보 메뉴 변환](#6-후보-메뉴-변환)
7. [결정 변수](#7-결정-변수)
8. [Hard Constraint](#8-hard-constraint)
9. [월 예산 Constraint](#9-월-예산-constraint)
10. [반복 횟수 Constraint](#10-반복-횟수-constraint)
11. [Objective 전체 구조](#11-objective-전체-구조)
12. [Recommendation Score 보상](#12-recommendation-score-보상)
13. [비용 Penalty](#13-비용-penalty)
14. [반복 Penalty](#14-반복-penalty)
15. [Protein Bonus](#15-protein-bonus)
16. [Difficulty Bonus](#16-difficulty-bonus)
17. [Nutrition Outlier Penalty](#17-nutrition-outlier-penalty)
18. [Solver 실행](#18-solver-실행)
19. [Solver 상태](#19-solver-상태)
20. [사전 실행 가능성 검사](#20-사전-실행-가능성-검사)
21. [Retry Fallback](#21-retry-fallback)
22. [INFEASIBLE 정책](#22-infeasible-정책)
23. [Optimizer 결과 구조](#23-optimizer-결과-구조)
24. [Plan 결과 매핑](#24-plan-결과-매핑)
25. [대체 메뉴 생성](#25-대체-메뉴-생성)
26. [실험 및 Snapshot](#26-실험-및-snapshot)
27. [실행 및 테스트](#27-실행-및-테스트)
28. [현재 구현상 주의사항](#28-현재-구현상-주의사항)
29. [관련 문서](#29-관련-문서)

<br>

## 1. 모듈 역할

Optimizer는 후보 메뉴 각각의 적합도를 계산하는 모듈이 아니라, 전체 기간의 메뉴 배치를 결정하는 모듈입니다.

Recommendation은 다음과 같은 메뉴별 점수를 생성합니다.

```text
final_score
estimated_cost
protein
difficulty_score
nutrition_outlier_penalty
```

Optimizer는 이 값들을 받아 다음 문제를 해결합니다.

```text
주어진 월간 식사 슬롯을
어떤 메뉴들로 채워야

- 사용자 추천 점수가 높고
- 월 예산을 넘지 않으며
- 같은 메뉴가 과도하게 반복되지 않고
- 선택 Style의 목표가 반영되는가?
```

### 역할 구분

| 단계 | 역할 |
|---|---|
| Recommendation | 후보 메뉴별 사용자 적합도 계산 |
| MMR | 노출 메뉴와의 유사성을 반영한 재랭킹 |
| OR-Tools Optimizer | 전체 월간 Slot에 대한 조합 최적화 |
| Plan Mapper | Solver 결과를 일자별 응답 구조로 변환 |
| Validation | 생성된 월간 식단의 품질과 Style 반영 검증 |

<br>

## 2. 전체 처리 흐름

```text
월간 Profile
+ Recommendation 후보
        ↓
build_optimizer_input()
        ↓
required_meal_count 계산
        ↓
Optimizer 후보 수 제한 및 보충
        ↓
Slot과 Menu 입력 생성
        ↓
사전 후보 수 검사
        ↓
사전 예산 실행 가능성 검사
        ↓
solve_monthly_plan_with_ortools()
        ↓
OPTIMAL 또는 FEASIBLE
        ├── 성공
        │   → build_ortools_monthly_plan()
        │   → 월간 Plan 매핑
        │
        └── 실패
            → 추가 RAG 후보 요청
            → 후보 병합
            → Recommendation 재실행
            → Optimizer Input 재생성
            → Solver 재시도
            → 최종 실패 응답
```

<br>

## 3. 파일 구조

```text
modeling/
├── services/
│   ├── optimizer/
│   │   ├── optimizer_input_builder.py
│   │   │
│   │   ├── baselines/
│   │   │   └── least_cost_baseline.py
│   │   │
│   │   └── ortools/
│   │       ├── monthly_plan_optimizer.py
│   │       ├── result_mapper.py
│   │       └── infeasible_policy.py
│   │
│   ├── modeling_service.py
│   │
│   └── plan/
│       ├── plan_validation_service.py
│       └── plan_payload_service.py
│
├── experiments/
│   ├── analysis/
│   ├── scenarios/
│   ├── snapshots/
│   └── tuning/
│
└── tests/
    ├── contract/
    └── optimizer/
```

### 파일별 역할

| 파일 | 역할 |
|---|---|
| `optimizer_input_builder.py` | Recommendation 결과를 OR-Tools 입력으로 변환하고 설정을 구성 |
| `monthly_plan_optimizer.py` | CP-SAT 모델, 제약조건, Objective와 Solver 실행 |
| `result_mapper.py` | 선택 결과를 일자별 월간 식단 구조로 매핑 |
| `infeasible_policy.py` | 실패 시 활성 조건, 진단 정보와 조정 Action 생성 |
| `least_cost_baseline.py` | 최저가 중심 Baseline 생성 |
| `modeling_service.py` | 사전 진단, Solver 실행, Retry 및 실패 응답 제어 |

<br>

## 4. Optimizer 입력 데이터

Optimizer 진입점은 다음 형태의 Dictionary를 받습니다.

```python
solve_monthly_plan_with_ortools(
    optimizer_input: dict,
) -> dict
```

대표 필드:

```text
profile
period_days
meal_count_per_day
slots
menus
monthly_budget
required_meal_count

original_recommendation_count
used_optimizer_candidate_count
optimizer_candidate_multiplier
optimizer_candidate_limit
low_cost_candidate_limit
additional_low_cost_candidate_count

max_repeat_per_menu
solver_time_limit_seconds

score_weight
cost_penalty_weight
cost_penalty_divisor
repeat_penalty_weight
repeat_penalty_growth

enable_nutrition_outlier_penalty
nutrition_outlier_penalty_weight

enable_protein_bonus
protein_bonus_weight
protein_bonus_cap_grams

enable_difficulty_bonus
difficulty_bonus_weight

optimizer_config
```

### 필수 식사 수

```text
required_meal_count
= period_days × meal_count_per_day
```

예시:

```text
30일 × 하루 3끼
= 90개 Slot
```

<br>

## 5. 월간 Slot 생성

Optimizer의 Slot은 월간 식단에서 메뉴 하나가 배치되어야 하는 위치입니다.

대표 구조:

```json
{
  "day": 1,
  "meal_order": 1
}
```

예를 들어 30일 동안 하루 3끼를 생성하면 다음 수의 Slot이 만들어집니다.

```text
Slot 수 = 30 × 3 = 90
```

각 Slot에는 반드시 메뉴 하나가 선택되어야 합니다.

<br>

## 6. 후보 메뉴 변환

Recommendation 메뉴는 Optimizer에서 사용할 수 있도록 정규화됩니다.

대표 필드:

```text
index
menu_id
final_score
estimated_cost
protein
difficulty_score
nutrition_outlier_penalty
is_extreme_nutrition_outlier
raw_menu
```

### Difficulty Score

Optimizer에서 사용하는 `difficulty_score`는 메뉴 자체의 난이도 원점수가 아닙니다.

```text
menu.difficulty
→ 값이 높을수록 조리가 어려움

difficulty_score
→ 사용자 실력 대비 조리 적합도가 높을수록 높은 점수
```

Difficulty Bonus는 후자의 적합도 점수를 사용합니다.

### 원본 메뉴 보존

Solver의 계산용 필드 외에 전체 원본 Recommendation 결과는 다음 필드로 보존됩니다.

```text
raw_menu
```

Solver가 선택한 뒤 Plan Mapper에서 원본 메뉴 정보를 복원할 때 사용합니다.

<br>

## 7. 결정 변수

OR-Tools CP-SAT 모델은 Slot과 Menu의 모든 조합에 Bool Variable을 생성합니다.

```python
decision_vars[(slot_index, menu_index)] = model.NewBoolVar(
    f"x_s{slot_index}_m{menu_index}"
)
```

수학적으로는 다음과 같습니다.

```text
x[s, m] ∈ {0, 1}
```

의미:

```text
x[s, m] = 1
→ Slot s에 Menu m을 배치

x[s, m] = 0
→ Slot s에 Menu m을 배치하지 않음
```

Slot이 90개이고 후보 메뉴가 108개라면 결정 변수는 최대 다음과 같이 생성됩니다.

```text
90 × 108 = 9,720개
```

<br>

## 8. Hard Constraint

현재 CP-SAT 모델의 핵심 Hard Constraint는 세 가지입니다.

```text
1. 각 Slot에는 메뉴를 정확히 하나 배치
2. 메뉴별 사용 횟수가 최대 반복 상한을 넘지 않음
3. 월간 총 예상 비용이 월 예산을 넘지 않음
```

Hard Constraint는 Objective 점수가 높더라도 위반할 수 없습니다.

### Soft Constraint와의 차이

| 유형 | 의미 | 현재 예시 |
|---|---|---|
| Hard Constraint | 반드시 만족 | Slot당 하나, 반복 상한, 월 예산 |
| Soft Constraint | 위반 가능하지만 Objective 손해 | 반복 Penalty |
| Bonus | 목표에 적합한 선택을 보상 | Protein, Difficulty |
| Penalty | 품질이 낮은 선택을 감점 | Cost, Nutrition Outlier |

<br>

## 9. 월 예산 Constraint

월 예산이 0보다 클 때만 활성화됩니다.

```python
if monthly_budget > 0:
    model.Add(
        total_estimated_cost_expr <= monthly_budget
    )
```

전체 예상 비용:

```text
total_estimated_cost
= Σ x[s, m] × menu[m].estimated_cost
```

제약식:

```text
total_estimated_cost ≤ monthly_budget
```

### 예산이 없는 경우

```text
monthly_budget ≤ 0
→ 예산 Hard Constraint 비활성화
```

단, 비용 Penalty는 개별 메뉴 Objective에서 별도로 적용될 수 있습니다.

<br>

## 10. 반복 횟수 Constraint

각 메뉴의 전체 사용 횟수는 다음과 같이 계산됩니다.

```text
usage_count[m]
= Σ x[s, m]
```

Hard Constraint:

```text
usage_count[m] ≤ max_repeat_per_menu
```

예시:

```text
max_repeat_per_menu = 2
→ 같은 메뉴는 월간 식단에서 최대 두 번 선택 가능
```

이 상한과 별개로 같은 메뉴의 두 번째 사용부터 Repeat Penalty도 적용됩니다.

<br>

## 11. Objective 전체 구조

OR-Tools는 다음 Objective를 최대화합니다.

```text
Maximize

Σ(
    Recommendation Score 보상
    + Protein Bonus
    + Difficulty Bonus
    - Cost Penalty
    - Nutrition Outlier Penalty
)
- Repeat Penalty
```

코드 구조:

```python
model.Maximize(
    sum(objective_terms)
    - sum(repeat_penalty_terms)
)
```

Slot별 Menu Value:

```text
menu_value
= score
+ protein_bonus
+ difficulty_bonus
- cost_penalty × cost_penalty_weight
- nutrition_outlier_penalty
```

<br>

## 12. Recommendation Score 보상

Recommendation의 `final_score`는 CP-SAT 정수 Objective에 맞게 정수화됩니다.

```text
score
= round(final_score × score_weight)
```

기본 Fallback 값:

```text
score_weight = 100
```

예시:

```text
final_score = 83.52
score_weight = 100

Objective Score
= round(83.52 × 100)
= 8,352
```

이 값이 Objective의 가장 기본적인 메뉴 적합도 보상이 됩니다.

<br>

## 13. 비용 Penalty

관련 함수:

```python
calculate_cost_penalty(
    estimated_cost: int,
    cost_penalty_divisor: int,
) -> int
```

계산식:

```text
cost_penalty
= round(estimated_cost ÷ cost_penalty_divisor)
```

예시:

```text
estimated_cost = 5,000원
cost_penalty_divisor = 100

cost_penalty = 50
```

최종 Objective에서는 다음처럼 반영됩니다.

```text
cost_penalty × cost_penalty_weight
```

### 예외 처리

```text
estimated_cost ≤ 0
→ Penalty 0

cost_penalty_divisor ≤ 0
→ Penalty 0
```

월 예산 Hard Constraint와 비용 Penalty는 역할이 다릅니다.

```text
월 예산 Constraint
→ 전체 비용 상한을 절대적으로 제한

Cost Penalty
→ 예산 안에서도 상대적으로 저렴한 메뉴를 선호하도록 유도
```

<br>

## 14. 반복 Penalty

반복 Penalty는 동일 메뉴 사용을 금지하지 않고, 두 번째 사용부터 Objective 손해를 부여합니다.

```text
1회 사용
→ Penalty 없음

2회 사용
→ Repeat Penalty 발생

3회 이상 사용
→ 더 큰 Repeat Penalty 발생
```

관련 설정:

```text
repeat_penalty_weight
repeat_penalty_growth
```

### Linear

```text
repeat_multiplier
= repeat_level - 1
```

예시:

| 사용 단계 | Multiplier |
|---:|---:|
| 2회 | 1 |
| 3회 | 2 |
| 4회 | 3 |

### Quadratic

```text
repeat_multiplier
= (repeat_level - 1)²
```

예시:

| 사용 단계 | Multiplier |
|---:|---:|
| 2회 | 1 |
| 3회 | 4 |
| 4회 | 9 |

각 단계의 감점:

```text
repeat_penalty
= repeat_penalty_weight × repeat_multiplier
```

### 누적 방식

메뉴를 세 번 사용하면 2회 도달 Penalty와 3회 도달 Penalty가 모두 활성화됩니다.

Quadratic 설정의 경우:

```text
2회 도달: weight × 1
3회 도달: weight × 4

총 반복 Penalty
= weight × 5
```

### Hard Constraint와의 관계

```text
max_repeat_per_menu
→ 반복의 절대 상한

repeat_penalty
→ 상한 이내에서도 가능한 한 다른 메뉴를 선택하도록 유도
```

<br>

## 15. Protein Bonus

Protein Bonus는 설정이 활성화되고 가중치가 0보다 클 때 적용됩니다.

```text
enable_protein_bonus = True
protein_bonus_weight > 0
```

단백질은 지정한 상한까지만 보상합니다.

```text
capped_protein
= min(menu.protein, protein_bonus_cap_grams)
```

보상 계산:

```text
protein_bonus
= round(capped_protein × protein_bonus_weight)
```

기본 단백질 Cap Fallback 값:

```text
protein_bonus_cap_grams = 35
```

예시:

```text
protein = 42g
cap = 35g
weight = 180

bonus
= 35 × 180
= 6,300
```

42g 전체가 아니라 35g까지만 Objective에 반영합니다.

이는 단백질 수치가 지나치게 높은 일부 메뉴가 Objective를 독점하는 것을 줄이기 위한 상한입니다.

<br>

## 16. Difficulty Bonus

Difficulty Bonus는 다음 조건에서 적용됩니다.

```text
enable_difficulty_bonus = True
difficulty_bonus_weight > 0
```

계산식:

```text
difficulty_bonus
= round(difficulty_score × difficulty_bonus_weight)
```

`difficulty_score`는 0~100 범위의 사용자 적합도 점수입니다.

예시:

```text
difficulty_score = 80
difficulty_bonus_weight = 50

difficulty_bonus
= 80 × 50
= 4,000
```

간편식 또는 낮은 조리 부담을 강조하는 상황에서 쉬운 메뉴의 선택 가능성을 높이는 데 사용할 수 있습니다.

<br>

## 17. Nutrition Outlier Penalty

RAG Mapper가 계산한 영양 이상치 Penalty를 Objective에 반영할 수 있습니다.

활성화 조건:

```text
enable_nutrition_outlier_penalty = True
```

계산식:

```text
nutrition_outlier_penalty
= round(
    menu.nutrition_outlier_penalty
    × nutrition_outlier_penalty_weight
)
```

기본 설정에서는 비활성화 상태로 구성될 수 있습니다.

대표 설정:

```text
enable_nutrition_outlier_penalty = False
nutrition_outlier_penalty_weight = 1
```

비활성화 상태에서는 메뉴가 `nutrition_outlier_penalty` 필드를 가지고 있어도 Objective에 직접 차감되지 않습니다.

<br>

## 18. Solver 실행

Solver:

```python
solver = cp_model.CpSolver()
```

설정:

```python
solver.parameters.max_time_in_seconds = float(time_limit)
solver.parameters.num_workers = 8
```

### 시간 제한

Optimizer Input의 다음 값을 사용합니다.

```text
solver_time_limit_seconds
```

`monthly_plan_optimizer.py` 내부 Fallback 값은 10초이지만, 정상 파이프라인에서는 Input Builder가 생성한 값이 전달됩니다.

### 병렬 Worker

```text
num_workers = 8
```

CP-SAT이 최대 8개 Worker를 사용하도록 설정합니다.

<br>

## 19. Solver 상태

서비스에서 성공으로 인정하는 Solver 상태는 두 가지입니다.

```python
SUCCESS_SOLVER_STATUSES = {
    "OPTIMAL",
    "FEASIBLE",
}
```

### OPTIMAL

설정된 시간과 탐색 조건 안에서 최적해가 증명된 상태입니다.

### FEASIBLE

모든 Hard Constraint를 만족하는 해를 찾았지만, 전역 최적해임을 증명하지 못한 상태입니다.

서비스에서는 두 상태 모두 사용할 수 있는 성공 결과로 처리합니다.

### 실패 계열

대표적으로 다음 상태가 발생할 수 있습니다.

```text
INFEASIBLE
UNKNOWN
MODEL_INVALID
NO_SLOTS
NO_CANDIDATE_MENUS
```

### 입력 자체가 없는 경우

Slot 없음:

```json
{
  "success": false,
  "solver_status": "NO_SLOTS",
  "selected_items": [],
  "message": "식단 슬롯이 없습니다."
}
```

후보 없음:

```json
{
  "success": false,
  "solver_status": "NO_CANDIDATE_MENUS",
  "selected_items": [],
  "message": "OR-Tools에 입력할 후보 메뉴가 없습니다."
}
```

<br>

## 20. 사전 실행 가능성 검사

Solver를 실행하기 전에 후보 수와 예산에 대한 실행 가능성을 확인합니다.

### 최대 채울 수 있는 식사 수

```text
max_fillable_meal_count
= available_recommendation_count
× max_repeat_per_menu
```

다음 조건이면 Solver를 실행하지 않고 후보 부족 응답을 반환합니다.

```text
max_fillable_meal_count
< required_meal_count
```

예시:

```text
후보 메뉴 20개
메뉴당 최대 2회 반복
필요 식사 수 90개

20 × 2 = 40
40 < 90

→ 후보 수 부족
```

### 예산 절대 불가능 진단

각 후보를 허용 반복 횟수만큼 확장한 뒤 가장 저렴한 조합의 최소 가능 비용을 계산합니다.

```text
min_possible_cost
= 반복 상한을 반영했을 때
  필요한 Slot을 채우는 최저 비용 합
```

다음 조건이면 Solver 실행 전에 예산 불가능으로 판단합니다.

```text
min_possible_cost > monthly_budget
```

이 경우 Solver가 찾아낼 수 있는 해가 없으므로 즉시 별도 실패 응답을 반환합니다.

<br>

## 21. Retry Fallback

기본적으로 Optimizer Retry Fallback은 활성화됩니다.

```text
enable_optimizer_retry_fallback = True
```

초기 Solver 결과가 `OPTIMAL` 또는 `FEASIBLE`이 아니면 추가 RAG 후보를 요청해 한 번 더 시도합니다.

### Retry 흐름

```text
1차 Solver 실패
→ 추가 후보 수 계산
→ 선호 카테고리 완화
→ 재료 선호 범위 확장
→ 다양성 수준을 보통으로 조정
→ RAG 후보 추가 요청
→ 기존 후보와 신규 후보 병합
→ Recommendation 전체 재실행
→ Optimizer Input 재생성
→ Solver 재실행
```

### 완화되는 조건

추가 RAG 요청용 Profile:

```text
preferred_categories = ["다 좋아요"]
ingredient_preferences = 확장된 재료 선호 목록
diversity_level = "보통"
```

알레르기 조건은 완화하지 않습니다.

### 후보 확장 수

코드에서는 다음 값들을 조합해 확장 후보 수를 계산합니다.

```text
현재 후보 수 + required_meal_count × 0.8
required_meal_count × 2.8
추가 후보 계산 함수의 결과
```

이들 중 큰 값을 사용합니다.

```python
expanded_candidate_count = max(
    current_candidate_count + round(required_meal_count * 0.8),
    round(required_meal_count * 2.8),
    additional_candidate_count,
)
```

### 후보 병합

```text
기존 Candidate Menus
+ 추가 RAG Candidate Menus
→ menu_id 및 매핑 기준으로 병합
```

추가 후보가 실제로 늘어난 경우에만 Recommendation과 Optimizer를 다시 실행합니다.

### Fallback 기록

```text
fallback_used
fallback_steps
final_candidate_count
warnings
candidate_diagnostics
```

대표 Fallback Step:

```json
{
  "reason": "optimizer_infeasible_additional_rag",
  "candidate_count": 252,
  "additional_candidate_count": 108,
  "result_count": 100,
  "merged_candidate_count": 180,
  "previous_solver_status": "INFEASIBLE"
}
```

<br>

## 22. INFEASIBLE 정책

관련 파일:

```text
modeling/services/optimizer/ortools/infeasible_policy.py
```

INFEASIBLE 정책은 실패 원인을 임의로 하나로 단정하지 않습니다.

실제 입력에서 활성화된 조건과 후보 진단 정보를 구조화하고, 사용자가 조정할 수 있는 Action을 제공합니다.

### 활성 Constraint Context

수집 가능한 Context:

```text
slot_requirement
candidate_pool
budget_constraint
repeat_constraint
preference_constraint
allergy_constraint
diversity_constraint
```

각 Context에는 실제 입력 Evidence가 포함됩니다.

예시:

```json
{
  "type": "repeat_constraint",
  "active": true,
  "evidence": {
    "max_repeat_per_menu": 2,
    "repeat_penalty_weight": 5000
  }
}
```

### Relaxation Action

| Context | Action |
|---|---|
| 예산 | `adjust_budget` |
| 식사 수 | `adjust_meal_count` |
| 후보 풀 | `request_more_candidates` |
| 선호 조건 | `expand_preferences` |
| 알레르기 | `review_allergy_alternatives` |
| 다양성 | `adjust_diversity` |
| 반복 제한 | `adjust_repeat_limit` |

알레르기 Action은 알레르기 조건 자체를 제거하는 기능이 아니라, 충돌하지 않는 대체 재료를 검토하도록 안내합니다.

### 진단 원칙

```text
Solver 실패 원인을 임의로 단정하지 않고,
실제 입력과 Candidate Diagnostics에 존재하는
활성 조건만 기록한다.
```

### 실험용 진단 분리

상세 Policy와 활성 Constraint Context는 서비스 Payload를 변경하지 않고 실험 Artifact에 저장합니다.

```text
서비스 응답
→ 기존 사용자 안내 구조 유지

Experiment Artifact
→ 상세 Policy와 Context 기록
```

### 사용자 안내 구조

```json
{
  "title": "현재 조건으로는 월간 식단 조합을 찾지 못했어요.",
  "description": "조건을 일부 조정하면 다시 생성할 수 있습니다.",
  "primary_actions": [],
  "recommended_actions": [],
  "diagnostic_summary": {}
}
```

주요 진단 필드:

```text
solver_status
monthly_budget
required_meal_count
budget_per_meal
available_recommendation_count
max_repeat_per_menu
optimizer_candidate_limit
used_optimizer_candidate_count
diversity_level
preferred_category_count
ingredient_preference_count
allergy_ingredient_count
```

<br>

## 23. Optimizer 결과 구조

성공 결과:

```json
{
  "success": true,
  "solver_status": "OPTIMAL",
  "selected_items": [
    {
      "day": 1,
      "meal_order": 1,
      "menu_index": 0,
      "menu_id": 101,
      "selected_menu": {}
    }
  ],
  "objective_value": 1234567,
  "message": "OR-Tools 월간 식단 최적화가 완료되었습니다.",
  "optimizer_config": {}
}
```

실패 결과:

```json
{
  "success": false,
  "solver_status": "INFEASIBLE",
  "selected_items": [],
  "objective_value": null,
  "message": "OR-Tools가 가능한 식단 조합을 찾지 못했습니다.",
  "optimizer_config": {}
}
```

### Config 추적

성공과 실패 결과 모두 실행 시 사용한 설정을 포함합니다.

```text
score_weight
cost_penalty_weight
cost_penalty_divisor
repeat_penalty_weight
repeat_penalty_growth
enable_nutrition_outlier_penalty
nutrition_outlier_penalty_weight
enable_protein_bonus
protein_bonus_weight
protein_bonus_cap_grams
enable_difficulty_bonus
difficulty_bonus_weight
max_repeat_per_menu
solver_time_limit_seconds
monthly_budget
required_meal_count
original_recommendation_count
used_optimizer_candidate_count
optimizer_candidate_multiplier
optimizer_candidate_limit
```

<br>

## 24. Plan 결과 매핑

관련 함수:

```python
build_ortools_monthly_plan(
    optimizer_result: dict,
    optimizer_input: dict,
    recommendations: list,
    profile: dict,
) -> dict
```

Solver가 선택한 `selected_items`를 다음 구조로 변환합니다.

```text
월간 Plan
└── days
    └── meals
        ├── selected_menu
        └── alternative_menus
```

Solver Status가 다음 두 값이 아니면 정상 Plan으로 매핑하지 않습니다.

```text
OPTIMAL
FEASIBLE
```

### Plan Summary

매핑 이후 다음 정보가 생성될 수 있습니다.

```text
required_meal_count
selected_menu_count
total_estimated_cost
average_daily_cost
average_protein
average_calories
duplicate_menu_count
average_difficulty_score
average_preference_score
average_diversity_score
```

이 Summary는 Style Validation과 최종 응답 구성에 사용됩니다.

<br>

## 25. 대체 메뉴 생성

OR-Tools는 대표 메뉴를 선택하고, Result Mapper는 Recommendation 후보를 이용해 대체 메뉴를 구성합니다.

현재 테스트 기준으로 각 식사에는 최대 두 개의 대체 메뉴가 포함됩니다.

검증 조건:

```text
선택 메뉴와 같은 menu_id 제외
대체 메뉴끼리 menu_id 중복 방지
후보가 없으면 빈 배열 반환
```

예시:

```json
{
  "selected_menu": {
    "menu_id": 1
  },
  "alternative_menus": [
    {
      "menu_id": 2
    },
    {
      "menu_id": 3
    }
  ]
}
```

후보가 하나뿐인 경우:

```json
{
  "alternative_menus": []
}
```

<br>

## 26. 실험 및 Snapshot

Optimizer는 단일 실행 결과만으로 정책을 결정하지 않고 실험 Snapshot과 Replay를 통해 가중치를 비교합니다.

대표 실험 요소:

```text
repeat_penalty_weight
repeat_penalty_growth
protein_bonus_weight
protein_bonus_cap_grams
difficulty_bonus_weight
nutrition_outlier_penalty_weight
candidate multiplier
solver time limit
diversity policy
```

대표 도구:

```text
experiments/tuning/grid_search_optimizer_tuning.py
experiments/tuning/replay_optimizer_snapshots.py
experiments/tuning/replay_optimizer_policy.py
experiments/tuning/extract_optimizer_snapshots.py
```

### Snapshot 목적

```text
동일한 Candidate Input
+ 서로 다른 Optimizer Config
→ 결과 비교
```

RAG를 다시 호출하지 않고 동일 후보 풀에서 정책 변화만 비교할 수 있습니다.

대표 비교 지표:

```text
solver_status
runtime
objective_value
validation_status
duplicate_rate
average_protein
average_difficulty_score
candidate_to_required_ratio
fallback 여부
```

<br>

## 27. 실행 및 테스트

프로젝트 루트에서 실행합니다.

### 비용 Penalty 확인

```bash
PYTHONPATH=modeling \
python - <<'PY'
from services.optimizer.ortools.monthly_plan_optimizer import (
    calculate_cost_penalty,
)

print(
    calculate_cost_penalty(
        estimated_cost=5000,
        cost_penalty_divisor=100,
    )
)
PY
```

예상 결과:

```text
50
```

### 최소 Solver 실행

```bash
PYTHONPATH=modeling \
python - <<'PY'
from services.optimizer.ortools.monthly_plan_optimizer import (
    solve_monthly_plan_with_ortools,
)

menus = [
    {
        "index": 0,
        "menu_id": 1,
        "final_score": 90,
        "estimated_cost": 3000,
        "protein": 30,
        "difficulty_score": 100,
        "nutrition_outlier_penalty": 0,
        "raw_menu": {
            "menu_id": 1,
            "name": "테스트 메뉴 A",
        },
    },
    {
        "index": 1,
        "menu_id": 2,
        "final_score": 80,
        "estimated_cost": 2500,
        "protein": 20,
        "difficulty_score": 80,
        "nutrition_outlier_penalty": 0,
        "raw_menu": {
            "menu_id": 2,
            "name": "테스트 메뉴 B",
        },
    },
]

optimizer_input = {
    "slots": [
        {"day": 1, "meal_order": 1},
        {"day": 1, "meal_order": 2},
    ],
    "menus": menus,
    "monthly_budget": 10000,
    "required_meal_count": 2,
    "max_repeat_per_menu": 1,
    "solver_time_limit_seconds": 3,
    "score_weight": 100,
    "cost_penalty_weight": 1,
    "cost_penalty_divisor": 100,
    "repeat_penalty_weight": 1500,
    "repeat_penalty_growth": "quadratic",
    "enable_nutrition_outlier_penalty": False,
    "nutrition_outlier_penalty_weight": 1,
    "enable_protein_bonus": False,
    "protein_bonus_weight": 0,
    "protein_bonus_cap_grams": 35,
    "enable_difficulty_bonus": False,
    "difficulty_bonus_weight": 0,
}

result = solve_monthly_plan_with_ortools(
    optimizer_input=optimizer_input,
)

print("success:", result["success"])
print("solver_status:", result["solver_status"])
print("objective_value:", result.get("objective_value"))
print("selected_items:", result["selected_items"])
PY
```

정상 실행 시 `OPTIMAL` 또는 `FEASIBLE`이 반환되어야 합니다.

### Optimizer 테스트

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/optimizer \
  modeling/tests/contract/test_optimizer_failure_response_contract.py \
  -q
```

### 문법 검사

```bash
python -m py_compile \
  modeling/services/optimizer/optimizer_input_builder.py \
  modeling/services/optimizer/ortools/monthly_plan_optimizer.py \
  modeling/services/optimizer/ortools/result_mapper.py \
  modeling/services/optimizer/ortools/infeasible_policy.py
```

### 전체 Modeling 테스트

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest modeling/tests -q
```

### 현재 확인된 테스트 범위

#### 실패 응답 Contract

```text
UNKNOWN
→ failure_reason = optimizer_unknown
→ monthly_plan.days = []

INFEASIBLE
→ failure_reason = optimizer_infeasible
```

Dispatcher가 Solver Status에 맞는 Failure Builder를 호출하는지도 검증합니다.

#### 성공 응답 Contract

```text
success = True
failure_reason = None
request_type = monthly_plan
```

#### 대체 메뉴

```text
대체 메뉴 두 개 생성
선택 메뉴 ID 제외
대체 메뉴 ID 중복 방지
대체 후보가 없으면 빈 배열
```

현재 CP-SAT Objective 각 경계값과 Constraint를 직접 검증하는 단위 테스트는 제한적입니다.

<br>

## 28. 현재 구현상 주의사항

### FEASIBLE도 성공 처리

시간 제한 내 최적해를 증명하지 못해도 모든 Hard Constraint를 만족하는 `FEASIBLE` 해가 있으면 월간 식단으로 사용합니다.

운영에서는 Solver Status와 Objective Value를 함께 모니터링해야 합니다.

### 월 예산이 없으면 Budget Constraint 비활성화

```text
monthly_budget ≤ 0
→ 예산 Hard Constraint 없음
```

이 경우 Cost Penalty만으로 저가 메뉴를 유도할 수 있지만 전체 비용 상한은 보장되지 않습니다.

### 가격이 0인 메뉴

가격이 없거나 0으로 매핑된 메뉴는:

```text
예산 Constraint 비용 = 0
Cost Penalty = 0
```

따라서 가격 누락 메뉴가 Objective에서 유리해질 수 있습니다. RAG 가격 품질 진단과 Recommendation 품질 감점을 함께 확인해야 합니다.

### 반복 Penalty는 단계별 누적

Quadratic 설정에서 세 번째 사용의 감점은 단순히 `weight × 4`만 적용되는 것이 아니라 두 번째 단계의 `weight × 1`도 함께 누적됩니다.

```text
3회 사용 총 감점
= weight × 1
+ weight × 4
```

### 후보 확장 시 선호 조건 완화

Retry 과정에서는 다음 조건이 완화됩니다.

```text
preferred_categories
ingredient_preferences
diversity_level
```

그러나 Allergy는 완화하지 않습니다.

최종 응답의 Fallback 정보에서 후보 확장이 발생했는지 확인해야 합니다.

### Style별 Bonus와 Recommendation 중복 반영

예를 들어 고단백은 다음 단계에서 여러 번 강조될 수 있습니다.

```text
Recommendation nutrition_score
Recommendation Style Soft Constraint
월간 Profile nutrition weight
Optimizer Protein Bonus
```

과도한 중복 가중이 발생하지 않는지 Snapshot Replay로 검증해야 합니다.

### Difficulty Bonus 의미

Difficulty Bonus는 `menu.difficulty`가 아니라 `difficulty_score`를 사용합니다.

```text
높은 difficulty_score
→ 사용자에게 조리 부담이 낮음
```

필드 이름만 보고 반대로 해석하지 않도록 주의해야 합니다.

### Nutrition Outlier Penalty 기본 비활성 가능성

Optimizer가 필드를 지원하더라도 다음 값이 `False`이면 Objective에 반영되지 않습니다.

```text
enable_nutrition_outlier_penalty
```

실제 실행 결과의 `optimizer_config`를 확인해야 현재 활성화 여부를 알 수 있습니다.

### Solver Worker 수 고정

```text
num_workers = 8
```

저사양 EC2에서는 CPU 수보다 Worker가 많을 수 있습니다. 실제 인스턴스 사양과 Solver Runtime을 함께 측정해야 합니다.

### Retry는 후보가 실제로 늘어난 경우 재실행

추가 RAG 요청을 수행해도 병합 후 후보 수가 증가하지 않으면 Recommendation과 Solver를 다시 실행하지 않습니다.

### 실패 원인을 단정하지 않음

INFEASIBLE은 예산, 후보 수, 반복 제한 등 여러 조건의 결합으로 발생할 수 있습니다.

현재 Policy는 단일 원인을 임의로 지정하지 않고 활성 Constraint와 Evidence를 제공합니다.

### 전용 Constraint 테스트 부족

현재 확인된 테스트는 응답 Contract와 대체 메뉴 매핑 중심입니다.

다음 항목은 별도 단위 테스트 보강 대상입니다.

```text
Slot당 정확히 하나 선택
월 예산 상한
최대 반복 횟수
Linear / Quadratic Repeat Penalty
Protein Cap
Difficulty Bonus
Nutrition Outlier Penalty
OPTIMAL / FEASIBLE 처리
후보 부족 사전 차단
예산 절대 불가능 사전 차단
Retry 후보 확장
```

<br>

## 29. 관련 문서

### Repository 상세 문서

- [`../../experiments/docs/modeling_validation_optimizer_report.md`](../../experiments/docs/modeling_validation_optimizer_report.md)  
  Style Validation, RAG 후보 품질, Optimizer Fallback, 반복 감점과 전체 검증 결과를 정리한 문서

- [`../../experiments/docs/optimizer_difficulty_diagnostics.md`](../../experiments/docs/optimizer_difficulty_diagnostics.md)  
  간편식 시나리오의 Difficulty Score 분포, 후보 풀 한계와 Validation 기준 분석 문서

### 프로젝트 설계 및 튜닝

- [📘 OR-Tools 기반 월간 식단 제약 최적화](https://app.notion.com/p/OR-Tools-36d9e3e335cc8094a75ddae49bbbc612?source=copy_link)  
  월간 식단의 결정 변수, 예산, 반복 제한과 Solver 기반 조합 최적화 설계

- [⚙️ OR-Tools 식단 최적화 Objective 가중치 튜닝](https://app.notion.com/p/OR-Tools-objective-3829e3e335cc80059b6fd19a0a1b26e6?source=copy_link)  
  Repeat Penalty, Protein Bonus, Difficulty Bonus와 Objective 가중치 실험 및 검증 과정

### 참고 자료

- [📚 OR-Tools 참고 자료](https://app.notion.com/p/Or-Tools-36c9e3e335cc804c8a22de0465e33507?source=copy_link)  
  OR-Tools와 CP-SAT의 기본 개념, 결정 변수, 제약조건 및 목적함수 학습 자료
