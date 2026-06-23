# 👤 User Profile Builder

사용자가 입력한 식단 설정값을 RAG 후보 요청, 메뉴 점수 계산, 재랭킹과 월간 식단 최적화에서 사용할 수 있는 Modeling Profile로 변환하는 모듈입니다.

```text
사용자 식단 설정
→ Pydantic 입력 검증
→ 식단 기간 설정
→ 한 끼 예산 계산
→ 끼니별 목표 칼로리 계산
→ 식단 목표별 가중치 생성
→ 조리 난이도 기준 생성
→ 다양성 감점 강도 생성
→ Modeling Profile 반환
```

<br>

## 목차

1. [모듈 역할](#1-모듈-역할)
2. [입력 요청 구조](#2-입력-요청-구조)
3. [입력값 검증](#3-입력값-검증)
4. [전체 처리 흐름](#4-전체-처리-흐름)
5. [식단 기간 처리](#5-식단-기간-처리)
6. [한 끼 예산 계산](#6-한-끼-예산-계산)
7. [하루 및 끼니별 칼로리 기준](#7-하루-및-끼니별-칼로리-기준)
8. [목표별 추천 가중치](#8-목표별-추천-가중치)
9. [복수 목표 가중치 병합](#9-복수-목표-가중치-병합)
10. [조리 난이도 기준](#10-조리-난이도-기준)
11. [다양성 감점 강도](#11-다양성-감점-강도)
12. [생성되는 Modeling Profile](#12-생성되는-modeling-profile)
13. [RAG 연동](#13-rag-연동)
14. [Recommendation 연동](#14-recommendation-연동)
15. [Optimizer 연동](#15-optimizer-연동)
16. [샘플 사용자 데이터](#16-샘플-사용자-데이터)
17. [실행 및 검증](#17-실행-및-검증)
18. [파일 구조](#18-파일-구조)
19. [현재 구현상 주의사항](#19-현재-구현상-주의사항)

<br>

## 1. 모듈 역할

Profile 모듈은 Backend에서 전달한 사용자 식단 설정을 그대로 추천 엔진에 사용하지 않고, 계산에 필요한 파생값을 추가한 Modeling Profile로 변환합니다.

### 원본 입력값 유지

- 식단 목표
- 월 예산
- 하루 식사 횟수
- 권장 하루 칼로리
- 요리 실력
- 선호 음식 카테고리
- 선호 재료군
- 알레르기 재료
- 다양성 수준
- 샘플 식단 기간
- 월간 식단 기간

### Modeling 계산값 추가

- 예산 계산 기준 일수
- 한 끼 기준 예산
- 하루 목표 칼로리
- 끼니별 목표 칼로리
- 목표별 추천 가중치
- 최대 허용 조리 난이도
- 다양성 감점 강도

<table style="background-color:#EAF4FF; border-left:6px solid #4D96D9; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>💡 핵심 역할</strong><br>
      Profile 모듈은 최종 메뉴를 직접 선택하지 않습니다.
      사용자 입력을 예산·영양·선호도·조리 난이도·다양성 계산에 사용할 수 있는
      공통 Profile로 변환하여 RAG, Recommendation 및 Optimizer 단계에 제공합니다.
    </td>
  </tr>
</table>

<br>

## 2. 입력 요청 구조

입력 스키마는 다음 파일에서 관리합니다.

```text
modeling/schemas/user_profile_schema.py
```

전체 요청은 `UserProfileRequest`와 그 내부의 `UserProfileInput`으로 구성됩니다.

```text
UserProfileRequest
├── id
├── request_type
└── profile
    └── UserProfileInput
```

### UserProfileRequest

| 필드 | 타입 | 설명 |
|---|---|---|
| `id` | `int \| str` | 사용자 식별값 |
| `request_type` | `str` | 요청 종류 |
| `profile` | `UserProfileInput` | 사용자 식단 설정 |

대표적인 요청 종류:

```text
meal_style_candidates
monthly_plan
```

### UserProfileInput

| 필드 | 타입 | 조건 | 설명 |
|---|---|---|---|
| `goals` | `List[str]` | 1~3개 | 사용자의 식단 목표 |
| `monthly_budget` | `int` | 0 초과 | 월 식비 예산 |
| `meal_count_per_day` | `int` | 1~5 | 하루 식사 횟수 |
| `recommended_daily_calories` | `Optional[int]` | 값이 있으면 0 초과 | Persona 단계에서 계산한 권장 하루 칼로리 |
| `cooking_skill` | `int` | 1~5 | 사용자의 요리 실력 |
| `preferred_categories` | `List[str]` | 1개 이상 | 선호 음식 카테고리 |
| `diversity_level` | `str` | 허용값만 입력 | 원하는 식단 다양성 |
| `ingredient_preferences` | `List[str]` | 기본 빈 목록 | 선호 재료군 |
| `allergy_ingredients` | `List[str]` | 기본 빈 목록 | 알레르기 및 제외 재료 |
| `sample_period_days` | `int` | 1~7, 기본 3 | 샘플 식단 생성 기간 |
| `period_days` | `Optional[int]` | 1~31 | 월간 식단 생성 기간 |

### 요청 예시

```json
{
  "id": 4,
  "request_type": "monthly_plan",
  "profile": {
    "goals": [
      "다이어트",
      "간편식"
    ],
    "monthly_budget": 300000,
    "meal_count_per_day": 3,
    "recommended_daily_calories": 1905,
    "cooking_skill": 2,
    "preferred_categories": [
      "한식",
      "샐러드/건강식"
    ],
    "diversity_level": "보통",
    "ingredient_preferences": [
      "육류",
      "채소류"
    ],
    "allergy_ingredients": [
      "새우"
    ],
    "sample_period_days": 3,
    "period_days": 30
  }
}
```

<br>

## 3. 입력값 검증

`UserProfileInput`은 Pydantic Validator를 사용해 추천 파이프라인에서 허용하는 값을 검증합니다.

### 지원하는 식단 목표

```text
식비 절약
영양 균형
다이어트
고단백
간편식
맛 중심
```

검증 규칙:

- 최소 1개 이상
- 최대 3개
- 중복 선택 불가
- 지원 목록 외 값 입력 불가

### 지원하는 음식 카테고리

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

검증 규칙:

- 최소 1개 이상
- 중복 선택 불가
- 지원 목록 외 값 입력 불가

### 지원하는 다양성 수준

```text
낮음
보통
높음
```

### 지원하는 선호 재료군

```text
육류
해산물류
식물성 단백질류
채소류
계란 및 유제품류
```

검증 규칙:

- 선택하지 않아도 됨
- 중복 선택 불가
- 지원 목록 외 값 입력 불가

### 알레르기 재료

알레르기 재료는 자유 문자열 목록이지만, 동일한 재료를 중복으로 입력할 수 없습니다.

```text
["새우", "우유"]       → 정상
["새우", "새우"]       → 검증 오류
```

<br>

## 4. 전체 처리 흐름

```text
Backend Request
        ↓
UserProfileRequest 검증
        ↓
UserProfileInput 추출
        ↓
식단 기간 결정
        ├── period_days 입력값
        └── 값이 없으면 30일
        ↓
한 끼 예산 계산
        ↓
식단 목표별 가중치 조회
        ↓
복수 목표 가중치 평균
        ↓
가중치 합계 재정규화
        ↓
권장 하루 칼로리 확인
        ↓
끼니별 목표 칼로리 계산
        ↓
조리 난이도 및 다양성 정책 생성
        ↓
Modeling Profile 반환
```

관련 함수:

```python
build_user_profile(user_input: UserProfileInput) -> dict
```

전체 요청을 검증하고 응답 형태로 묶는 함수:

```python
build_user_profile_response(request_data: dict) -> dict
```

<br>

## 5. 식단 기간 처리

Profile에는 샘플 식단 기간과 실제 식단 생성 기간이 별도로 존재합니다.

### sample_period_days

```text
기본값: 3일
허용 범위: 1~7일
```

식단 스타일 후보를 보여주기 위한 짧은 샘플 식단 생성에 사용합니다.

### period_days

```text
기본값: None
허용 범위: 1~31일
```

월간 식단 등 실제 기간형 식단 생성에 사용합니다.

### Profile 내부 기본값

`period_days`가 전달되지 않으면 Profile Builder에서 30일로 설정합니다.

```python
budget_period_days = user_input.period_days or 30
period_days = user_input.period_days or budget_period_days
```

따라서 실제 반환 Profile에서는 `period_days`가 항상 정수로 존재합니다.

```text
period_days 입력 있음
→ 입력값 사용

period_days 입력 없음
→ 30일 사용
```

### 예산 계산 기준

현재 `budget_period_days`와 `period_days`는 같은 값을 사용합니다.

```text
period_days = 20
→ budget_period_days = 20
→ period_days = 20

period_days = None
→ budget_period_days = 30
→ period_days = 30
```

<br>

## 6. 한 끼 예산 계산

한 끼 예산은 월 예산을 예산 기준 일수와 하루 식사 횟수로 나누어 계산합니다.

```text
한 끼 예산
= 월 예산
÷ 예산 기준 일수
÷ 하루 식사 횟수
```

코드에서는 정수 나눗셈을 사용합니다.

```python
monthly_budget // budget_period_days // meal_count_per_day
```

관련 함수:

```python
calculate_meal_budget(
    monthly_budget: int,
    meal_count_per_day: int,
    budget_period_days: int = 30,
) -> int
```

### 계산 예시

```text
월 예산: 300,000원
기간: 30일
하루 식사: 3끼

300,000 // 30 // 3
= 3,333원
```

### 기간이 다른 경우

```text
월 예산: 300,000원
기간: 20일
하루 식사: 3끼

300,000 // 20 // 3
= 5,000원
```

<table style="background-color:#FFF6C7; border-left:6px solid #E6C85C; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>⭐ 계산 기준</strong><br>
      현재 한 끼 예산 계산에는 가구원 수가 직접 포함되지 않습니다.
      Backend가 전달한 <code>monthly_budget</code>과 하루 식사 횟수,
      식단 기간만 사용합니다.
    </td>
  </tr>
</table>

<br>

## 7. 하루 및 끼니별 칼로리 기준

`recommended_daily_calories`는 앞선 Persona 단계에서 계산된 사용자·가구 기준 권장 하루 칼로리입니다.

Profile Builder는 해당 값을 다음 두 필드로 유지합니다.

```text
recommended_daily_calories
daily_calorie_target
```

그리고 하루 식사 횟수로 나누어 끼니별 목표 칼로리를 계산합니다.

```text
끼니별 목표 칼로리
= 권장 하루 칼로리
÷ 하루 식사 횟수
```

관련 코드:

```python
daily_calorie_target = user_input.recommended_daily_calories
meal_calorie_target = None

if daily_calorie_target and user_input.meal_count_per_day:
    meal_calorie_target = round(
        daily_calorie_target / user_input.meal_count_per_day,
        2,
    )
```

### 계산 예시

```text
권장 하루 칼로리: 1,905kcal
하루 식사: 3끼

1,905 ÷ 3
= 끼니별 635kcal
```

### 권장 칼로리가 없는 경우

`recommended_daily_calories`는 선택 필드입니다.

값이 전달되지 않으면 다음과 같이 처리됩니다.

```text
recommended_daily_calories = None
daily_calorie_target = None
meal_calorie_target = None
```

이 경우 Recommendation 단계에서는 사용자별 칼로리 목표 대신 목표별 기본 칼로리 기준을 사용할 수 있습니다.

<br>

## 8. 목표별 추천 가중치

각 식단 목표는 다음 다섯 가지 평가 항목에 서로 다른 가중치를 부여합니다.

```text
budget
nutrition
preference
difficulty
diversity
```

가중치 정의는 다음 파일에서 관리합니다.

```text
modeling/services/profile/weight_service.py
```

### 식비 절약

| 항목 | 가중치 |
|---|---:|
| 예산 | `0.45` |
| 영양 | `0.20` |
| 선호도 | `0.15` |
| 난이도 | `0.10` |
| 다양성 | `0.10` |

### 영양 균형

| 항목 | 가중치 |
|---|---:|
| 예산 | `0.15` |
| 영양 | `0.45` |
| 선호도 | `0.15` |
| 난이도 | `0.10` |
| 다양성 | `0.15` |

### 다이어트

| 항목 | 가중치 |
|---|---:|
| 예산 | `0.15` |
| 영양 | `0.40` |
| 선호도 | `0.15` |
| 난이도 | `0.10` |
| 다양성 | `0.20` |

### 고단백

| 항목 | 가중치 |
|---|---:|
| 예산 | `0.15` |
| 영양 | `0.45` |
| 선호도 | `0.15` |
| 난이도 | `0.10` |
| 다양성 | `0.15` |

### 간편식

| 항목 | 가중치 |
|---|---:|
| 예산 | `0.20` |
| 영양 | `0.15` |
| 선호도 | `0.15` |
| 난이도 | `0.40` |
| 다양성 | `0.10` |

### 맛 중심

| 항목 | 가중치 |
|---|---:|
| 예산 | `0.10` |
| 영양 | `0.15` |
| 선호도 | `0.45` |
| 난이도 | `0.10` |
| 다양성 | `0.20` |

### 목표별 특징

| 목표 | 가장 높은 가중치 |
|---|---|
| 식비 절약 | 예산 |
| 영양 균형 | 영양 |
| 다이어트 | 영양 |
| 고단백 | 영양 |
| 간편식 | 조리 난이도 |
| 맛 중심 | 선호도 |

<br>

## 9. 복수 목표 가중치 병합

사용자는 최대 3개의 식단 목표를 선택할 수 있습니다.

복수 목표가 선택되면 각 목표의 가중치를 항목별로 합산한 뒤 목표 개수로 나누어 평균을 계산합니다.

```text
목표별 가중치 합산
→ 선택 목표 개수로 나누기
→ 소수점 넷째 자리 반올림
→ 전체 합계로 다시 정규화
```

관련 함수:

```python
get_weights_by_goals(goals: list[str]) -> dict[str, float]
```

### 병합 예시

선택 목표:

```text
다이어트
간편식
```

원본 가중치:

| 항목 | 다이어트 | 간편식 |
|---|---:|---:|
| 예산 | `0.15` | `0.20` |
| 영양 | `0.40` | `0.15` |
| 선호도 | `0.15` | `0.15` |
| 난이도 | `0.10` | `0.40` |
| 다양성 | `0.20` | `0.10` |

평균:

```text
budget     = (0.15 + 0.20) ÷ 2 = 0.175
nutrition  = (0.40 + 0.15) ÷ 2 = 0.275
preference = (0.15 + 0.15) ÷ 2 = 0.150
difficulty = (0.10 + 0.40) ÷ 2 = 0.250
diversity  = (0.20 + 0.10) ÷ 2 = 0.150
```

최종 결과:

```json
{
  "budget": 0.175,
  "nutrition": 0.275,
  "preference": 0.15,
  "difficulty": 0.25,
  "diversity": 0.15
}
```

### 재정규화

각 값을 소수점 넷째 자리로 반올림하면 합계가 정확히 1이 아닐 수 있습니다.

따라서 평균 계산 후 다음 방식으로 다시 정규화합니다.

```text
정규화 가중치
= 평균 가중치
÷ 평균 가중치 전체 합
```

최종 가중치도 소수점 넷째 자리로 반올림합니다.

<table style="background-color:#EAF4FF; border-left:6px solid #4D96D9; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>💡 복수 목표 처리</strong><br>
      첫 번째 목표만 우선 적용하지 않고, 선택된 모든 목표의 가중치를 동일한 비중으로 평균냅니다.
      따라서 목표 선택 순서는 최종 가중치에 영향을 주지 않습니다.
    </td>
  </tr>
</table>

<br>

## 10. 조리 난이도 기준

사용자의 `cooking_skill` 값은 Profile의 `max_difficulty`로 그대로 전달됩니다.

```text
cooking_skill
→ max_difficulty
```

허용 범위:

```text
1~5
```

반환 예시:

```json
{
  "cooking_skill": 2,
  "max_difficulty": 2
}
```

이 값은 Recommendation과 식단 품질 검증 단계에서 사용자 조리 수준 대비 메뉴 난이도를 평가하는 기준으로 사용됩니다.

현재 Profile 단계에서는 별도의 난이도 변환 공식 없이 입력값을 그대로 유지합니다.

<br>

## 11. 다양성 감점 강도

사용자가 선택한 다양성 수준은 메뉴 반복과 유사도 제어에 사용할 감점 강도로 변환됩니다.

관련 함수:

```python
get_diversity_penalty_strength(diversity_level: str) -> float
```

### 변환 기준

| 다양성 수준 | 감점 강도 |
|---|---:|
| `낮음` | `0.20` |
| `보통` | `0.45` |
| `높음` | `0.65` |

```text
다양성 수준이 낮음
→ 기존 추천 점수 중심

다양성 수준이 높음
→ 메뉴 유사도 및 반복에 더 강한 감점
```

지원하지 않는 값이 함수에 직접 전달되면 기본값 `0.45`를 반환합니다.

다만 정상 API 요청에서는 Pydantic Validator가 지원하지 않는 다양성 값을 먼저 차단합니다.

<br>

## 12. 생성되는 Modeling Profile

`build_user_profile()`은 원본 입력값과 계산용 파생값을 하나의 Dictionary로 반환합니다.

### 원본 입력 필드

```text
goals
monthly_budget
meal_count_per_day
recommended_daily_calories
cooking_skill
preferred_categories
diversity_level
ingredient_preferences
allergy_ingredients
sample_period_days
period_days
```

### 계산용 필드

```text
budget_period_days
meal_budget
daily_calorie_target
meal_calorie_target
weights
max_difficulty
diversity_penalty_strength
```

### 반환 예시

```json
{
  "goals": [
    "다이어트",
    "간편식"
  ],
  "monthly_budget": 300000,
  "meal_count_per_day": 3,
  "recommended_daily_calories": 1905,
  "cooking_skill": 2,
  "preferred_categories": [
    "한식",
    "샐러드/건강식"
  ],
  "diversity_level": "보통",
  "ingredient_preferences": [
    "육류",
    "채소류"
  ],
  "allergy_ingredients": [
    "새우"
  ],
  "sample_period_days": 3,
  "period_days": 30,
  "budget_period_days": 30,
  "meal_budget": 3333,
  "daily_calorie_target": 1905,
  "meal_calorie_target": 635.0,
  "weights": {
    "budget": 0.175,
    "nutrition": 0.275,
    "preference": 0.15,
    "difficulty": 0.25,
    "diversity": 0.15
  },
  "max_difficulty": 2,
  "diversity_penalty_strength": 0.45
}
```

### Profile 응답

전체 요청을 처리하는 `build_user_profile_response()`는 다음 형태로 반환합니다.

```json
{
  "id": 4,
  "request_type": "profile_build",
  "profile": {
    "goals": [
      "다이어트",
      "간편식"
    ],
    "meal_budget": 3333,
    "meal_calorie_target": 635.0,
    "weights": {
      "budget": 0.175,
      "nutrition": 0.275,
      "preference": 0.15,
      "difficulty": 0.25,
      "diversity": 0.15
    }
  }
}
```

입력 요청의 `request_type`과 관계없이 Profile Builder의 응답 `request_type`은 `profile_build`로 설정됩니다.

<br>

## 13. RAG 연동

RAG 요청 생성 단계에서는 Profile의 계산 결과 중 한 끼 예산 등이 활용됩니다.

현재 확인되는 대표 필드:

```text
meal_budget
```

관련 모듈:

```text
modeling/services/rag/rag_request_service.py
```

대표적인 흐름:

```text
Profile
├── 목표
├── 한 끼 예산
├── 선호 카테고리
├── 선호 재료군
├── 알레르기 재료
└── 식단 기간
        ↓
RAG 요청 Payload
        ↓
후보 메뉴 검색
```

`meal_budget`은 RAG에서 사용자 예산에 적합한 후보 메뉴를 검색하거나 후보 범위를 설정하는 데 사용됩니다.

Profile의 원본 선호도와 알레르기 정보도 이후 RAG 요청과 후보 처리 단계에서 사용할 수 있도록 유지됩니다.

<br>

## 14. Recommendation 연동

Recommendation 단계에서는 Profile의 계산 필드를 사용해 각 후보 메뉴를 평가합니다.

### 예산 점수

```text
menu cost
↔ profile.meal_budget
→ budget_score
```

사용 필드:

```text
meal_budget
```

### 영양 점수

```text
menu calories
↔ profile.meal_calorie_target
→ nutrition_score
```

사용 필드:

```text
meal_calorie_target
goals
```

식단 목표에 따라 다음 평가 기준이 달라집니다.

- 다이어트: 칼로리와 지방
- 고단백: 단백질과 과도한 열량
- 영양 균형: 칼로리 범위와 주요 영양소 비율

### 최종 가중 점수

```text
base_final_score
= budget_score × weights.budget
+ nutrition_score × weights.nutrition
+ preference_score × weights.preference
+ difficulty_score × weights.difficulty
+ diversity_score × weights.diversity
```

사용 필드:

```text
weights
meal_budget
meal_calorie_target
max_difficulty
preferred_categories
ingredient_preferences
allergy_ingredients
diversity_penalty_strength
```

관련 모듈:

```text
modeling/services/recommendation/
├── recommendation_service.py
└── scoring_service.py
```

<br>

## 15. Optimizer 연동

Profile은 월간 식단 Optimizer 입력을 구성하는 기초 정보로 전달됩니다.

대표적으로 다음 값이 활용됩니다.

```text
period_days
meal_count_per_day
monthly_budget
meal_budget
goals
weights
max_difficulty
diversity_level
diversity_penalty_strength
daily_calorie_target
meal_calorie_target
```

전체 필요한 끼니 수는 다음 조건을 기준으로 구성할 수 있습니다.

```text
필요 끼니 수
= period_days × meal_count_per_day
```

Profile 자체는 Solver를 실행하지 않습니다.

```text
Profile Builder
→ 사용자 조건 및 파생값 생성
→ Optimizer Input Builder
→ OR-Tools Solver
```

관련 모듈:

```text
modeling/services/optimizer/
├── optimizer_input_builder.py
└── ortools/
    └── monthly_plan_optimizer.py
```

<table style="background-color:#FFF6C7; border-left:6px solid #E6C85C; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>⭐ 역할 구분</strong><br>
      Profile은 추천과 최적화에 사용할 기준값을 생성합니다.
      실제 Solver 변수, 제약조건과 목적함수 구성은
      <code>services/optimizer/</code>에서 수행합니다.
    </td>
  </tr>
</table>

<br>

## 16. 샘플 사용자 데이터

`user_input_service.py`는 JSON 파일에 저장된 사용자 Mock 데이터를 불러오거나 무작위로 한 명을 선택하는 개발·실험용 기능을 제공합니다.

### 전체 사용자 로드

```python
load_sample_users(
    file_path: str = "data/sample_users.json",
) -> list[dict]
```

### 무작위 사용자 선택

```python
select_random_user_input(
    file_path: str = "data/sample_users.json",
) -> dict
```

처리 흐름:

```text
sample_users.json 읽기
→ 사용자 목록 반환
→ random.choice()로 1개 선택
```

사용자 목록이 비어 있으면 다음 오류를 발생시킵니다.

```text
사용자 mock 데이터가 비어 있습니다.
```

샘플 데이터 파일:

```text
modeling/data/sample_users.json
```

<br>

## 17. 실행 및 검증

프로젝트 루트에서 실행합니다.

### Profile 생성 Smoke Test

별도 전용 테스트 파일이 없는 경우 Python 명령으로 직접 확인할 수 있습니다.

```bash
PYTHONPATH=modeling \
python - <<'PY'
from schemas.user_profile_schema import UserProfileInput
from services.profile.profile_service import build_user_profile

user_input = UserProfileInput(
    goals=["다이어트", "간편식"],
    monthly_budget=300000,
    meal_count_per_day=3,
    recommended_daily_calories=1905,
    cooking_skill=2,
    preferred_categories=["한식", "샐러드/건강식"],
    diversity_level="보통",
    ingredient_preferences=["육류", "채소류"],
    allergy_ingredients=["새우"],
    sample_period_days=3,
    period_days=30,
)

profile = build_user_profile(user_input)

print(profile)
PY
```

### 주요 계산값만 확인

```bash
PYTHONPATH=modeling \
python - <<'PY'
from schemas.user_profile_schema import UserProfileInput
from services.profile.profile_service import build_user_profile

profile = build_user_profile(
    UserProfileInput(
        goals=["다이어트", "간편식"],
        monthly_budget=300000,
        meal_count_per_day=3,
        recommended_daily_calories=1905,
        cooking_skill=2,
        preferred_categories=["한식"],
        diversity_level="보통",
        ingredient_preferences=[],
        allergy_ingredients=[],
        period_days=30,
    )
)

print("meal_budget:", profile["meal_budget"])
print("daily_calorie_target:", profile["daily_calorie_target"])
print("meal_calorie_target:", profile["meal_calorie_target"])
print("weights:", profile["weights"])
print("max_difficulty:", profile["max_difficulty"])
print(
    "diversity_penalty_strength:",
    profile["diversity_penalty_strength"],
)
PY
```

예상 핵심 결과:

```text
meal_budget: 3333
daily_calorie_target: 1905
meal_calorie_target: 635.0
max_difficulty: 2
diversity_penalty_strength: 0.45
```

### 문법 검사

```bash
python -m py_compile \
  modeling/schemas/user_profile_schema.py \
  modeling/services/profile/profile_service.py \
  modeling/services/profile/user_input_service.py \
  modeling/services/profile/weight_service.py \
  modeling/utils/calculator.py
```

### 전체 Modeling 테스트

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest modeling/tests -q
```

<br>

## 18. 파일 구조

```text
modeling/
├── schemas/
│   └── user_profile_schema.py
│
├── services/
│   └── profile/
│       ├── __init__.py
│       ├── profile_service.py
│       ├── user_input_service.py
│       ├── weight_service.py
│       └── README.md
│
├── data/
│   └── sample_users.json
│
└── utils/
    └── calculator.py
```

### 파일별 역할

| 파일 | 역할 |
|---|---|
| `user_profile_schema.py` | 사용자 식단 설정 요청과 허용값 검증 |
| `profile_service.py` | 원본 입력과 파생값을 결합한 Modeling Profile 생성 |
| `weight_service.py` | 식단 목표별 가중치 정의 및 복수 목표 병합 |
| `user_input_service.py` | 실험용 사용자 Mock 데이터 로드 및 무작위 선택 |
| `calculator.py` | 월 예산 기반 한 끼 예산 계산 |

<br>

## 19. 현재 구현상 주의사항

### 권장 하루 칼로리는 Profile에서 직접 계산하지 않음

Profile은 `recommended_daily_calories`를 입력으로 전달받습니다.

가구원 신체정보 기반 BMR·TDEE와 권장 칼로리 계산은 Persona 모듈에서 수행합니다.

```text
Persona
→ recommended_daily_calories 생성

Profile
→ daily_calorie_target 유지
→ meal_calorie_target 생성
```

권장 칼로리가 전달되지 않으면 `daily_calorie_target`과 `meal_calorie_target`도 `None`입니다.

### 한 끼 예산은 정수 나눗셈

현재 계산은 `//` 연산자를 사용하므로 소수점 이하는 버려집니다.

```text
300,000 ÷ 30 ÷ 3
= 3,333.333...

실제 반환
= 3,333
```

### 한 끼 예산에 가구원 수 미반영

Persona의 식사당 예산 구간 계산은 가구원 수를 반영하지만, Profile의 `meal_budget` 계산은 가구원 수를 입력받지 않습니다.

```text
Persona 예산 구간
= 월 예산 ÷ 가구원 수 ÷ 식사 횟수 ÷ 기간

Profile 한 끼 예산
= 월 예산 ÷ 식사 횟수 ÷ 기간
```

두 값은 목적과 계산 기준이 다르므로 혼동하지 않아야 합니다.

### period_days가 예산 계산 기간으로 사용됨

`period_days`가 30보다 작으면 동일한 월 예산을 더 짧은 기간으로 나누므로 한 끼 예산이 증가합니다.

```text
period_days = 30
→ 일반적인 월 기준 예산

period_days = 15
→ 동일 예산을 15일에 사용하는 계산
```

요청의 `monthly_budget`이 항상 월 전체 예산을 의미한다면, 기간이 짧은 식단 생성에서도 예산 계산 기준을 30일로 고정할지 정책 검토가 필요할 수 있습니다.

### sample_period_days는 Profile에 유지만 됨

`sample_period_days`는 Profile에 포함되지만 `build_user_profile()`의 한 끼 예산 계산에는 직접 사용되지 않습니다.

`period_days`가 없으면 예산 기준은 30일입니다.

```text
sample_period_days = 3
period_days = None

budget_period_days = 30
meal_budget = 월 예산 ÷ 30 ÷ 식사 횟수
```

따라서 3일치 샘플 식단에서도 월 예산 기준 한 끼 예산을 유지합니다.

### max_difficulty는 cooking_skill과 동일

현재 별도의 난이도 보정 없이 다음과 같이 복사됩니다.

```text
cooking_skill
= max_difficulty
```

난이도 스케일이 변경되면 사용자 입력과 메뉴 난이도 점수의 척도를 함께 검토해야 합니다.

### 다양성 함수의 기본값

정상 요청에서는 Pydantic Validator가 `낮음`, `보통`, `높음` 외 값을 차단합니다.

다만 `get_diversity_penalty_strength()`를 직접 호출할 경우 알 수 없는 값은 `0.45`로 처리됩니다.

### 가중치 최종 합계

평균 후 다시 정규화하지만, 각 항목을 소수점 넷째 자리로 반올림하므로 최종 합계가 극히 작은 수준에서 정확히 `1.0`과 다를 가능성이 있습니다.

### request_type 응답값

`build_user_profile_response()`는 입력 요청 종류와 무관하게 다음 값을 반환합니다.

```text
request_type = profile_build
```

이 함수는 내부 Profile 변환 결과를 나타내기 위한 응답이므로, 원본 요청 종류를 유지하지 않습니다.

### Mock 데이터 기본 경로

`user_input_service.py`의 기본 경로는 다음과 같습니다.

```text
data/sample_users.json
```

이는 실행 시 현재 작업 디렉터리에 따라 경로 해석이 달라질 수 있습니다.

프로젝트 루트에서 직접 호출하면 실제 파일 경로인 `modeling/data/sample_users.json`을 명시하는 것이 안전합니다.

```python
load_sample_users("modeling/data/sample_users.json")
```

<table style="background-color:#FFF6C7; border-left:6px solid #E6C85C; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>⭐ 설계 요약</strong><br>
      Profile 모듈은 사용자 식단 설정을 보존하면서,
      추천·RAG·최적화에서 공통으로 사용할 한 끼 예산, 칼로리 기준,
      목표별 가중치, 조리 난이도와 다양성 정책을 추가합니다.
      이를 통해 이후 단계가 동일한 사용자 조건을 기준으로 동작하도록 합니다.
    </td>
  </tr>
</table>
