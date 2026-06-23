# 👥 Persona & Recommended Calorie

사용자의 가구 형태, 가구원 신체 정보, 예산, 활동량과 식단 목적을 기반으로 다음 결과를 생성하는 모듈입니다.

- 가구원별 기초대사량(BMR)
- 활동량이 반영된 일일 에너지 소비량(TDEE)
- 식단 목적이 반영된 권장 하루 칼로리
- 사용자 조건과 가까운 대표 페르소나 후보 4개

```text
가구 및 가구원 정보
→ 입력값 검증
→ 활동량 정규화
→ 가구원별 BMR 계산
→ TDEE 계산
→ 식단 목적별 칼로리 보정
→ 사용자·가구 기준 권장 칼로리 생성
→ 페르소나 조건 변환
→ 대표 페르소나 점수 계산
→ 상위 4개 후보 반환
```

<br>

## 목차

1. [모듈 역할](#1-모듈-역할)
2. [입력 스키마](#2-입력-스키마)
3. [전체 처리 흐름](#3-전체-처리-흐름)
4. [활동량 정규화](#4-활동량-정규화)
5. [BMR 계산](#5-bmr-계산)
6. [TDEE 계산](#6-tdee-계산)
7. [식단 목적별 칼로리 보정](#7-식단-목적별-칼로리-보정)
8. [가구 기준 권장 칼로리](#8-가구-기준-권장-칼로리)
9. [식사당 예산 구간](#9-식사당-예산-구간)
10. [페르소나 카탈로그](#10-페르소나-카탈로그)
11. [페르소나 점수 계산](#11-페르소나-점수-계산)
12. [후보 정렬 및 반환](#12-후보-정렬-및-반환)
13. [최종 응답 구조](#13-최종-응답-구조)
14. [실행 및 검증](#14-실행-및-검증)
15. [파일 구조](#15-파일-구조)
16. [현재 구현상 주의사항](#16-현재-구현상-주의사항)
17. [관련 문서](#17-관련-문서)

<br>

## 1. 모듈 역할

Persona 모듈은 식단 추천에 앞서 사용자의 기본 특성을 정리하는 1차 프로필 생성 단계입니다.

주요 역할은 다음과 같습니다.

### 권장 칼로리 생성

- 가구원별 성별, 나이, 키, 체중 검증
- Mifflin-St Jeor 공식 기반 BMR 계산
- 활동량 계수 기반 TDEE 계산
- 다이어트·고단백 목적에 따른 칼로리 보정
- 가구원별 계산 결과 제공
- 사용자·가구 기준 권장 하루 칼로리 제공

### 페르소나 후보 생성

- 가구 형태 구분
- 식사당 예산 구간 계산
- 활동량 정규화
- 식단 목적 일치도 계산
- 식사 횟수 적합성 계산
- 대표 페르소나 20개 중 상위 4개 반환

<table style="background-color:#EAF4FF; border-left:6px solid #4D96D9; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>💡 핵심 역할</strong><br>
      Persona 모듈은 최종 식단을 직접 생성하지 않습니다.
      추천에 필요한 권장 칼로리와 사용자 특성 후보를 생성하고,
      이후 Profile·Recommendation·Optimizer 단계에서 사용할 기초 정보를 제공합니다.
    </td>
  </tr>
</table>

<br>

## 2. 입력 스키마

입력 스키마는 다음 파일에서 관리합니다.

```text
modeling/schemas/persona_profile_schema.py
```

### FamilyMemberInput

가구원 한 명의 신체 정보를 표현합니다.

| 필드 | 타입 | 조건 | 설명 |
|---|---|---|---|
| `nickname` | `str` | 필수 | 가구원 표시 이름 |
| `gender` | `str` | 필수 | 성별 |
| `age` | `int` | `1~120` | 나이 |
| `height` | `float` | `0 초과` | 키(cm) |
| `weight` | `float` | `0 초과` | 체중(kg) |

### PersonaProfileBuildInput

페르소나 생성과 권장 칼로리 계산에 필요한 전체 요청입니다.

| 필드 | 타입 | 조건 | 설명 |
|---|---|---|---|
| `id` | `int \| str` | 필수 | 사용자 식별값 |
| `household_type` | `str` | 필수 | `1인 가구` 또는 `다인 가구` |
| `family_count` | `int` | `1 이상` | 가구원 수 |
| `monthly_budget` | `int` | `0 초과` | 월 식비 예산 |
| `meals_per_day` | `int` | `1~5` | 하루 식사 횟수 |
| `purpose` | `List[str]` | 1개 이상 | 식단 목적 |
| `activity_level` | `int \| str` | 필수 | 활동량 단계 또는 설명 문구 |
| `family_members` | `List[FamilyMemberInput]` | 1명 이상 | 가구원 신체 정보 |

### 요청 예시

```json
{
  "id": 4,
  "household_type": "1인 가구",
  "family_count": 1,
  "monthly_budget": 300000,
  "meals_per_day": 3,
  "purpose": [
    "다이어트",
    "간편식"
  ],
  "activity_level": 2,
  "family_members": [
    {
      "nickname": "본인",
      "gender": "남",
      "age": 26,
      "height": 178.0,
      "weight": 75.5
    }
  ]
}
```

<br>

## 3. 전체 처리 흐름

```text
PersonaProfileBuildInput
        ↓
Pydantic 입력 검증
        ↓
활동량 정규화
        ├── 정수 1~4
        ├── 활동량 설명 문구
        └── 숫자 문자열
        ↓
가구원별 칼로리 계산
        ├── BMR
        ├── TDEE
        └── 식단 목적별 보정
        ↓
가구 기준 권장 하루 칼로리
        ↓
페르소나 요청 조건 생성
        ├── 가구 형태
        ├── 식사당 예산 구간
        ├── 활동량
        ├── 식사 횟수
        └── 식단 목적
        ↓
동일 가구 형태의 페르소나만 필터링
        ↓
페르소나별 적합도 점수 계산
        ↓
점수 및 세부 기준으로 정렬
        ↓
상위 4개 후보 단순화
        ↓
profile_build 응답 반환
```

<br>

## 4. 활동량 정규화

활동량은 숫자 또는 사용자 친화적인 문구로 입력할 수 있습니다.

### 활동량 단계

| 단계 | 사용자 문구 | TDEE 계수 |
|---|---|---:|
| `1` | 거의 앉아서 생활해요 | `1.2` |
| `2` | 가벼운 활동을 해요 | `1.375` |
| `3` | 보통 활동을 해요 | `1.55` |
| `4` | 활동이 많아요 | `1.725` |

### 정규화 규칙

```text
정수 입력
→ 1~4 범위로 제한

등록된 활동량 문구
→ 대응하는 단계로 변환

숫자 문자열
→ 정수 변환 후 1~4 범위로 제한

지원하지 않는 문자열 또는 기타 값
→ 기본값 2
```

예시:

| 입력 | 변환 결과 |
|---|---:|
| `1` | `1` |
| `5` | `4` |
| `"3"` | `3` |
| `"보통 활동을 해요"` | `3` |
| `"알 수 없음"` | `2` |

관련 함수:

```python
normalize_activity_level(activity_level: int | str) -> int
```

<br>

## 5. BMR 계산

가구원별 기초대사량은 Mifflin-St Jeor 공식을 사용해 계산합니다.

### 남성

```text
BMR
= 10 × 체중(kg)
+ 6.25 × 키(cm)
- 5 × 나이
+ 5
```

### 여성

```text
BMR
= 10 × 체중(kg)
+ 6.25 × 키(cm)
- 5 × 나이
- 161
```

관련 함수:

```python
calculate_bmr(member: dict[str, Any]) -> float
```

### 성별 처리 기준

현재 구현에서는 `gender == "여"`인 경우 여성 공식을 사용합니다.

그 외 값은 남성 공식으로 처리됩니다.

<table style="background-color:#FFF1E6; border-left:6px solid #E67E22; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>⚠️ 입력값 주의</strong><br>
      현재 Pydantic 스키마에서는 <code>gender</code>가 일반 문자열로 선언되어 있습니다.
      지원하는 성별 값에 대한 별도 Validator는 없으므로,
      Backend와 Frontend에서 약속된 값인 <code>남</code>과 <code>여</code>를 전달해야 합니다.
    </td>
  </tr>
</table>

<br>

## 6. TDEE 계산

TDEE는 BMR에 정규화된 활동량 계수를 곱해 계산합니다.

```text
TDEE
= BMR × 활동량 계수
```

예시:

```text
BMR 1,700 kcal
활동량 단계 2
TDEE 계수 1.375

1,700 × 1.375
= 2,337.5 kcal
```

관련 함수:

```python
calculate_member_recommended_calorie(
    member: dict[str, Any],
    activity_level: int,
    purposes: list[str],
) -> dict[str, Any]
```

가구원별 계산 결과에는 다음 정보가 포함됩니다.

```text
nickname
gender
age
height
weight
bmr
activity_level
activity_label
estimated_tdee
recommended_daily_calories
```

<br>

## 7. 식단 목적별 칼로리 보정

계산된 TDEE는 사용자가 선택한 식단 목적에 따라 보정됩니다.

### 다이어트

```text
보정 칼로리
= max(
    TDEE - 500,
    1,200,
    BMR × 0.95
  )
```

다이어트 목적에서는 다음 세 기준 중 가장 큰 값을 선택합니다.

- TDEE에서 500kcal 차감
- 최소 1,200kcal
- BMR의 95% 이상

지나치게 낮은 권장 열량이 반환되는 것을 방지하기 위한 안전 기준입니다.

### 고단백

```text
보정 칼로리
= TDEE + 300
```

고단백 또는 근육량 증가 목적을 고려해 TDEE보다 300kcal 높은 값을 사용합니다.

### 기타 목적

```text
보정 칼로리
= TDEE
```

식비 절약, 영양 균형, 간편식, 맛 중심 등은 별도의 열량 가감 없이 TDEE를 유지합니다.

### 복수 목적 우선순위

다이어트와 고단백이 함께 선택되면 다이어트 보정이 우선됩니다.

```python
if "다이어트" in purposes:
    ...
elif "고단백" in purposes:
    ...
else:
    ...
```

### 최대 상한

모든 계산 결과는 최대 `3,500kcal`로 제한됩니다.

관련 함수:

```python
apply_goal_calorie_adjustment(
    tdee: float,
    bmr: float,
    purposes: list[str],
) -> int
```

<br>

## 8. 가구 기준 권장 칼로리

각 가구원에 대해 개별 권장 칼로리를 계산한 뒤, 전체 가구원의 평균값을 사용자·가구 기준 권장 하루 칼로리로 반환합니다.

```text
가구 기준 권장 하루 칼로리
= 가구원별 권장 하루 칼로리의 합
÷ 가구원 수
```

관련 함수:

```python
calculate_recommended_calories(
    family_members: list[dict[str, Any]],
    activity_level: int,
    purposes: list[str],
) -> dict[str, Any]
```

### 반환 구조

```json
{
  "recommended_daily_calories": 2100,
  "member_calories": [
    {
      "nickname": "본인",
      "gender": "남",
      "age": 26,
      "height": 178.0,
      "weight": 75.5,
      "bmr": 1748.75,
      "activity_level": 2,
      "activity_label": "가벼운 활동을 해요",
      "estimated_tdee": 2404.53,
      "recommended_daily_calories": 1905
    }
  ]
}
```

<table style="background-color:#FFF6C7; border-left:6px solid #E6C85C; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>⭐ 현재 계산 기준</strong><br>
      다인 가구의 최종 <code>recommended_daily_calories</code>는
      가구원 전체 필요 열량의 합계가 아니라 <strong>가구원별 권장 칼로리의 평균값</strong>입니다.
      각 가구원의 상세 계산값은 내부 <code>member_calories</code>에 생성되지만,
      현재 최종 <code>profile_build</code> 응답에는 평균 권장 칼로리만 포함됩니다.
    </td>
  </tr>
</table>

<br>

## 9. 식사당 예산 구간

월 예산은 가구원 수, 하루 식사 횟수와 30일을 기준으로 식사당 예산으로 변환합니다.

```text
식사당 예산
= 월 예산
÷ (가구원 수 × 하루 식사 횟수 × 30일)
```

### 예산 구간

| 식사당 예산 | 구간 |
|---:|---|
| 2,500원 미만 | `very_low` |
| 2,500원 이상 4,500원 미만 | `low` |
| 4,500원 이상 7,000원 미만 | `medium` |
| 7,000원 이상 | `high` |

관련 함수:

```python
get_meal_budget_band(
    monthly_budget: int,
    family_count: int,
    meals_per_day: int,
    period_days: int = 30,
) -> str
```

### 계산 예시

```text
월 예산: 300,000원
가구원 수: 1명
하루 식사: 3끼
기간: 30일

300,000 ÷ (1 × 3 × 30)
= 약 3,333원

예산 구간: low
```

<br>

## 10. 페르소나 카탈로그

페르소나 카탈로그는 Frontend 이미지 매핑과 카드 UI 관리를 고려하여 대표 페르소나 20개로 고정되어 있습니다.

```text
전체 20개
├── 1인 가구 10개
└── 다인 가구 10개
```

관련 파일:

```text
services/persona/persona_catalog.py
```

### 페르소나 구조

각 페르소나는 다음 정보를 가집니다.

| 필드 | 설명 |
|---|---|
| `persona_id` | Frontend 이미지 및 카드 매핑용 고유 ID |
| `household_type` | `1인 가구` 또는 `다인 가구` |
| `description` | 사용자에게 표시할 페르소나 이름 |
| `summary` | 사용자 친화형 설명 |
| `target_purposes` | 주요 식단 목적 |
| `target_budget_bands` | 적합한 식사당 예산 구간 |
| `target_activity_levels` | 적합한 활동량 단계 |
| `target_meals_per_day` | 적합한 하루 식사 횟수 |

### 1인 가구 대표 유형

- 가성비 절약형
- 가벼운 관리형
- 단백질 충전형
- 초간단 해결형
- 균형식단 루틴형
- 입맛만족 추구형
- 탄탄관리 단백형
- 알뜰간편 생존형
- 실속관리 루틴형
- 다채로운 루틴형

### 다인 가구 대표 유형

- 가족예산 수비대형
- 가족균형 식단형
- 가족식단 해결사형
- 가족단백 충전형
- 가족건강 관리형
- 가족입맛 조율형
- 가족알뜰 균형러형
- 가족알뜰 간편형
- 가족건강 루틴러형
- 다채로운 가족식탁형

<br>

## 11. 페르소나 점수 계산

요청 조건과 각 대표 페르소나의 조건을 비교해 적합도 점수를 계산합니다.

관련 함수:

```python
calculate_persona_match_score(
    persona: dict[str, Any],
    request_condition: dict[str, Any],
) -> dict[str, Any]
```

### 점수 기준

| 조건 | 점수 |
|---|---:|
| 가구 형태 일치 | `+100` |
| 식단 목적 1개 일치 | `+35` |
| 식사당 예산 구간 일치 | `+18` |
| 활동량 단계 일치 | `+10` |
| 하루 식사 횟수 일치 | `+8` |
| 사용자 목적이 페르소나에 누락 | 목적당 `-8` |
| 페르소나에 불필요한 목적 존재 | 목적당 `-3` |

### 계산 예시

사용자 조건:

```text
가구 형태: 1인 가구
목적: 다이어트, 간편식
예산 구간: low
활동량: 2
하루 식사: 3끼
```

`실속관리 루틴형`이 아래 조건을 가진다고 가정합니다.

```text
가구 형태 일치
다이어트 일치
간편식 일치
예산 구간 일치
활동량 일치
식사 횟수 일치
```

점수:

```text
가구 형태       +100
목적 2개 일치    +70
예산 구간        +18
활동량           +10
식사 횟수         +8
────────────────────
총점             206
```

### 매칭 사유

조건이 일치하면 다음 값이 `match_reasons`에 포함됩니다.

```text
household_type
budget_band
activity_level
meals_per_day
```

식단 목적 일치 개수는 `matched_purpose_count`로 별도 반환됩니다.

<br>

## 12. 후보 정렬 및 반환

먼저 요청과 가구 형태가 동일한 페르소나만 비교합니다.

```text
1인 가구 요청
→ 1인 가구 페르소나 10개만 평가

다인 가구 요청
→ 다인 가구 페르소나 10개만 평가
```

평가된 페르소나는 다음 순서로 정렬됩니다.

```text
1. score 내림차순
2. missing_purpose_count 오름차순
3. extra_purpose_count 오름차순
4. persona_id 오름차순
```

코드 기준 정렬 키:

```python
key=lambda item: (
    -item["score"],
    item["missing_purpose_count"],
    item["extra_purpose_count"],
    item["persona_id"],
)
```

기본적으로 상위 4개 후보를 반환합니다.

```python
build_persona_candidates(
    request_data=request_data,
    limit=4,
)
```

### Frontend 반환 정보 단순화

내부 계산에서는 점수와 매칭 조건을 모두 관리하지만, 최종 응답에는 Frontend 표시와 이미지 매핑에 필요한 정보만 반환합니다.

```json
{
  "rank": 1,
  "persona_id": "persona_single_diet_easy",
  "description": "실속관리 루틴형",
  "summary": "건강 관리와 간편함을 함께 챙기고 싶은 1인 가구예요."
}
```

관련 함수:

```python
simplify_persona_candidate(
    persona: dict[str, Any] | None,
) -> dict[str, Any] | None
```

<br>

## 13. 최종 응답 구조

최종 응답은 다음 함수에서 생성합니다.

```python
build_persona_profile_response(
    request_data: dict[str, Any],
) -> dict[str, Any]
```

### 응답 예시

```json
{
  "id": 4,
  "request_type": "profile_build",
  "recommended_daily_calories": 1905,
  "persona_candidates": [
    {
      "rank": 1,
      "persona_id": "persona_single_diet_easy",
      "description": "실속관리 루틴형",
      "summary": "건강 관리와 간편함을 함께 챙기고 싶은 1인 가구예요."
    },
    {
      "rank": 2,
      "persona_id": "persona_single_diet_light",
      "description": "가벼운 관리형",
      "summary": "칼로리 부담을 줄이고 체중 관리를 꾸준히 이어가고 싶은 1인 가구예요."
    }
  ]
}
```

### 반환 필드

| 필드 | 설명 |
|---|---|
| `id` | 요청 사용자 식별값 |
| `request_type` | 항상 `profile_build` |
| `recommended_daily_calories` | 가구원별 권장 열량의 평균 |
| `persona_candidates` | 점수 기준 상위 페르소나 후보 |

<br>

## 14. 실행 및 검증

프로젝트 루트에서 실행합니다.

### 기존 실행 스크립트

```bash
PYTHONPATH=modeling \
python modeling/tests/persona/test_persona_profile_build.py
```

현재 스크립트는 다음 흐름을 확인합니다.

```text
샘플 요청 생성
→ Pydantic 입력 검증
→ 페르소나 프로필 생성
→ JSON 응답 출력
```

### 출력 예시 확인

```bash
PYTHONPATH=modeling \
python modeling/tests/persona/test_persona_profile_build.py \
  | python -m json.tool
```

다만 Python 스크립트가 이미 들여쓰기된 JSON을 출력하므로, 기본 실행만으로도 결과를 확인할 수 있습니다.

### 문법 검사

```bash
python -m py_compile \
  modeling/schemas/persona_profile_schema.py \
  modeling/services/persona/persona_service.py \
  modeling/services/persona/persona_catalog.py \
  modeling/tests/persona/test_persona_profile_build.py
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
      <strong>⚠️ 현재 Persona 검증 파일</strong><br>
      <code>test_persona_profile_build.py</code>는 샘플 요청을 실행하고 응답을 출력하는
      Smoke Test 성격의 스크립트입니다.
      현재 파일에는 <code>assert</code> 기반의 세부 단위 테스트가 포함되어 있지 않습니다.
    </td>
  </tr>
</table>

<br>

## 15. 파일 구조

```text
modeling/
├── schemas/
│   └── persona_profile_schema.py
│
├── services/
│   └── persona/
│       ├── __init__.py
│       ├── persona_catalog.py
│       ├── persona_service.py
│       └── README.md
│
└── tests/
    └── persona/
        ├── __init__.py
        └── test_persona_profile_build.py
```

### 파일별 역할

| 파일 | 역할 |
|---|---|
| `persona_profile_schema.py` | Persona 요청과 가구원 입력 검증 |
| `persona_catalog.py` | 대표 페르소나 20개 정의 |
| `persona_service.py` | 칼로리 계산, 조건 변환, 점수 계산 및 응답 생성 |
| `test_persona_profile_build.py` | 샘플 요청 기반 실행 및 응답 확인 |

<br>

## 16. 현재 구현상 주의사항

### 가구 권장 칼로리는 평균값

다인 가구의 최종 권장 칼로리는 가구 전체 섭취량의 합이 아니라 가구원별 권장 칼로리의 평균입니다.

```text
현재 구현
→ 가구원별 권장 칼로리 평균

가구 전체 필요 열량이 필요한 경우
→ 가구원별 권장 칼로리 합계 별도 계산 필요
```

### 활동량은 가구 전체에 공통 적용

요청에는 `activity_level`이 하나만 존재하므로 모든 가구원에게 동일한 활동량 계수가 적용됩니다.

가구원별 활동량을 따로 반영하려면 `FamilyMemberInput`에 활동량 필드를 추가해야 합니다.

### 성별 Validator 없음

현재 `gender`는 일반 문자열입니다.

`여`가 아닌 값은 남성 공식으로 처리되므로, 입력 계약을 명확히 유지하거나 Enum·Validator를 추가하는 것이 안전합니다.

### family_count와 family_members 길이

현재 스키마에서는 다음 두 값이 일치하는지 별도로 검증하지 않습니다.

```text
family_count
len(family_members)
```

데이터 정합성을 강화하려면 모델 수준 Validator를 추가할 수 있습니다.

### family_count_group

`get_family_count_group()` 함수와 `family_count_group` 요청 조건은 생성되지만, 현재 페르소나 점수 계산에는 직접 사용되지 않습니다.

현재 카탈로그는 세부 가구원 수가 아니라 다음 두 가구 유형을 기준으로 필터링합니다.

```text
1인 가구
다인 가구
```

### 상세 칼로리 결과 미노출

내부적으로 가구원별 BMR, TDEE와 권장 칼로리를 계산하지만, 최종 `profile_build` 응답에는 다음만 포함됩니다.

```text
recommended_daily_calories
persona_candidates
```

가구원별 상세 계산값이 Frontend 또는 Backend에 필요하다면 응답 계약 확장이 필요합니다.

<table style="background-color:#FFF6C7; border-left:6px solid #E6C85C; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>⭐ 설계 요약</strong><br>
      Persona 모듈은 고정된 대표 페르소나 카탈로그를 사용해 Frontend 이미지 매핑을 안정화하고,
      사용자 조건별 점수 계산을 통해 가장 가까운 후보를 제공합니다.
      동시에 가구원 신체 정보와 활동량을 기반으로 추천 파이프라인에서 사용할
      권장 하루 칼로리를 생성합니다.
    </td>
  </tr>
</table>

<br>

## 17. 관련 문서

Persona 생성 로직의 기획 배경, 온보딩 입력 구조와 상세 설계 내용은 아래 Notion 문서에서 확인할 수 있습니다.

- [📘 Persona 및 권장 칼로리 상세 문서](https://app.notion.com/p/3809e3e335cc808c8235c61fed49adb3?source=copy_link)
