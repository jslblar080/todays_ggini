# 🎨 Meal Style Candidate & Selection

사용자의 목표를 기반으로 서로 다른 방향의 식단 스타일 후보를 생성하고, 사용자가 선택한 스타일을 월간 식단 생성 Profile에 반영하는 모듈입니다.

Style 모듈은 단순히 카드 이름만 생성하지 않습니다. 각 스타일에 맞게 Recommendation 가중치를 조정하고, 샘플 식단을 구성한 뒤 화면 표시용 점수와 설명을 반환합니다. 이후 사용자가 선택한 스타일은 월간 Recommendation, MMR 기반 메뉴 선택, OR-Tools 최적화와 Style Validation에 연결됩니다.

```text
사용자 Profile
→ 목표 기반 Style 후보 3개 생성
→ Style별 가중치 강화
→ 후보 메뉴 재추천
→ 스타일 간 메뉴 중복 최소화
→ 샘플 식단 구성
→ 화면 표시 점수 생성
→ 사용자 Style 선택
→ 월간 Profile 가중치 조정
→ Recommendation 및 Plan에 반영
→ 월간 결과 Style Validation
```

<br>

## 목차

1. [모듈 역할](#1-모듈-역할)
2. [전체 처리 흐름](#2-전체-처리-흐름)
3. [지원하는 식단 스타일](#3-지원하는-식단-스타일)
4. [Style 후보 3개 생성](#4-style-후보-3개-생성)
5. [Style 샘플 가중치 강화](#5-style-샘플-가중치-강화)
6. [Style 전용 Profile 생성](#6-style-전용-profile-생성)
7. [Style별 후보 메뉴 추천](#7-style별-후보-메뉴-추천)
8. [스타일 간 메뉴 중복 제어](#8-스타일-간-메뉴-중복-제어)
9. [샘플 식단 구성](#9-샘플-식단-구성)
10. [화면 표시 점수](#10-화면-표시-점수)
11. [Style Candidate 응답 구조](#11-style-candidate-응답-구조)
12. [선택 Style 요약](#12-선택-style-요약)
13. [선택 Style의 월간 Profile 반영](#13-선택-style의-월간-profile-반영)
14. [영양 세부 가중치](#14-영양-세부-가중치)
15. [Recommendation 연동](#15-recommendation-연동)
16. [월간 메뉴 선택 우선순위](#16-월간-메뉴-선택-우선순위)
17. [Style Validation](#17-style-validation)
18. [후보 풀 난이도 진단](#18-후보-풀-난이도-진단)
19. [보조 경고와 상태 보정](#19-보조-경고와-상태-보정)
20. [실행 및 테스트](#20-실행-및-테스트)
21. [파일 구조](#21-파일-구조)
22. [현재 구현상 주의사항](#22-현재-구현상-주의사항)
23. [관련 문서](#23-관련-문서)

<br>

## 1. 모듈 역할

Style 모듈은 사용자에게 세 가지 샘플 식단 방향을 제시하고, 선택 결과를 월간 식단 생성에 반영합니다.

주요 역할은 다음과 같습니다.

### Style 후보 생성

- 사용자가 선택한 목표를 Style 메타데이터로 변환
- 부족한 후보를 지원 Style로 보충
- 최대 세 개의 Style 후보 반환

### Style별 샘플 추천

- 기본 Profile 가중치 유지
- Style의 핵심 평가 항목 강화
- 샘플 단계에서는 다양성도 추가 강화
- Style마다 후보 메뉴를 다시 점수화

### 샘플 간 차별화

- 동일 `menu_id` 중복 방지
- 유사 메뉴 중복 최소화
- 동일 Style 내부 유사 메뉴 최소화
- 후보 부족 시 단계적 Fallback

### 월간 Profile 반영

- 선택한 Style Goal 저장
- 선택한 Style ID 저장
- 선택한 `focus_key` 저장
- 기본 가중치 재조정
- 영양 내부 세부 가중치 적용

### 결과 검증

- 고단백, 다이어트, 영양 균형
- 식비 절약, 간편식, 맛 중심
- Pass, Warning, Fail, Unknown 상태 생성
- 중복률과 후보 풀 조건을 고려한 보정

<br>

## 2. 전체 처리 흐름

```text
Profile.goals
      ↓
get_candidate_style_metas()
      ↓
Style 후보 최대 3개
      ↓
각 Style의 focus_key 확인
      ↓
boost_style_weights()
      ↓
build_profile_with_style_weights()
      ↓
recommend_menus()
      ↓
select_diverse_recommendations_for_style()
      ↓
build_sample_plan_from_recommendations()
      ↓
build_display_scores()
      ↓
meal_style_candidates 반환
      ↓
사용자가 Style 하나 선택
      ↓
build_selected_style_summary()
      ↓
apply_selected_style_to_profile()
      ↓
Recommendation Soft Constraint
      ↓
MMR 및 Style Priority 메뉴 선택
      ↓
OR-Tools 월간 식단 구성
      ↓
build_style_validation()
      ↓
enrich_style_validation()
```

핵심 후보 생성 함수:

```python
build_meal_style_candidates(
    user_id: str,
    candidate_menus: list[dict],
    profile: dict,
    meal_count_per_day: int,
    sample_period_days: int = 3,
) -> dict
```

선택 Style 적용 함수:

```python
apply_selected_style_to_profile(
    profile: dict,
    selected_style: dict,
) -> dict
```

<br>

## 3. 지원하는 식단 스타일

Style 메타데이터는 `GOAL_STYLE_META`에 정의되어 있습니다.

| Source Goal | Style ID | Style Name | Focus Key |
|---|---|---|---|
| 식비 절약 | `budget_first` | 가성비 최우선 | `budget` |
| 영양 균형 | `nutrition_balance` | 영양 균형식 | `nutrition` |
| 다이어트 | `diet_light` | 가벼운 관리식 | `nutrition` |
| 고단백 | `high_protein` | 고단백 관리식 | `nutrition` |
| 간편식 | `easy_cooking` | 간편 조리식 | `difficulty` |
| 맛 중심 | `taste_first` | 취향 맞춤식 | `preference` |

각 Style에는 다음 메타데이터가 포함됩니다.

```text
style_id
style_name
description
summary_comment
focus_key
source_goal
```

### Style별 설명

#### 가성비 최우선

```text
설명: 예산을 가장 우선으로 고려한 식단
요약: 예산 부담을 줄이고 간편하게 구성한 식단입니다.
```

#### 영양 균형식

```text
설명: 칼로리와 단백질 균형을 함께 고려한 식단
요약: 영양 균형을 고려해 건강하게 구성한 식단입니다.
```

#### 가벼운 관리식

```text
설명: 칼로리 부담을 줄이고 가볍게 구성한 식단
요약: 부담이 적은 메뉴를 중심으로 구성한 식단입니다.
```

#### 고단백 관리식

```text
설명: 단백질 섭취를 우선으로 고려한 식단
요약: 단백질 섭취를 늘리고 싶은 사용자에게 적합한 식단입니다.
```

#### 간편 조리식

```text
설명: 조리 난이도와 시간을 낮게 유지한 식단
요약: 조리 부담을 줄이고 빠르게 준비할 수 있는 식단입니다.
```

#### 취향 맞춤식

```text
설명: 선호 카테고리와 재료 취향을 더 많이 반영한 식단
요약: 사용자의 취향과 선호 재료를 중심으로 구성한 식단입니다.
```

<br>

## 4. Style 후보 3개 생성

관련 함수:

```python
get_candidate_style_metas(profile: dict) -> list[dict]
```

Style 후보는 최대 세 개를 반환합니다.

### 목표가 세 개인 경우

사용자가 선택한 세 목표를 그대로 사용합니다.

```text
goals:
- 다이어트
- 고단백
- 식비 절약

→ 가벼운 관리식
→ 고단백 관리식
→ 가성비 최우선
```

### 목표가 한 개 또는 두 개인 경우

선택 목표를 먼저 넣고, `GOAL_STYLE_META` 정의 순서에 따라 지원 Style을 추가합니다.

```text
사용자 목표:
- 고단백

결과:
1. 고단백 관리식
2. 가성비 최우선
3. 영양 균형식
```

사용자가 선택하지 않은 목표로 채워진 후보에는 내부적으로 다음 값이 설정됩니다.

```text
is_support_style = True
```

사용자가 직접 선택한 목표 기반 후보는 다음 값을 가집니다.

```text
is_support_style = False
```

현재 이 값은 후보 메타 생성 단계에서 사용되지만 최종 `meal_style_candidates` 응답에는 포함되지 않습니다.

<br>

## 5. Style 샘플 가중치 강화

관련 함수:

```python
boost_style_weights(
    base_weights: dict,
    focus_key: str,
    boost_amount: float = 0.45,
) -> dict
```

Style 후보 화면에서는 각 Style의 차이가 명확하게 보여야 하므로 월간 적용보다 강한 보정을 사용합니다.

### 핵심 Focus 강화

```text
weights[focus_key] += 0.45
```

### 다양성 강화

```text
weights.diversity += 0.25
```

Style 카드 세 개가 비슷한 메뉴로만 구성되지 않도록 다양성 가중치도 높입니다.

### Focus별 보조 조정

| Focus Key | 보조 조정 |
|---|---|
| `budget` | nutrition `-0.05` |
| `nutrition` | budget `-0.05` |
| `difficulty` | preference `-0.05` |
| `preference` | difficulty `-0.05` |

감산 결과는 최소 `0`으로 제한합니다.

모든 조정 후 가중치 합이 1이 되도록 다시 정규화합니다.

```text
normalized_weight
= 각 weight ÷ 전체 weight 합
```

가중치는 소수점 넷째 자리까지 반올림합니다.

<br>

## 6. Style 전용 Profile 생성

관련 함수:

```python
build_profile_with_style_weights(
    profile: dict,
    style_weights: dict,
    style_goal: str,
) -> dict
```

원본 Profile을 복사한 뒤 Style 샘플 추천에 필요한 항목만 변경합니다.

```python
style_profile["goals"] = [style_goal]
style_profile["weights"] = style_weights
style_profile["diversity_penalty_strength"] = 0.65
```

### Goal 단일화

복수 목표 사용자의 경우에도 Style 카드 한 장은 하나의 목표를 명확히 표현해야 하므로 다음과 같이 변경합니다.

```text
원본 goals:
- 다이어트
- 고단백

고단백 Style Profile:
- 고단백
```

### 다양성 강도 고정

사용자의 기본 다양성 선택과 관계없이 Style 샘플 단계에서는 다음 값으로 고정됩니다.

```text
diversity_penalty_strength = 0.65
```

샘플 후보끼리 비교하기 쉽도록 메뉴 반복을 적극적으로 줄이기 위한 설정입니다.

<br>

## 7. Style별 후보 메뉴 추천

각 Style Profile을 사용해 Recommendation 모듈을 다시 실행합니다.

```python
raw_recommendations = recommend_menus(
    menus=candidate_menus,
    profile=style_profile,
    top_n=len(candidate_menus),
)
```

`top_n`에 전체 후보 수를 전달하므로 Style별 전체 후보를 순차적으로 다시 점수화합니다.

Recommendation 단계에서 반영되는 주요 항목:

```text
budget_score
nutrition_score
preference_score
difficulty_score
diversity_score
base_final_score
style_soft_constraint_score
quality_penalty
final_score
```

Style 후보 생성 단계는 Recommendation이 산출한 순위를 기반으로 샘플에 사용할 메뉴를 다시 선택합니다.

<br>

## 8. 스타일 간 메뉴 중복 제어

관련 함수:

```python
select_diverse_recommendations_for_style(
    recommendations: list[dict],
    used_menus: list[dict],
    required_count: int,
) -> list[dict]
```

세 Style 카드가 동일하거나 유사한 메뉴로 구성되지 않도록 네 단계 선택 정책을 사용합니다.

### 1차 선택

다음 조건을 모두 만족하는 메뉴를 선택합니다.

```text
다른 Style에서 같은 menu_id를 사용하지 않음
다른 Style의 메뉴와 유사하지 않음
현재 Style 내부 선택 메뉴와 유사하지 않음
```

### 2차 선택

후보가 부족하면 다른 Style과의 유사성은 허용합니다.

```text
다른 Style과 같은 menu_id는 금지
현재 Style 내부 같은 menu_id 금지
현재 Style 내부 유사 메뉴 금지
```

### 3차 선택

그래도 부족하면 현재 Style 내부에서 `menu_id`만 겹치지 않도록 채웁니다.

### 4차 Fallback

후보가 정말 부족하면 기존 추천 순서에서 아직 선택되지 않은 메뉴를 추가합니다.

### 유사 메뉴 판정

```python
are_menus_similar(recommendation, used_menu)
```

유사성 판정에는 다음 기준이 사용됩니다.

```text
menu_id
similar_menu_ids
정규화된 메뉴명
재료 유사도
```

선택된 메뉴는 `used_menus`에 누적되어 다음 Style 생성 시 사용됩니다.

<br>

## 9. 샘플 식단 구성

관련 함수:

```python
build_sample_plan_from_recommendations(
    recommendations: list[dict],
    meal_count_per_day: int,
    sample_period_days: int,
) -> dict
```

필요한 샘플 메뉴 수:

```text
required_sample_meal_count
= sample_period_days × meal_count_per_day
```

예시:

```text
샘플 기간: 3일
하루 끼니 수: 2끼

필요 메뉴 수:
3 × 2 = 6개
```

추천 결과를 순서대로 Day와 Meal에 배치합니다.

```text
recommendation 1 → 1일 차 1끼
recommendation 2 → 1일 차 2끼
recommendation 3 → 2일 차 1끼
...
```

후보 수가 부족하면 `% len(recommendations)` 방식으로 다시 앞에서부터 사용하므로 메뉴가 반복될 수 있습니다.

이 경우 `meta.warnings`에 부족한 메뉴 수가 기록됩니다.

### 샘플 메뉴 필드

샘플 카드에는 다음 필드만 남깁니다.

```text
meal_order
menu_id
name
category
estimated_cost
calories
protein
```

<br>

## 10. 화면 표시 점수

관련 함수:

```python
build_display_scores(
    recommendations: list[dict],
    focus_key: str,
) -> dict
```

Recommendation의 내부 평균 점수를 사용자 화면용 1~10 점수로 변환합니다.

### 내부 점수 매핑

| 내부 점수 | 표시 점수 |
|---|---|
| nutrition | health |
| budget | cost_efficiency |
| preference | taste |
| difficulty | cooking_ease |

### 점수 변환

```text
display_score
= round(internal_score ÷ 10)
```

최소값은 `1`, 최대값은 `10`입니다.

### Focus 최소 점수 보정

Style 카드의 핵심 방향이 화면에서 명확하게 보이도록 해당 Focus 표시 점수는 최소 `8점`으로 보정합니다.

```text
focus_display_score
= max(계산된 점수, 8)
```

예시:

```text
가성비 Style
→ focus_key = budget
→ cost_efficiency 최소 8점
```

### 표시 라벨

```json
{
  "health": "건강",
  "cost_efficiency": "가성비",
  "taste": "맛",
  "cooking_ease": "조리"
}
```

표시 점수는 Style 간 의도를 쉽게 비교하기 위한 UI용 지표이며, 원본 Recommendation 점수와 동일한 척도가 아닙니다.

<br>

## 11. Style Candidate 응답 구조

대표 반환 구조:

```json
{
  "id": "user-001",
  "request_type": "meal_style_candidates",
  "meta": {
    "sample_period_days": 3,
    "meal_count_per_day": 2,
    "total_style_count": 3,
    "generated_at": "2026-06-24T05:00:00Z",
    "warnings": []
  },
  "meal_style_candidates": [
    {
      "style_id": "high_protein",
      "style_name": "고단백 관리식",
      "description": "단백질 섭취를 우선으로 고려한 식단",
      "summary_comment": "단백질 섭취를 늘리고 싶은 사용자에게 적합한 식단입니다.",
      "source_goal": "고단백",
      "focus_key": "nutrition",
      "display_scores": {
        "health": 9,
        "cost_efficiency": 7,
        "taste": 7,
        "cooking_ease": 8
      },
      "display_labels": {
        "health": "건강",
        "cost_efficiency": "가성비",
        "taste": "맛",
        "cooking_ease": "조리"
      },
      "sample_plan": {
        "period_days": 3,
        "meal_count_per_day": 2,
        "days": []
      }
    }
  ]
}
```

생성 시각은 UTC 기준 ISO 문자열입니다.

```text
YYYY-MM-DDTHH:MM:SSZ
```

<br>

## 12. 선택 Style 요약

관련 함수:

```python
build_selected_style_summary(
    selected_style: dict,
) -> dict
```

사용자가 선택한 Style에서 월간 식단 응답과 Profile 적용에 필요한 정보만 추출합니다.

반환 필드:

```text
style_id
style_name
description
summary_comment
source_goal
focus_key
display_scores
display_labels
```

샘플 식단 전체는 선택 Style 요약에 포함되지 않습니다.

<br>

## 13. 선택 Style의 월간 Profile 반영

관련 함수:

```python
apply_selected_style_to_profile(
    profile: dict,
    selected_style: dict,
) -> dict
```

원본 Profile을 복사한 뒤 다음 필드를 추가합니다.

```text
selected_style_goal
selected_style_id
selected_style_focus_key
nutrition_detail_weights
```

### 월간 Focus 강화

Style 샘플 생성에서는 Focus에 `0.45`를 추가했지만, 실제 월간 Profile에서는 보다 완만한 `0.2`를 추가합니다.

```text
weights[focus_key] += 0.2
```

### Focus별 보조 조정

| Focus Key | 월간 보조 조정 |
|---|---|
| `budget` | nutrition `-0.05`, preference `-0.03` |
| `nutrition` | budget `-0.05` |
| `difficulty` | preference `-0.03` |
| `preference` | difficulty `-0.03` |

### 다양성 가중치

기본 가중치에 `diversity`가 있으면 다음 값을 추가합니다.

```text
weights.diversity += 0.05
```

모든 조정 후 가중치 합을 다시 1로 정규화합니다.

### Focus Key가 없는 경우

가중치는 수정하지 않고 영양 세부 가중치만 설정합니다.

### Focus Key가 기본 Weights에 없는 경우

가중치를 수정하지 않고 영양 세부 가중치만 설정합니다.

<br>

## 14. 영양 세부 가중치

관련 함수:

```python
get_nutrition_detail_weights_by_style(
    selected_style: dict,
) -> dict
```

Recommendation의 `nutrition_score` 내부는 세 기준으로 구성됩니다.

```text
diet
high_protein
balance
```

선택 Style에 따라 내부 영양 가중치를 변경합니다.

### 다이어트

```json
{
  "diet": 0.75,
  "high_protein": 0.10,
  "balance": 0.15
}
```

### 고단백

```json
{
  "diet": 0.15,
  "high_protein": 0.65,
  "balance": 0.20
}
```

### 영양 균형

```json
{
  "diet": 0.20,
  "high_protein": 0.20,
  "balance": 0.60
}
```

### 기타 Style

```json
{
  "diet": 0.33,
  "high_protein": 0.34,
  "balance": 0.33
}
```

이 값은 Recommendation의 목표 문자열 평균보다 우선 적용됩니다.

<br>

## 15. Recommendation 연동

선택 Style은 Recommendation에 여러 경로로 반영됩니다.

### Profile Weight

```text
selected_style_focus_key
→ 월간 weights 조정
→ base_final_score 변화
```

### Nutrition Detail Weight

```text
selected_style_goal
→ nutrition_detail_weights
→ diet / high_protein / balance 구성 변화
```

### Soft Constraint

Recommendation에서는 다음 Style Goal에 별도 보정 점수를 적용합니다.

```text
고단백
→ 단백질 함량 기준 -4 ~ +3

간편식
→ difficulty_score 기준 -10 ~ +8
```

### 추천 이유 필터링

```text
selected_style_focus_key
→ 해당 type의 추천 이유 우선 노출
```

예시:

```text
focus_key = budget
→ budget 이유만 사용자 응답에 유지
```

<br>

## 16. 월간 메뉴 선택 우선순위

실제 월간 배치에서는 MMR 재랭킹 이후에도 고단백과 간편식 Style을 조건부로 우선합니다.

관련 위치:

```text
modeling/services/plan/meal_selector_service.py
```

관련 함수:

```python
filter_menus_by_style_priority(
    menus: list[dict],
    profile: dict,
) -> list[dict]
```

### 고단백 Style

다음 순서로 충분한 후보가 있는지 확인합니다.

```text
단백질 30g 이상 후보 20개 이상
→ 해당 후보 우선

부족하면 단백질 25g 이상 후보 20개 이상
→ 해당 후보 우선

부족하면 단백질 22g 이상 후보 20개 이상
→ 해당 후보 우선

모두 부족
→ 전체 후보 유지
```

### 간편식 Style

```text
difficulty score 70 이상 후보 20개 이상
→ 해당 후보 우선

부족하면 difficulty score 60 이상 후보 20개 이상
→ 해당 후보 우선

후보 부족
→ 전체 후보 유지
```

이는 절대적인 Hard Filter가 아닙니다. 후보 풀이 너무 좁아져 반복이 증가하는 것을 막기 위해 최소 20개 조건을 사용합니다.

### Style 내부 정렬

고단백:

```text
mmr_score
→ protein
→ final_score
```

간편식:

```text
mmr_score
→ difficulty score
→ final_score
```

내림차순으로 정렬합니다.

<br>

## 17. Style Validation

Style Validation의 실제 구현은 Plan 모듈에 있습니다.

```text
modeling/services/plan/plan_validation_service.py
```

대표 함수:

```python
build_style_validation(
    selected_style: dict,
    summary: dict,
    profile: dict,
) -> dict
```

검증 결과 상태:

```text
pass
warning
fail
unknown
```

### 고단백

평균 단백질을 기준으로 검증합니다.

| 평균 단백질 | 상태 |
|---:|---|
| 28g 이상 | pass |
| 25g 이상 | warning |
| 25g 미만 | fail |

### 다이어트

| 조건 | 상태 |
|---|---|
| 평균 650kcal 이하이면서 지방 23g 이하 | pass |
| 평균 750kcal 이하이면서 지방 28g 이하 | warning |
| 그 외 | fail |

### 영양 균형

평균 탄수화물, 단백질, 지방의 g 비율을 사용합니다.

엄격 기준:

```text
탄수화물 0.45~0.65
단백질   0.15~0.35
지방     0.15~0.35
```

모두 충족하면 `pass`입니다.

완화 기준:

```text
탄수화물 0.35~0.70
단백질   0.10~0.40
지방     0.10~0.45
```

모두 충족하면 `warning`, 그 외에는 `fail`입니다.

3대 영양소 합이 0 이하라면 `unknown`입니다.

### 식비 절약

```text
budget_usage_rate
= total_estimated_cost ÷ monthly_budget
```

| 예산 사용률 | 상태 |
|---:|---|
| 85% 이하 | pass |
| 100% 이하 | warning |
| 100% 초과 | fail |

월 예산이 없으면 다음 방식으로 추정합니다.

```text
meal_budget × period_days × meal_count_per_day
```

이 값도 0 이하이면 `unknown`입니다.

### 간편식

월간 평균 난이도 점수를 기준으로 합니다.

| 평균 Difficulty Score | 상태 |
|---:|---|
| 75 이상 | pass |
| 65 이상 | warning |
| 65 미만 | fail |

Difficulty Score가 높을수록 사용자 실력 대비 조리 부담이 낮다는 의미입니다.

### 맛 중심

평균 선호도 점수를 사용합니다.

| 평균 Preference Score | 상태 |
|---:|---|
| 85 이상 | pass |
| 70 이상 | warning |
| 70 미만 | fail |

<br>

## 18. 후보 풀 난이도 진단

간편식 Validation 실패가 Optimizer 선택 문제인지 후보 풀 부족인지 구분하기 위한 진단입니다.

관련 함수:

```python
build_difficulty_feasibility_diagnostics(
    optimizer_snapshot: dict | None,
    pass_threshold: float = 75,
    warning_threshold: float = 65,
) -> dict | None
```

수집 지표:

```text
candidate_count
candidate_avg_difficulty
candidate_p75_difficulty
candidate_p90_difficulty
candidate_max_difficulty
candidate_ge75_count
candidate_ge65_count
candidate_ge40_count
candidate_eq0_count
```

### 진단 상태

#### 통과 후보 없음

```text
candidate_ge75_count == 0

status = absolute_pass_unreachable
reason = candidate_difficulty_shortage
```

#### 통과 후보가 매우 희소

```text
candidate_p90 < 75

status = pass_threshold_very_sparse
reason = candidate_difficulty_sparse
```

#### 후보 풀에 통과 선택지 존재

```text
status = candidate_pool_has_pass_options
reason = candidate_pool_feasible
```

이 진단 자체는 기본 Validation 상태를 직접 변경하지 않고, 실패 원인을 설명하는 보조 자료로 사용됩니다.

<br>

## 19. 보조 경고와 상태 보정

관련 함수:

```python
enrich_style_validation(
    style_validation: dict,
    selected_style: dict,
    summary: dict,
    difficulty_feasibility_diagnostics: dict | None = None,
) -> dict
```

### Secondary Warnings

Style 자체 기준 외에 사용자 경험상 문제가 될 수 있는 항목을 별도로 기록합니다.

| 항목 | 조건 | Level |
|---|---:|---|
| 평균 난이도 점수 | 60 미만 | warning |
| 평균 선호도 점수 | 60 미만 | warning |
| 평균 다양성 점수 | 75 미만 | warning |
| 동일 메뉴 비율 | 15% 이상 30% 미만 | info |
| 동일 메뉴 비율 | 30% 이상 | warning |

중복률:

```text
duplicate_rate
= duplicate_menu_count ÷ selected_menu_count
```

### 간편식 후보 부족 보정

다음 조건이 모두 충족되면 `fail`을 `warning`으로 조정합니다.

```text
source_goal == 간편식
기본 status == fail
후보 풀 status == absolute_pass_unreachable
```

이 경우 사용자 선택이나 Optimizer 실패가 아니라 충분히 쉬운 후보 자체가 부족한 것으로 해석합니다.

### 중복률 상태 보정

기본 Style Validation이 `pass`여도 중복률이 30% 이상이면 최종 상태를 `warning`으로 낮춥니다.

```text
base status = pass
duplicate_rate ≥ 0.30
→ final status = warning
```

### Recommendation Hint

최종 상태와 Source Goal에 따라 다음 개선 방향을 반환합니다.

```text
recommendation_hint
```

예시:

- 고단백 메뉴 우선 배치
- 지방 25g 이상 감점 강화
- 영양 비율 가중치 조정
- 예산 Soft Constraint 강화
- 간편식 난이도 산식 세분화
- 선호 카테고리·재료군 반영 강화

<br>

## 20. 실행 및 테스트

프로젝트 루트에서 실행합니다.

### Style 메타 확인

```bash
PYTHONPATH=modeling \
python - <<'PY'
from services.style.meal_style_service import (
    get_candidate_style_metas,
)

profile = {
    "goals": ["고단백", "간편식"],
}

for style in get_candidate_style_metas(profile):
    print(
        style["style_id"],
        style["style_name"],
        style["source_goal"],
        style["focus_key"],
        style["is_support_style"],
    )
PY
```

예상 구조:

```text
high_protein 고단백 관리식 고단백 nutrition False
easy_cooking 간편 조리식 간편식 difficulty False
budget_first 가성비 최우선 식비 절약 budget True
```

### Style 가중치 확인

```bash
PYTHONPATH=modeling \
python - <<'PY'
from services.style.meal_style_service import (
    boost_style_weights,
)

base_weights = {
    "budget": 0.20,
    "nutrition": 0.30,
    "preference": 0.20,
    "difficulty": 0.15,
    "diversity": 0.15,
}

result = boost_style_weights(
    base_weights=base_weights,
    focus_key="nutrition",
)

print(result)
print("total:", round(sum(result.values()), 4))
PY
```

정규화 후 합은 약 `1.0`이어야 합니다.

### 선택 Style 월간 적용 확인

```bash
PYTHONPATH=modeling \
python - <<'PY'
from services.style.style_selection_service import (
    apply_selected_style_to_profile,
)

profile = {
    "weights": {
        "budget": 0.20,
        "nutrition": 0.30,
        "preference": 0.20,
        "difficulty": 0.15,
        "diversity": 0.15,
    }
}

selected_style = {
    "style_id": "high_protein",
    "source_goal": "고단백",
    "focus_key": "nutrition",
}

monthly_profile = apply_selected_style_to_profile(
    profile=profile,
    selected_style=selected_style,
)

print(monthly_profile)
print(
    "weight total:",
    round(sum(monthly_profile["weights"].values()), 4),
)
PY
```

### Style Validation 확인

```bash
PYTHONPATH=modeling \
python - <<'PY'
from services.plan.plan_validation_service import (
    build_style_validation,
)

selected_style = {
    "style_name": "고단백 관리식",
    "source_goal": "고단백",
    "focus_key": "nutrition",
}

summary = {
    "average_protein": 29,
}

result = build_style_validation(
    selected_style=selected_style,
    summary=summary,
    profile={},
)

print(result)
PY
```

예상 상태:

```text
pass
```

### 문법 검사

```bash
python -m py_compile \
  modeling/services/style/meal_style_service.py \
  modeling/services/style/style_selection_service.py \
  modeling/services/plan/plan_validation_service.py \
  modeling/services/plan/meal_selector_service.py
```

### API 요청 검증 테스트

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/api/test_modeling_api_request_validation.py \
  -q
```

### 전체 Modeling 테스트

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest modeling/tests -q
```

현재 전용 Style 점수 단위 테스트보다는 API Schema 검증, 실험 시나리오, Snapshot Replay와 전체 Validation 흐름을 통해 주로 검증합니다.

<br>

## 21. 파일 구조

```text
modeling/
├── services/
│   ├── style/
│   │   ├── __init__.py
│   │   ├── meal_style_service.py
│   │   ├── style_selection_service.py
│   │   └── README.md
│   │
│   ├── recommendation/
│   │   ├── recommendation_service.py
│   │   └── scoring_service.py
│   │
│   └── plan/
│       ├── meal_selector_service.py
│       ├── plan_validation_service.py
│       └── plan_payload_service.py
│
├── experiments/
│   ├── analysis/
│   ├── flows/
│   ├── scenarios/
│   └── tuning/
│
└── tests/
    └── api/
```

### 파일별 역할

| 파일 | 역할 |
|---|---|
| `meal_style_service.py` | Style 후보 메타, 샘플 가중치, 후보 추천, 샘플 식단과 표시 점수 생성 |
| `style_selection_service.py` | 선택 Style 요약과 월간 Profile 반영 |
| `recommendation_service.py` | Style Profile 기반 후보 점수화와 Soft Constraint |
| `meal_selector_service.py` | 월간 메뉴 선택 시 Style Priority 적용 |
| `plan_validation_service.py` | 월간 결과의 Style 적합도 검증 |
| `plan_payload_service.py` | 적용 전후 가중치와 Style 조정 결과 응답 |
| `analyze_style_validation_result.py` | Style Validation 결과 분석 |
| `replay_optimizer_snapshots.py` | Snapshot 기반 Optimizer 및 Validation 재실행 |

<br>

## 22. 현재 구현상 주의사항

### 지원 Style 순서가 보조 후보 선택에 영향을 줌

사용자가 목표를 세 개 미만으로 선택하면 `GOAL_STYLE_META` 정의 순서대로 보조 Style을 채웁니다.

현재 순서:

```text
식비 절약
영양 균형
다이어트
고단백
간편식
맛 중심
```

따라서 목표가 하나뿐이면 가성비와 영양 균형 Style이 보조 후보로 먼저 선택될 가능성이 큽니다.

### is_support_style이 최종 응답에서 제거됨

후보 메타에는 `is_support_style`이 있지만 최종 Style Candidate Payload에는 포함하지 않습니다.

Front에서 직접 선택한 목표 기반 Style과 자동 보충 Style을 구분해야 한다면 응답 필드 추가가 필요합니다.

### 표시 Focus 점수는 최소 8점으로 보정됨

`display_scores`는 실제 평균 점수를 그대로 1~10으로만 변환한 값이 아닙니다.

```text
Style Focus 점수
→ 최소 8점
```

따라서 UI 비교용 점수이며 모델 내부 성능 지표로 사용하면 안 됩니다.

### 샘플 후보가 부족하면 반복됨

샘플 식단 배치에서 Recommendation Index에 나머지 연산을 사용합니다.

```text
recommendation_index % len(recommendations)
```

필요 메뉴 수보다 추천 메뉴가 적으면 같은 메뉴가 다시 배치됩니다. 이 경우 Warning을 확인해야 합니다.

### 샘플 Style과 월간 Style의 Boost 강도가 다름

```text
Style 샘플 카드:
focus +0.45
diversity +0.25

월간 Profile:
focus +0.20
diversity +0.05
```

샘플 카드에서는 Style 차이를 명확히 보여주고, 월간 식단에서는 지나친 편향을 줄이기 위한 구조입니다.

### 영양 균형은 g 비율 사용

Style Validation의 영양 균형은 탄수화물, 단백질, 지방의 g 합을 기준으로 비율을 계산합니다.

```text
탄수화물 1g = 4kcal
단백질 1g = 4kcal
지방 1g = 9kcal
```

현재 방식은 에너지 비율이 아닌 중량 비율입니다.

### Validation 기준과 사용자별 목표의 차이

다이어트 Validation은 고정 기준을 사용합니다.

```text
Pass:
평균 650kcal 이하
평균 지방 23g 이하
```

Recommendation 점수에서는 사용자별 `meal_calorie_target`을 사용할 수 있으므로, 개인별 점수 계산과 월간 Validation 기준이 완전히 같지는 않습니다.

### 간편식 Difficulty Score 의미 확인 필요

간편식 Validation은 Difficulty Score가 높을수록 쉬운 메뉴로 해석합니다.

반면 이름만 보면 일반적인 난이도 원점수와 혼동할 수 있으므로 다음을 구분해야 합니다.

```text
menu.difficulty
→ 값이 높을수록 어려운 메뉴

scores.difficulty
→ 값이 높을수록 사용자에게 적합하고 부담이 낮음
```

### Style Priority는 고단백과 간편식에만 별도 적용

월간 `meal_selector_service.py`의 조건부 후보 우선 선택은 현재 다음 두 Style에만 존재합니다.

```text
고단백
간편식
```

식비 절약, 다이어트, 영양 균형과 맛 중심은 Recommendation Weight 및 Optimizer 목적함수 중심으로 반영됩니다.

### Style Validation 전용 단위 테스트 부족

현재 API 요청 검증 테스트는 존재하지만 다음 함수의 경계값을 직접 검증하는 전용 테스트는 별도로 확인되지 않았습니다.

```text
get_candidate_style_metas
boost_style_weights
build_display_scores
select_diverse_recommendations_for_style
apply_selected_style_to_profile
validate_*_style
enrich_style_validation
```

정책 변경 시 회귀 방지를 위해 경계값 중심 단위 테스트를 추가하는 것이 좋습니다.

<br>

## 23. 관련 문서

Style 후보 선택이 월간 식단 결과에 반영되었는지 검증하는 기준, 시나리오와 결과 분석 과정은 아래 문서에서 확인할 수 있습니다.

### 프로젝트 설계 및 검증

- [✅ Style Validation](https://app.notion.com/p/Style-Validation-35f9e3e335cc809f8186ee380e1b12a4?source=copy_link)  
  고단백, 다이어트, 영양 균형, 식비 절약, 간편식 및 맛 중심 Style별 검증 기준과 사용자 조건 안정성 분석
