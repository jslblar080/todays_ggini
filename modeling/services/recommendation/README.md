# 🎯 Menu Recommendation Scoring

RAG에서 수집하고 정규화한 후보 메뉴를 사용자 Profile과 선택한 식단 스타일에 따라 평가하고, 추천 우선순위를 계산하는 모듈입니다.

예산, 영양, 선호도, 조리 난이도와 다양성 점수를 계산한 뒤 Profile의 가중치를 적용합니다. 이후 선택 스타일에 따른 Soft Constraint와 RAG 데이터 품질 감점을 반영해 최종 추천 점수를 생성합니다.

```text
RAG Candidate Menus
→ 알레르기·제외 재료 Hard Filter
→ 예산 점수 계산
→ 영양 점수 계산
→ 선호도 점수 계산
→ 조리 난이도 점수 계산
→ 다양성 점수 계산
→ Profile 가중치 적용
→ Style Soft Constraint 적용
→ 데이터 품질 Penalty 적용
→ Final Score 계산
→ 추천 이유 생성
→ 점수순 메뉴 선택
```

<br>

## 목차

1. [모듈 역할](#1-모듈-역할)
2. [전체 처리 흐름](#2-전체-처리-흐름)
3. [입력 데이터](#3-입력-데이터)
4. [알레르기 및 제외 재료 필터](#4-알레르기-및-제외-재료-필터)
5. [예산 점수](#5-예산-점수)
6. [영양 점수](#6-영양-점수)
7. [다이어트 점수](#7-다이어트-점수)
8. [고단백 점수](#8-고단백-점수)
9. [영양 균형 점수](#9-영양-균형-점수)
10. [선호도 점수](#10-선호도-점수)
11. [조리 난이도 점수](#11-조리-난이도-점수)
12. [다양성 점수](#12-다양성-점수)
13. [기본 가중 점수](#13-기본-가중-점수)
14. [Style Soft Constraint](#14-style-soft-constraint)
15. [RAG 데이터 품질 감점](#15-rag-데이터-품질-감점)
16. [영양 정보 누락 감점](#16-영양-정보-누락-감점)
17. [최종 점수](#17-최종-점수)
18. [추천 이유 생성](#18-추천-이유-생성)
19. [선택 스타일 기반 이유 필터링](#19-선택-스타일-기반-이유-필터링)
20. [순차 추천과 Top-N](#20-순차-추천과-top-n)
21. [MMR 및 Optimizer와의 역할 구분](#21-mmr-및-optimizer와의-역할-구분)
22. [반환 구조](#22-반환-구조)
23. [실행 및 검증](#23-실행-및-검증)
24. [파일 구조](#24-파일-구조)
25. [현재 구현상 주의사항](#25-현재-구현상-주의사항)

<br>

## 1. 모듈 역할

Recommendation 모듈은 후보 메뉴를 사용자 조건에 따라 점수화하고 정렬 가능한 추천 결과로 변환합니다.

주요 역할은 다음과 같습니다.

### 후보 안전성 확인

- 사용자가 입력한 알레르기 재료 확인
- 메뉴 재료와 RAG 알레르기 재료 목록 확인
- 제외 재료가 포함된 메뉴를 점수 계산 전에 제거

### 세부 점수 계산

- 예산 적합도
- 영양 적합도
- 음식 카테고리 및 재료군 선호도
- 사용자 요리 실력 대비 메뉴 난이도
- 기존 선택 메뉴 대비 다양성

### 후처리

- 식단 스타일에 따른 Soft Constraint
- RAG 데이터 품질 감점
- 영양 정보 누락 감점
- 사용자 친화형 추천 이유 생성
- 최종 점수 기반 순차 추천

<table style="background-color:#EAF4FF; border-left:6px solid #4D96D9; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>💡 핵심 역할</strong><br>
      Recommendation은 월간 식단 전체 조합을 결정하지 않습니다.
      각 후보 메뉴가 현재 사용자에게 얼마나 적합한지를 계산하고,
      이후 MMR 재랭킹과 OR-Tools Optimizer가 사용할 점수와 설명 정보를 생성합니다.
    </td>
  </tr>
</table>

<br>

## 2. 전체 처리 흐름

```text
Candidate Menus
        ↓
알레르기 및 제외 재료 확인
        ↓
제외 재료 포함 후보 제거
        ↓
남은 후보별 세부 점수 계산
        ├── budget_score
        ├── nutrition_score
        ├── preference_score
        ├── difficulty_score
        └── diversity_score
        ↓
Profile weights 적용
        ↓
base_final_score
        ↓
선택 스타일 Soft Constraint
        ↓
RAG 품질 및 영양 누락 Penalty
        ↓
final_score
        ↓
추천 이유 생성
        ↓
selected_style_focus_key 기반 이유 필터링
        ↓
현재 최고 점수 메뉴 선택
        ↓
선택 메뉴 ID 추가
        ↓
남은 후보의 다양성 점수 재계산
        ↓
Top-N까지 반복
```

핵심 함수:

```python
calculate_final_score(
    menu: dict,
    profile: dict,
    selected_menu_ids: list,
) -> dict
```

전체 추천 함수:

```python
recommend_menus(
    menus: list,
    profile: dict,
    top_n: int = 5,
) -> list
```

<br>

## 3. 입력 데이터

Recommendation은 크게 두 데이터를 입력으로 사용합니다.

### Candidate Menu

RAG Mapper가 변환한 메뉴 구조를 사용합니다.

대표 필드:

```text
menu_id
name
category
estimated_cost
calories
carbohydrate
protein
fat
difficulty
difficulty_detail
ingredients
ingredient_groups
ingredient_usages
similar_menu_ids
allergy_ingredients
recipe
rag_data_quality_score
rag_data_quality_issues
nutrition_outlier_issues
nutrition_outlier_penalty
is_extreme_nutrition_outlier
```

### Modeling Profile

Profile Builder와 Style Selection 단계에서 생성된 조건을 사용합니다.

대표 필드:

```text
goals
meal_budget
meal_calorie_target
cooking_skill
max_difficulty
preferred_categories
ingredient_preferences
allergy_ingredients
weights
diversity_penalty_strength
selected_style_goal
selected_style_focus_key
nutrition_detail_weights
```

<br>

## 4. 알레르기 및 제외 재료 필터

알레르기 재료는 점수 감점이 아니라 추천 대상에서 제거하는 Hard Filter입니다.

관련 함수:

```python
has_excluded_ingredient(
    menu: dict,
    excluded_ingredients: list,
) -> bool
```

검사 대상:

```text
menu.ingredients
+
menu.allergy_ingredients
```

처리 흐름:

```python
if has_excluded_ingredient(
    menu=menu,
    excluded_ingredients=profile.get("allergy_ingredients", []),
):
    continue
```

예시:

```text
사용자 알레르기: 새우
메뉴 ingredients: 양파, 새우, 마늘

→ 후보에서 제외
→ 점수 계산하지 않음
```

<table style="background-color:#FFF1E6; border-left:6px solid #E67E22; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>⚠️ 안전 조건</strong><br>
      예산, 선호도, 영양 품질과 난이도는 점수로 보정하지만,
      알레르기 조건은 사용자 안전과 직접 관련되므로 후보에서 즉시 제외합니다.
    </td>
  </tr>
</table>

<br>

## 5. 예산 점수

관련 함수:

```python
calculate_budget_score(
    menu_cost: int | None,
    meal_budget: int,
) -> float
```

### 가격 정보가 없는 경우

메뉴 예상 가격이 없거나 0 이하이면 중립 점수 `70점`을 부여합니다.

```text
menu_cost 없음 또는 0 이하
→ 70점
```

한 끼 예산이 0 이하인 경우에도 판단할 수 없으므로 `70점`입니다.

### 예산 이내

```text
menu_cost ≤ meal_budget
→ 100점
```

### 예산 초과

```text
budget_score
= 100
- ((menu_cost - meal_budget) ÷ meal_budget × 100)
```

점수는 최소 `0점`으로 제한합니다.

### 계산 예시

```text
한 끼 예산: 5,000원
메뉴 비용: 6,000원

초과 금액: 1,000원
초과율: 20%

budget_score
= 100 - 20
= 80점
```

<br>

## 6. 영양 점수

관련 함수:

```python
calculate_nutrition_score(
    menu: dict,
    profile: dict,
) -> float
```

영양 점수는 다음 세 가지 세부 기준으로 구성됩니다.

```text
diet
high_protein
balance
```

메뉴 영양 정보는 직접 필드와 `nutrient_summary` 구조를 모두 지원합니다.

관련 함수:

```python
get_menu_nutrients(menu: dict) -> dict
```

### 목표별 평가

| 사용자 목표 | 적용 점수 |
|---|---|
| 다이어트 | `diet` |
| 고단백 | `high_protein` |
| 영양 균형 | `balance` |

복수 목표가 있으면 적용된 세부 점수의 평균을 사용합니다.

```text
다이어트 + 고단백
→ (diet_score + high_protein_score) ÷ 2
```

영양 관련 목표가 없다면 중립 점수 `70점`을 반환합니다.

### 선택 스타일 세부 가중치

Profile에 `nutrition_detail_weights`가 있으면 기본 목표 평균보다 우선 적용합니다.

```text
weighted_score
= Σ(세부 영양 점수 × 세부 가중치)
÷ 전체 가중치 합
```

사용 가능한 세부 키:

```text
diet
high_protein
balance
```

<br>

## 7. 다이어트 점수

관련 함수:

```python
calculate_diet_score(
    calories: float,
    fat: float,
    meal_calorie_target: float | None = None,
) -> float
```

### 지방 우선 제한

지방이 지나치게 높으면 칼로리 조건과 관계없이 상한 점수가 적용됩니다.

| 지방 | 점수 |
|---:|---:|
| `35g 이상` | `35` |
| `30g 이상` | `45` |
| `25g 이상` | `60` |

### 사용자별 끼니 목표 칼로리가 있는 경우

| 조건 | 점수 |
|---|---:|
| 목표의 65% 이상~목표 이하, 지방 20g 이하 | `100` |
| 목표의 115% 이하, 지방 22g 이하 | `90` |
| 목표의 130% 이하 | `75` |
| 목표의 150% 이하 | `55` |
| 그 이상 | `40` |

목표 칼로리보다 지나치게 낮은 메뉴도 최고 점수 조건에서는 제외됩니다.

```text
최고점 하한
= meal_calorie_target × 0.65
```

### 사용자별 목표가 없는 경우

| 조건 | 점수 |
|---|---:|
| 500kcal 이하, 지방 15g 이하 | `100` |
| 650kcal 이하, 지방 20g 이하 | `90` |
| 800kcal 이하, 지방 22g 이하 | `75` |
| 950kcal 이하 | `55` |
| 그 이상 | `40` |

<br>

## 8. 고단백 점수

관련 함수:

```python
calculate_high_protein_score(
    protein: float,
    calories: float,
    meal_calorie_target: float | None = None,
) -> float
```

### 단백질 기본 점수

| 단백질 | 점수 |
|---:|---:|
| `35g 이상` | `100` |
| `30g 이상` | `95` |
| `25g 이상` | `90` |
| `20g 이상` | `80` |
| `15g 이상` | `65` |
| `10g 이상` | `50` |
| `10g 미만` | `35` |

### 과도한 칼로리 보정

사용자별 끼니 목표 칼로리가 있으면 과도한 열량을 감점합니다.

| 칼로리 조건 | 추가 감점 |
|---|---:|
| 목표의 160% 초과 | `-20` |
| 목표의 135% 초과 | `-10` |

최종 점수는 최소 `0점`으로 제한합니다.

<br>

## 9. 영양 균형 점수

관련 함수:

```python
calculate_balanced_nutrition_score(
    calories: float,
    carbohydrate: float,
    protein: float,
    fat: float,
    meal_calorie_target: float | None = None,
) -> float
```

### 영양소 정보가 없는 경우

```text
carbohydrate + protein + fat ≤ 0
→ 60점
```

### 영양소 비율

현재 구현은 각 영양소의 g 값을 전체 g 합으로 나누어 비율을 계산합니다.

```text
탄수화물 비율
= carbohydrate ÷ total_macro

단백질 비율
= protein ÷ total_macro

지방 비율
= fat ÷ total_macro
```

### 매우 적합 기준

| 항목 | 허용 범위 |
|---|---|
| 탄수화물 비율 | `0.45~0.65` |
| 단백질 비율 | `0.15~0.35` |
| 지방 비율 | `0.15~0.35` |
| 칼로리 | 목표의 `80~120%` |

모든 조건을 만족하면 `100점`입니다.

### 적합 기준

| 항목 | 허용 범위 |
|---|---|
| 탄수화물 비율 | `0.35~0.70` |
| 단백질 비율 | `0.10~0.40` |
| 지방 비율 | `0.10~0.45` |
| 칼로리 | 목표의 `65~135%` |

모든 조건을 만족하면 `80점`입니다.

그 외에는 `60점`을 반환합니다.

### 끼니 목표가 없는 경우

| 평가 | 칼로리 범위 |
|---|---|
| 매우 적합 | `400~850kcal` |
| 적합 | `350~950kcal` |

<br>

## 10. 선호도 점수

관련 함수:

```python
calculate_preference_score(
    menu: dict,
    profile: dict,
) -> float
```

선호도는 카테고리와 재료군 점수를 각각 50%씩 반영합니다.

```text
preference_score
= category_score × 0.5
+ ingredient_score × 0.5
```

### 카테고리 점수

관련 함수:

```python
calculate_category_score(
    menu_category: str,
    preferred_categories: list[str],
) -> float
```

| 조건 | 점수 |
|---|---:|
| `"상관없음"` 선택 | `70` |
| 메뉴 카테고리 일치 | `100` |
| 불일치 | `40` |

### 재료군 점수

관련 함수:

```python
calculate_ingredient_score(
    menu_ingredient_groups: list[str],
    ingredient_preferences: list[str],
) -> float
```

계산식:

```text
재료군 점수
= 일치한 재료군 수
÷ 사용자가 선택한 선호 재료군 수
× 100
```

선호 재료군이 없거나 메뉴 재료군이 없으면 중립 점수 `50점`입니다.

최대 점수는 `100점`으로 제한합니다.

<br>

## 11. 조리 난이도 점수

관련 함수:

```python
calculate_difficulty_score(
    menu_difficulty: int,
    cooking_skill: int,
) -> float
```

메뉴 난이도가 사용자 요리 실력 이하이면 `100점`입니다.

```text
menu_difficulty ≤ cooking_skill
→ 100점
```

사용자 실력보다 어려우면 단계 차이마다 `30점`을 감점합니다.

```text
difficulty_score
= 100
- (menu_difficulty - cooking_skill) × 30
```

### 예시

| 사용자 실력 | 메뉴 난이도 | 점수 |
|---:|---:|---:|
| 2 | 2 | `100` |
| 2 | 3 | `70` |
| 2 | 4 | `40` |
| 2 | 5 | `10` |

최소 점수는 `0점`입니다.

<br>

## 12. 다양성 점수

관련 함수:

```python
calculate_diversity_score(
    menu: dict,
    selected_menu_ids: list,
    penalty_strength: float,
) -> float
```

현재 후보의 `similar_menu_ids` 안에 이미 선택된 메뉴가 존재하는지 확인합니다.

### 유사 메뉴가 없는 경우

```text
diversity_score = 100
```

### 유사 메뉴가 있는 경우

```text
diversity_score
= 100 - (100 × diversity_penalty_strength)
```

Profile의 다양성 수준별 값:

| 다양성 수준 | 감점 강도 | 유사 메뉴 점수 |
|---|---:|---:|
| 낮음 | `0.20` | `80` |
| 보통 | `0.45` | `55` |
| 높음 | `0.65` | `35` |

관련 Profile 필드:

```text
diversity_penalty_strength
```

<br>

## 13. 기본 가중 점수

세부 점수는 Profile의 목표별 가중치를 적용해 기본 최종 점수로 결합합니다.

```text
base_final_score
= budget_score × weights.budget
+ nutrition_score × weights.nutrition
+ preference_score × weights.preference
+ difficulty_score × weights.difficulty
+ diversity_score × weights.diversity
```

관련 Profile 가중치:

```text
budget
nutrition
preference
difficulty
diversity
```

예시:

```text
budget_score     = 100
nutrition_score  = 80
preference_score = 70
difficulty_score = 100
diversity_score  = 55

weights:
budget     = 0.15
nutrition  = 0.40
preference = 0.15
difficulty = 0.10
diversity  = 0.20

base_final_score
= 100×0.15
+ 80×0.40
+ 70×0.15
+ 100×0.10
+ 55×0.20

= 78.5
```

<br>

## 14. Style Soft Constraint

관련 함수:

```python
calculate_style_soft_constraint_score(
    menu: dict,
    profile: dict,
    scores: dict,
) -> float
```

선택한 식단 스타일에 적합한 메뉴를 가점하고, 적합도가 낮은 메뉴는 감점합니다.

Soft Constraint이므로 조건을 만족하지 않는 메뉴를 제거하지 않습니다.

스타일 판단 우선순위:

```text
selected_style_goal
→ 없으면 source_goal
```

현재 별도 보정을 적용하는 스타일 목표는 다음 두 가지입니다.

```text
고단백
간편식
```

### 고단백 Soft Constraint

관련 함수:

```python
calculate_high_protein_soft_constraint_score(
    menu: dict,
) -> float
```

| 단백질 | 보정 점수 |
|---:|---:|
| `35g 이상` | `+3` |
| `30g 이상` | `+2` |
| `25g 이상` | `+1` |
| `22g 이상` | `0` |
| `18g 이상` | `-2` |
| `18g 미만` | `-4` |

고단백 스타일에서 단백질 적합성을 반영하지만, 보정 폭을 제한해 다양성이 지나치게 훼손되지 않도록 합니다.

### 간편식 Soft Constraint

관련 함수:

```python
calculate_easy_cooking_soft_constraint_score(
    scores: dict,
) -> float
```

| Difficulty Score | 보정 점수 |
|---:|---:|
| `90 이상` | `+8` |
| `80 이상` | `+6` |
| `70 이상` | `+4` |
| `60 이상` | `0` |
| `40 이상` | `-6` |
| `40 미만` | `-10` |

간편식 스타일은 사용자 실력 대비 조리 부담이 적은 메뉴를 더 강하게 우선합니다.

### 기타 스타일

고단백과 간편식 이외의 스타일은 별도 Soft Constraint를 적용하지 않습니다.

```text
style_soft_constraint_score = 0
```

<br>

## 15. RAG 데이터 품질 감점

관련 함수:

```python
calculate_rag_data_quality_penalty(
    menu: dict,
) -> float
```

RAG Mapper가 생성한 `rag_data_quality_score`를 이용해 품질이 낮은 후보를 감점합니다.

| RAG 품질 점수 | 감점 |
|---:|---:|
| `80 이상` | `0` |
| `60 이상` | `3` |
| `40 이상` | `7` |
| `20 이상` | `12` |
| `20 미만` | `18` |

### 품질 점수가 없는 경우

Mock 또는 Local 데이터에는 품질 점수가 없을 수 있습니다.

```text
rag_data_quality_score = None
→ 감점 0
```

숫자로 변환할 수 없는 값도 감점하지 않습니다.

### 처리 방식

품질이 낮더라도 후보를 즉시 제외하지 않습니다.

```text
후보 부족 방지
→ 후보 유지
→ final_score에서 감점
```

<br>

## 16. 영양 정보 누락 감점

관련 함수:

```python
calculate_nutrition_missing_penalty(
    menu: dict,
    profile: dict,
) -> float
```

메뉴의 핵심 영양 정보가 0이거나 누락된 경우 추가 감점을 적용합니다.

### 기본 감점

| 누락 조건 | 감점 |
|---|---:|
| calories 0 이하 | `+5` |
| protein 0 이하 | `+5` |
| 탄수화물·단백질·지방 모두 0 이하 | `+8` |

감점은 누적됩니다.

### 최대 기본 감점 예시

```text
calories 없음       +5
protein 없음        +5
3대 영양소 모두 없음 +8
────────────────────
기본 감점           18
```

### 영양 중심 목표 가중

다음 목표가 하나라도 있으면 전체 감점을 `1.5배` 적용합니다.

```text
고단백
다이어트
영양 균형
```

예시:

```text
기본 누락 감점: 18
영양 중심 목표 선택

18 × 1.5
= 27점 감점
```

관련 영양 정보는 직접 필드와 `nutrient_summary`를 함께 확인합니다.

<br>

## 17. 최종 점수

전체 품질 감점은 다음 두 값을 합산합니다.

```text
total_quality_penalty
= rag_data_quality_penalty
+ nutrition_missing_penalty
```

최종 점수 공식:

```text
final_score
= base_final_score
+ style_soft_constraint_score
- total_quality_penalty
```

점수가 음수가 되지 않도록 최소값을 `0`으로 제한합니다.

```python
final_score = max(final_score, 0)
```

### 계산 예시

```text
base_final_score            78.5
style_soft_constraint_score +8
rag_data_quality_penalty    -3
nutrition_missing_penalty   -0
──────────────────────────────
final_score                 83.5
```

<br>

## 18. 추천 이유 생성

각 세부 점수에 대한 사용자 친화형 설명을 생성합니다.

관련 함수:

```python
build_recommendation_reasons(
    menu: dict,
    profile: dict,
    selected_menu_ids: list,
    scores: dict,
) -> list[dict]
```

생성되는 이유 유형:

```text
budget
nutrition
preference
difficulty
diversity
```

### 공통 반환 구조

```json
{
  "type": "budget",
  "score": 100,
  "level": "매우 적합",
  "message": "한 끼 예산 이내에 안정적으로 들어오는 메뉴입니다."
}
```

### 점수 수준 변환

관련 함수:

```python
score_to_level(score: float) -> str
```

| 점수 | 수준 |
|---:|---|
| `90 이상` | 매우 적합 |
| `75 이상` | 적합 |
| `60 이상` | 보통 |
| `40 이상` | 낮음 |
| `40 미만` | 부적합 |

### 예산 이유

다음 정보를 이용해 설명합니다.

- 한 끼 예산
- 메뉴 예상 비용
- 남은 금액과 비율
- 초과 금액과 초과율
- 예산 점수

### 영양 이유

선택된 목표에 따라 설명을 조합합니다.

- 다이어트: 칼로리와 지방
- 고단백: 단백질 함량
- 영양 균형: 탄수화물·단백질·지방 비율

복수 목표라면 여러 문장을 결합합니다.

### 선호도 이유

다음 조건의 일치 여부를 설명합니다.

- 선호 음식 카테고리
- 선호 재료군
- 실제 메뉴 카테고리
- 메뉴 재료군

### 난이도 이유

다음 정보를 설명에 포함합니다.

- 메뉴 난이도
- 사용자 가능 난이도
- 난이도 단계 차이
- 재료 수
- 조리 단계 수
- 조리 시간

### 다양성 이유

최근 선택 메뉴와 현재 후보의 `similar_menu_ids` 관계를 바탕으로 반복 가능성을 설명합니다.

<br>

## 19. 선택 스타일 기반 이유 필터링

월간 식단 응답에서는 모든 이유를 노출하지 않고 사용자가 선택한 스타일의 핵심 기준만 보여줄 수 있습니다.

관련 함수:

```python
get_reason_type_by_focus_key(
    focus_key: str | None,
) -> str | None
```

```python
filter_reasons_by_focus_key(
    reasons: list[dict],
    profile: dict,
) -> list[dict]
```

### Focus Key 매핑

| Focus Key | 이유 Type |
|---|---|
| `budget` | `budget` |
| `nutrition` | `nutrition` |
| `difficulty` | `difficulty` |
| `preference` | `preference` |
| `diversity` | `diversity` |

Profile 필드:

```text
selected_style_focus_key
```

### Fallback

다음 경우에는 전체 이유를 반환합니다.

- Focus Key가 없음
- 지원하지 않는 Focus Key
- 해당 Type의 이유가 생성되지 않음

<br>

## 20. 순차 추천과 Top-N

관련 함수:

```python
recommend_menus(
    menus: list,
    profile: dict,
    top_n: int = 5,
) -> list
```

Recommendation은 후보 전체를 한 번만 점수화해 정렬하지 않습니다.

### 순차 선택 방식

```text
1. 모든 남은 후보 점수 계산
2. final_score 내림차순 정렬
3. 최고 점수 메뉴 선택
4. selected_menu_ids에 추가
5. 선택된 후보를 목록에서 제거
6. 남은 후보의 다양성 점수 재계산
7. Top-N까지 반복
```

정렬 코드:

```python
scored_menus.sort(
    key=lambda item: item["result"]["final_score"],
    reverse=True,
)
```

### 다양성 재계산

메뉴가 하나 선택될 때마다 `selected_menu_ids`가 변경됩니다.

따라서 다음 메뉴의 `diversity_score`와 `final_score`도 달라질 수 있습니다.

```text
첫 번째 메뉴
→ 기본 점수 중심

두 번째 메뉴부터
→ 기존 선택 메뉴와 유사성 반영
```

### 월간 식단 후보 처리

월간 식단에서는 `top_n`에 전체 후보 수를 전달해 모든 후보를 순차적으로 다시 평가할 수 있습니다.

```python
recommend_menus(
    menus=candidate_menus,
    profile=monthly_profile,
    top_n=len(candidate_menus),
)
```

<br>

## 21. MMR 및 Optimizer와의 역할 구분

Recommendation, MMR과 Optimizer는 모두 메뉴 선택에 관여하지만 역할이 다릅니다.

### Recommendation

```text
사용자 Profile
+ 메뉴 속성
+ 이미 선택된 유사 메뉴
→ final_score
```

주요 기준:

- 예산
- 영양
- 선호도
- 난이도
- 다양성
- 선택 스타일
- 데이터 품질

### MMR

관련 위치:

```text
modeling/services/plan/mmr_service.py
modeling/services/plan/menu_diversity_service.py
```

MMR은 Recommendation이 생성한 `final_score`와 후보 간 유사도를 다시 결합합니다.

```text
final_score
+ 후보 간 유사도
→ mmr_score
→ 재랭킹
```

Recommendation의 다양성 점수는 최종 점수의 구성 요소이고, MMR은 후속 재랭킹 단계입니다.

### OR-Tools Optimizer

관련 위치:

```text
modeling/services/optimizer/
```

Optimizer는 개별 메뉴 하나가 아니라 전체 기간의 식단 조합을 결정합니다.

```text
추천 후보 점수
+ 예산
+ 반복 제한
+ 메뉴 수
+ 전체 식단 조건
→ 월간 식단 조합
```

<table style="background-color:#FFF6C7; border-left:6px solid #E6C85C; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>⭐ 역할 정리</strong><br>
      Recommendation은 후보별 사용자 적합도를 계산하고,
      MMR은 후보 간 유사성을 고려해 순서를 보정하며,
      Optimizer는 전체 기간에 배치할 메뉴 조합을 결정합니다.
    </td>
  </tr>
</table>

<br>

## 22. 반환 구조

`calculate_final_score()`는 메뉴 기본 정보와 점수·진단 정보를 결합해 반환합니다.

대표 구조:

```json
{
  "menu_id": "menu_001",
  "name": "닭가슴살 채소볶음",
  "category": "한식",
  "final_score": 83.5,
  "base_final_score": 78.5,
  "style_soft_constraint_score": 8,
  "scores": {
    "budget": 100,
    "nutrition": 80,
    "preference": 70,
    "difficulty": 100,
    "diversity": 55
  },
  "reasons": [
    {
      "type": "difficulty",
      "score": 100,
      "level": "매우 적합",
      "message": "사용자 가능 난이도 이내에 있어 충분히 조리 가능한 메뉴입니다."
    }
  ],
  "estimated_cost": 3200,
  "calories": 620,
  "protein": 32,
  "carbohydrate": 65,
  "fat": 18,
  "difficulty": 2,
  "rag_data_quality_score": 80,
  "rag_data_quality_penalty": 0,
  "nutrition_missing_penalty": 0,
  "total_quality_penalty": 0
}
```

### 주요 점수 필드

| 필드 | 의미 |
|---|---|
| `scores` | 다섯 가지 세부 점수 |
| `base_final_score` | Profile 가중치 적용 결과 |
| `style_soft_constraint_score` | 스타일 적합도 보정 |
| `rag_data_quality_penalty` | RAG 데이터 품질 감점 |
| `nutrition_missing_penalty` | 영양 정보 누락 감점 |
| `total_quality_penalty` | 전체 품질 감점 |
| `final_score` | 최종 추천 점수 |
| `reasons` | 사용자에게 노출할 추천 이유 |

### 원본 진단 필드 유지

다음 RAG 진단 필드도 추천 결과에 유지됩니다.

```text
rag_data_quality_issues
nutrition_outlier_issues
nutrition_outlier_penalty
is_extreme_nutrition_outlier
pricing_status
ingredient_costs
```

현재 `nutrition_outlier_penalty`는 반환 데이터에 포함되지만 Recommendation의 `total_quality_penalty`에 직접 더해지지는 않습니다.

<br>

## 23. 실행 및 검증

프로젝트 루트에서 실행합니다.

### 개별 점수 확인

```bash
PYTHONPATH=modeling \
python - <<'PY'
from services.recommendation.scoring_service import (
    calculate_budget_score,
    calculate_difficulty_score,
)

print(
    "budget_score:",
    calculate_budget_score(
        menu_cost=6000,
        meal_budget=5000,
    ),
)

print(
    "difficulty_score:",
    calculate_difficulty_score(
        menu_difficulty=4,
        cooking_skill=2,
    ),
)
PY
```

예상 결과:

```text
budget_score: 80.0
difficulty_score: 40
```

### 전체 최종 점수 확인

```bash
PYTHONPATH=modeling \
python - <<'PY'
from services.recommendation.recommendation_service import (
    calculate_final_score,
)

menu = {
    "menu_id": "menu_test",
    "name": "닭가슴살 채소볶음",
    "category": "한식",
    "estimated_cost": 3200,
    "calories": 620,
    "carbohydrate": 65,
    "protein": 32,
    "fat": 18,
    "difficulty": 2,
    "ingredients": ["닭가슴살", "양파"],
    "ingredient_groups": ["육류", "채소류"],
    "similar_menu_ids": [],
    "allergy_ingredients": [],
    "rag_data_quality_score": 100,
}

profile = {
    "goals": ["고단백"],
    "meal_budget": 5000,
    "meal_calorie_target": 650,
    "cooking_skill": 2,
    "max_difficulty": 2,
    "preferred_categories": ["한식"],
    "ingredient_preferences": ["육류", "채소류"],
    "weights": {
        "budget": 0.15,
        "nutrition": 0.45,
        "preference": 0.15,
        "difficulty": 0.10,
        "diversity": 0.15,
    },
    "diversity_penalty_strength": 0.45,
    "selected_style_goal": "고단백",
}

result = calculate_final_score(
    menu=menu,
    profile=profile,
    selected_menu_ids=[],
)

print("scores:", result["scores"])
print("base_final_score:", result["base_final_score"])
print(
    "style_soft_constraint_score:",
    result["style_soft_constraint_score"],
)
print("total_quality_penalty:", result["total_quality_penalty"])
print("final_score:", result["final_score"])
print("reasons:", result["reasons"])
PY
```

### 알레르기 필터 확인

```bash
PYTHONPATH=modeling \
python - <<'PY'
from services.recommendation.recommendation_service import (
    has_excluded_ingredient,
)

menu = {
    "ingredients": ["양파", "새우"],
    "allergy_ingredients": ["갑각류"],
}

print(
    has_excluded_ingredient(
        menu=menu,
        excluded_ingredients=["새우"],
    )
)
PY
```

예상 결과:

```text
True
```

### 문법 검사

```bash
python -m py_compile \
  modeling/services/recommendation/recommendation_service.py \
  modeling/services/recommendation/scoring_service.py
```

### 전체 Modeling 테스트

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest modeling/tests -q
```

<table style="background-color:#FFF1E6; border-left:6px solid #E67E22; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>⚠️ 테스트 현황</strong><br>
      현재 검색된 테스트 중 Recommendation의 개별 점수 공식과 Soft Constraint를
      직접 검증하는 전용 단위 테스트는 없습니다.
      현재는 전체 검증 파이프라인과 실험 결과를 통해 간접적으로 검증하고 있습니다.
    </td>
  </tr>
</table>

<br>

## 24. 파일 구조

```text
modeling/
├── services/
│   └── recommendation/
│       ├── __init__.py
│       ├── recommendation_service.py
│       ├── scoring_service.py
│       └── README.md
│
├── services/
│   ├── profile/
│   │   └── weight_service.py
│   ├── rag/
│   │   └── rag_response_mapper.py
│   ├── style/
│   │   └── style_selection_service.py
│   ├── plan/
│   │   ├── mmr_service.py
│   │   └── menu_diversity_service.py
│   └── optimizer/
│
└── tests/
```

### 파일별 역할

| 파일 | 역할 |
|---|---|
| `recommendation_service.py` | 최종 점수, Soft Constraint, 품질 감점, 추천 이유 및 순차 선택 |
| `scoring_service.py` | 예산·영양·선호·난이도·다양성 점수 계산 |
| `weight_service.py` | 사용자 목표별 세부 점수 가중치 생성 |
| `rag_response_mapper.py` | RAG 품질 점수와 영양 이상치 진단 생성 |
| `style_selection_service.py` | 선택 스타일을 월간 Profile에 적용 |
| `mmr_service.py` | Recommendation 이후 다양성 재랭킹 |

<br>

## 25. 현재 구현상 주의사항

### 알레르기 검사는 문자열 완전 일치

현재 제외 재료 검사는 다음 목록에서 동일한 문자열이 존재하는지 확인합니다.

```text
ingredients
allergy_ingredients
```

따라서 다음 표현 차이는 자동으로 같은 재료로 판단하지 못할 수 있습니다.

```text
새우
칵테일새우
냉동 새우
갑각류
```

Backend 또는 RAG 단계에서 알레르기 재료명 표준화가 필요할 수 있습니다.

### 영양 균형 비율은 g 기준

현재 영양 균형 점수는 탄수화물, 단백질과 지방의 g 값을 직접 합산해 비율을 구합니다.

지방은 g당 9kcal, 탄수화물과 단백질은 g당 4kcal이므로 에너지 비율과는 다릅니다.

```text
현재 구현
→ 영양소 중량 비율

에너지 기준 비율이 필요한 경우
→ carbohydrate×4, protein×4, fat×9 사용 필요
```

### 고단백 점수가 두 단계에서 반영됨

고단백 목표는 다음 두 곳에서 반영될 수 있습니다.

```text
nutrition_score
→ 단백질 함량 중심 평가

style_soft_constraint_score
→ 선택 스타일이 고단백인 경우 추가 보정
```

이는 중복 오류라기보다 고단백을 기본 목표와 선택 스타일 양쪽에서 강조하는 구조입니다. 보정 폭이 적절한지는 실험 결과로 확인해야 합니다.

### 간편식 Soft Constraint 보정 폭이 큼

간편식 스타일은 최대 `+8`, 최소 `-10`을 적용합니다.

고단백의 `+3~-4`보다 영향이 크므로 간편식 스타일에서 조리 난이도가 최종 순위에 강하게 반영됩니다.

### 품질 감점 중복 가능성

영양 정보 누락은 다음 두 경로에서 반영될 수 있습니다.

```text
rag_data_quality_score 하락
→ rag_data_quality_penalty

calories 또는 protein 누락
→ nutrition_missing_penalty
```

의도적으로 영양 정보 누락을 강하게 억제하는 구조지만, 감점이 과도하지 않은지 검증이 필요합니다.

### Nutrition Outlier Penalty는 직접 합산되지 않음

추천 결과에는 다음 값이 포함됩니다.

```text
nutrition_outlier_penalty
```

하지만 현재 Recommendation의 `total_quality_penalty`는 다음 두 값만 합산합니다.

```text
rag_data_quality_penalty
nutrition_missing_penalty
```

따라서 `nutrition_outlier_penalty`는 Recommendation 최종 점수에 별도로 직접 차감되지 않습니다. 다만 RAG 품질 이슈와 Optimizer 설정에서 간접적으로 반영될 수 있습니다.

### 선호 카테고리 중립 표현 차이

User Profile Validator는 다음 값을 지원합니다.

```text
다 좋아요
```

Recommendation의 카테고리 중립 처리는 다음 값을 확인합니다.

```text
상관없음
```

RAG Fallback이나 내부 Profile에서는 두 표현이 서로 다르게 사용될 수 있으므로 서비스 간 표현 통일을 검토할 필요가 있습니다.

### 추천 순위는 고정 정렬이 아님

`recommend_menus()`는 메뉴를 하나 선택할 때마다 다양성 점수를 다시 계산합니다.

따라서 후보 하나의 최종 점수는 선택 순서에 따라 달라질 수 있습니다.

```text
동일 후보 목록
+ selected_menu_ids 변화
→ diversity_score 변화
→ final_score 변화
```

### 추천 이유와 점수 기준 일부 차이

영양 점수의 영양 균형 계산은 사용자별 `meal_calorie_target`을 사용할 수 있지만, 현재 영양 균형 추천 메시지는 고정 칼로리 범위인 `400~850`, `350~950`을 기준으로 설명합니다.

점수 계산과 메시지 설명 기준이 완전히 동일하지 않을 수 있으므로 사용자 설명 정합성을 검토할 수 있습니다.

### Recommendation 전용 단위 테스트 부재

현재 API 수준에서는 `selected_style` 요청 검증 테스트가 존재하지만, 다음 계산을 직접 검증하는 전용 테스트는 확인되지 않았습니다.

```text
budget_score
nutrition_score
preference_score
difficulty_score
diversity_score
style_soft_constraint_score
quality_penalty
final_score
```

점수 정책 변경 시 회귀를 방지하려면 함수별 경계값 테스트를 추가하는 것이 좋습니다.

<table style="background-color:#FFF6C7; border-left:6px solid #E6C85C; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>⭐ 설계 요약</strong><br>
      Recommendation 모듈은 사용자 목표별 가중 점수를 기반으로 후보 메뉴의 적합도를 계산하고,
      선택 스타일과 RAG 데이터 신뢰도를 추가 반영합니다.
      알레르기는 Hard Filter로 처리하고, 나머지 조건은 점수와 Soft Constraint로 조정하여
      후보 부족을 줄이면서 사용자 맞춤 추천 품질을 유지합니다.
    </td>
  </tr>
</table>
