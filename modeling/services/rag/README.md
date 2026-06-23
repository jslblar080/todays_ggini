# 🕸️ RAG Candidate Integration

사용자 Profile을 RAG 후보 메뉴 요청으로 변환하고, RAG 응답을 추천·최적화에서 사용할 수 있는 Modeling Menu 구조로 매핑하는 모듈입니다.

RAG 연동 과정에서는 단순히 후보 메뉴를 전달받는 것에 그치지 않고, 재료 가격 기반 예상 비용 계산, 조리 난이도 산정, 재료군 보정, 영양 데이터 검증 및 후보 부족 진단까지 수행합니다.

```text
Modeling Profile
→ RAG 요청 Payload 생성
→ 후보 메뉴 API 호출
→ HTTP 오류 및 Timeout 처리
→ RAG 응답 후보 추출
→ 재료·영양·가격·레시피 매핑
→ 예상 비용 및 조리 난이도 계산
→ 재료군 보정
→ 데이터 품질 검사
→ Quality Score 및 Issue 기록
→ Modeling Candidate Menu 반환
```

<br>

## 목차

1. [모듈 역할](#1-모듈-역할)
2. [전체 처리 흐름](#2-전체-처리-흐름)
3. [RAG 요청 Payload](#3-rag-요청-payload)
4. [후보 메뉴 요청 수 계산](#4-후보-메뉴-요청-수-계산)
5. [RAG HTTP Client](#5-rag-http-client)
6. [RAG 오류 처리](#6-rag-오류-처리)
7. [RAG 응답 구조 변환](#7-rag-응답-구조-변환)
8. [메뉴 영양 정보 매핑](#8-메뉴-영양-정보-매핑)
9. [재료와 가격 정보 처리](#9-재료와-가격-정보-처리)
10. [예상 메뉴 비용 계산](#10-예상-메뉴-비용-계산)
11. [조리 난이도 계산](#11-조리-난이도-계산)
12. [재료군 보정](#12-재료군-보정)
13. [RAG 데이터 품질 검사](#13-rag-데이터-품질-검사)
14. [영양 이상치 진단](#14-영양-이상치-진단)
15. [RAG Quality Score](#15-rag-quality-score)
16. [Mapping Diagnostics](#16-mapping-diagnostics)
17. [후보 풀 진단](#17-후보-풀-진단)
18. [후보 부족 및 Fallback](#18-후보-부족-및-fallback)
19. [추가 후보 병합](#19-추가-후보-병합)
20. [Modeling Service 연동](#20-modeling-service-연동)
21. [실행 및 검증](#21-실행-및-검증)
22. [파일 구조](#22-파일-구조)
23. [현재 구현상 주의사항](#23-현재-구현상-주의사항)
24. [관련 문서](#24-관련-문서)

<br>

## 1. 모듈 역할

RAG 연동 모듈은 Modeling과 외부 메뉴 지식 검색 시스템 사이의 Adapter 역할을 담당합니다.

### 요청 단계

- 사용자 Profile에서 RAG 검색 조건 추출
- 목표, 예산, 선호 카테고리 및 재료군 전달
- 알레르기 및 제외 재료 전달
- 필요한 후보 메뉴 수 전달
- 응답 형식 지정

### 응답 단계

- RAG 응답에서 후보 메뉴 목록 추출
- Modeling 내부 메뉴 구조로 변환
- 영양 성분과 레시피 데이터 정규화
- 재료 사용량과 상품 가격을 이용한 비용 계산
- 레시피 정보 기반 조리 난이도 계산
- 누락된 재료군 정보 보완
- 데이터 품질 이슈와 이상치 기록

### 후보 관리 단계

- 후보 메뉴 수와 고유 메뉴 수 진단
- Optimizer 입력에 필요한 후보 수 확인
- 후보 부족 사유 분석
- 추가 요청 수 계산
- 기존 후보와 추가 후보 병합
- 중복 메뉴 제거

<table style="background-color:#EAF4FF; border-left:6px solid #4D96D9; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>💡 핵심 역할</strong><br>
      RAG 모듈은 검색 결과를 그대로 추천 엔진에 전달하지 않습니다.
      외부 응답을 Modeling이 신뢰할 수 있는 구조로 변환하고,
      비용·난이도·품질 정보를 추가하여 Recommendation과 Optimizer가 사용할 후보 풀을 생성합니다.
    </td>
  </tr>
</table>

<br>

## 2. 전체 처리 흐름

```text
User Profile
  ↓
build_rag_request()
  ├── goals
  ├── meal_budget
  ├── preferred_categories
  ├── ingredient_preferences
  ├── allergy_ingredients
  └── candidate_count
  ↓
request_candidate_menus_from_rag()
  ↓
RAG Cloud API
  ↓
Raw Candidate Menus
  ↓
map_rag_response_to_candidate_menus()
  ├── 필수 필드 검사
  ├── 재료군 보정
  ├── 예상 비용 계산
  ├── 조리 난이도 계산
  ├── 영양 이상치 분석
  ├── 데이터 품질 점수 계산
  └── Mapping Diagnostics 기록
  ↓
Modeling Candidate Menus
  ↓
Candidate Pool Diagnostics
  ↓
Recommendation / OR-Tools Optimizer
```

<br>

## 3. RAG 요청 Payload

RAG 요청은 다음 함수에서 생성합니다.

```python
build_rag_request(
    user_id: int | str,
    profile: dict,
    candidate_count: int,
) -> dict
```

관련 파일:

```text
modeling/services/rag/rag_request_service.py
```

### 요청 구조

```json
{
  "user_id": 4,
  "request_type": "meal_candidates",
  "candidate_count": 270,
  "conditions": {
    "goals": [
      "다이어트",
      "간편식"
    ],
    "meal_budget": 3333,
    "preferred_categories": [
      "한식"
    ],
    "ingredient_preferences": [
      "육류",
      "채소류"
    ],
    "allergy_ingredients": [
      "새우"
    ]
  },
  "response_format": "candidate_menus_v1"
}
```

### Profile에서 사용하는 필드

| Profile 필드 | RAG 요청 용도 |
|---|---|
| `goals` | 식단 목적 기반 후보 검색 |
| `meal_budget` | 한 끼 예산 범위 반영 |
| `preferred_categories` | 선호 음식 카테고리 검색 |
| `ingredient_preferences` | 선호 재료군 검색 |
| `allergy_ingredients` | 알레르기·제외 재료 필터 |
| `candidate_count` | 요청할 후보 메뉴 개수 |

### 응답 형식

```text
candidate_menus_v1
```

Modeling은 RAG가 해당 계약에 맞는 후보 메뉴 배열을 반환한다고 가정합니다.

<br>

## 4. 후보 메뉴 요청 수 계산

RAG에 요청할 후보 수는 식단 기간과 하루 식사 횟수를 기준으로 계산합니다.

기본 계산 함수:

```python
calculate_candidate_count(
    meal_count_per_day: int,
    period_days: int = 7,
    buffer_multiplier: int = 3,
) -> int
```

계산식:

```text
후보 요청 수
= 하루 식사 횟수
× 식단 기간
× Buffer 배수
```

예시:

```text
하루 3끼
7일 식단
Buffer 3배

3 × 7 × 3
= 후보 63개
```

### 식단 스타일 후보 요청

식단 스타일용 후보 수는 다음 방식으로 계산됩니다.

```text
sample_period_days
× meal_count_per_day
× 3
```

예시:

```text
샘플 기간 3일
하루 3끼

3 × 3 × 3
= 후보 27개
```

### 월간 식단 후보 요청

월간 식단에서는 필요한 전체 끼니 수에 RAG 후보 배수를 적용합니다.

```text
required_meal_count
= period_days × meal_count_per_day

candidate_count
= required_meal_count × rag_candidate_multiplier
```

최종 후보 요청 수는 최소한 필요한 전체 끼니 수 이상이 되도록 처리합니다.

```text
max(required_meal_count, candidate_count)
```

예시:

```text
30일 × 하루 3끼
= 필요 끼니 90개

RAG 후보 배수 3.0
→ 요청 후보 270개
```

<br>

## 5. RAG HTTP Client

외부 RAG API 호출은 다음 함수에서 수행합니다.

```python
request_candidate_menus_from_rag(
    rag_request: dict,
) -> dict
```

관련 파일:

```text
modeling/services/rag/rag_client.py
```

기본 RAG API 주소:

```text
https://api.kkini.cloud/api/v1/meal-candidates
```

운영 및 로컬 환경에서는 다음 환경변수로 변경할 수 있습니다.

```text
RAG_API_URL
```

### 호출 흐름

```text
RAG 요청 Dictionary
→ JSON HTTP 요청
→ 응답 상태 확인
→ JSON Body 파싱
→ Dictionary 반환
```

외부 통신 실패는 일반 예외를 그대로 노출하지 않고 `RagRequestError`로 변환합니다.

```python
class RagRequestError(RuntimeError):
    ...
```

<table style="background-color:#FFF1E6; border-left:6px solid #E67E22; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>⚠️ 외부 시스템 의존성</strong><br>
      실제 RAG 호출은 네트워크 상태, RAG 서버 부하, 응답 후보 수 및 데이터베이스 조회시간에 영향을 받습니다.
      따라서 API 서버에서는 외부 오류를 내부 오류와 분리하고,
      Backend가 구분할 수 있는 상태 코드와 실패 사유로 변환합니다.
    </td>
  </tr>
</table>

<br>

## 6. RAG 오류 처리

RAG 요청 과정의 오류는 `RagRequestError`로 구조화됩니다.

대표적으로 구분되는 상황은 다음과 같습니다.

- RAG 연결 실패
- 요청 Timeout
- RAG 인증 실패
- RAG Client 오류
- RAG Server 오류
- 응답 JSON 파싱 실패
- 예상하지 못한 네트워크 오류

Modeling API에서는 `RagRequestError`의 실패 사유를 기반으로 적절한 HTTP 상태 코드로 매핑합니다.

관련 파일:

```text
modeling/api/server.py
modeling/services/rag/rag_client.py
```

관련 함수:

```python
get_rag_error_status_code(error: RagRequestError) -> int
```

### 오류 처리 흐름

```text
RAG API 오류
→ RagRequestError
→ failure_reason 확인
→ Modeling API 상태 코드 변환
→ API Error Metric 기록
→ Backend에 구조화된 오류 반환
```

### 운영 로그 원칙

로그에는 다음 정보를 남길 수 있습니다.

```text
request path
failure_reason
RAG status code
elapsed time
request ID
```

다음 정보는 로그에 직접 기록하지 않는 것이 안전합니다.

```text
API Key
사용자 민감정보
전체 요청 Body
전체 RAG 응답
대용량 메뉴·재료 데이터
```

<br>

## 7. RAG 응답 구조 변환

RAG 응답은 다음 함수에서 Modeling 후보 메뉴 목록으로 변환합니다.

```python
map_rag_response_to_candidate_menus(
    rag_response: dict,
) -> list[dict]
```

관련 파일:

```text
modeling/services/rag/rag_response_mapper.py
```

지원 응답 구조:

```json
{
  "response_format": "candidate_menus_v1",
  "candidate_menus": [
    {}
  ]
}
```

### 매핑 처리

```text
candidate_menus 추출
→ 후보별 원본 데이터 검증
→ Modeling Menu 구조 생성
→ 품질 이슈 목록 추가
→ RAG 품질 점수 추가
→ 전체 후보 목록 반환
```

후보 하나를 변환하는 함수:

```python
map_candidate_menu_to_modeling_menu(
    candidate_menu: dict,
) -> dict
```

### Modeling 후보의 대표 필드

```text
menu_id
name
category
ingredients
ingredient_groups
ingredient_group_mapping
calories
protein
carbohydrate
fat
estimated_cost
ingredient_costs
difficulty
difficulty_detail
ingredient_usages
similar_menu_ids
allergy_ingredients
recipe
nutrition_outlier
rag_data_quality_score
rag_data_quality_issues
```

<br>

## 8. 메뉴 영양 정보 매핑

RAG 메뉴의 영양 정보는 Modeling 점수 계산과 검증에 사용할 수 있도록 평탄화됩니다.

대표 영양 필드:

```text
calories
protein
carbohydrate
fat
```

영양 정보는 후보 메뉴의 직접 필드 또는 `nutrient_summary` 구조에서 추출됩니다.

### 활용 위치

| 영양 필드 | 활용 |
|---|---|
| `calories` | 끼니 목표 열량과 비교 |
| `protein` | 고단백 목표 점수 및 보정 |
| `carbohydrate` | 영양 균형 평가 |
| `fat` | 다이어트·영양 균형 평가 |

매핑된 영양 정보는 다음 단계에서 사용됩니다.

```text
Recommendation nutrition_score
Optimizer protein bonus
Plan Summary
Style Validation
RAG Quality Penalty
```

<br>

## 9. 재료와 가격 정보 처리

RAG 후보 메뉴에는 다음과 같은 재료 관련 정보가 포함될 수 있습니다.

```text
ingredients
ingredient_groups
ingredient_usages
lowest_price
product information
estimated_cost
```

### 재료 사용량

`ingredient_usages`에는 메뉴 한 개를 만들 때 사용하는 재료량과 단위가 포함될 수 있습니다.

```json
{
  "ingredient_name": "닭가슴살",
  "usage_amount": 150,
  "usage_unit": "g"
}
```

### 가격 정보

재료에는 상품 가격, 상품 용량과 단위 정보가 포함될 수 있습니다.

```text
상품 가격
상품 총 용량
상품 단위
메뉴 사용량
메뉴 사용 단위
```

Modeling은 해당 정보를 기준 단위로 변환한 후 실제 사용량만큼의 재료비를 계산합니다.

<br>

## 10. 예상 메뉴 비용 계산

메뉴 예상 비용은 각 재료 사용량과 최저가 상품 정보를 이용해 계산합니다.

관련 함수:

```python
calculate_ingredient_cost(...)
calculate_menu_estimated_cost(...)
```

### 계산 흐름

```text
재료 사용량 확인
→ 사용 단위 정규화
→ 상품 용량 및 단위 확인
→ 기준 단위 변환
→ 사용량 비율 계산
→ 재료별 비용 계산
→ 전체 재료 비용 합산
```

개념적인 계산식:

```text
재료 사용 비용
= 상품 가격
× (메뉴 사용량 ÷ 상품 총 용량)
```

### 계산 실패 처리

다음 상황에서는 재료 비용 계산이 실패하거나 제외될 수 있습니다.

- 사용량 누락
- 지원하지 않는 단위
- 상품 가격 누락
- 상품 용량 누락
- 식품이 아닌 상품과 잘못 매칭
- 비정상적으로 높은 가격
- 계산 비용과 RAG 예상 비용의 과도한 차이

### RAG 예상 비용 Fallback

재료별 비용 계산이 불가능하거나 계산값이 비정상적인 경우 RAG가 제공한 `estimated_cost`를 Fallback으로 사용할 수 있습니다.

대표 상태:

```text
fallback_to_rag_estimated_cost
fallback_to_rag_estimated_cost_by_cost_gap
```

### 기본 재료 처리

물과 일부 기본 재료는 일반 상품과 동일한 방식으로 비용을 계산하면 예상 가격이 과도하게 커질 수 있습니다.

Mapper는 재료명과 단위를 정규화하고, 물과 비식품 상품 및 가격 이상치를 별도로 판별합니다.

<br>

## 11. 조리 난이도 계산

RAG 메뉴의 조리 난이도는 레시피 정보에서 계산합니다.

관련 함수:

```python
calculate_difficulty_from_recipe(
    candidate_menu: dict,
) -> dict
```

### 난이도 구성 요소

```text
재료 수
조리 단계 수
조리 시간
추정 사용량 비율
조리 행동 난이도
```

세부 함수:

```python
calculate_ingredient_count()
calculate_recipe_step_count()
calculate_cooking_time()
calculate_estimated_usage_ratio()
calculate_ingredient_count_points()
calculate_step_count_points()
calculate_cooking_time_points()
calculate_estimated_usage_points()
calculate_action_difficulty_points()
convert_points_to_difficulty()
```

### 처리 흐름

```text
Candidate Menu
→ 재료 수 계산
→ 레시피 단계 수 계산
→ 조리시간 확인
→ 복잡한 조리 행동 탐지
→ 구성요소별 점수 계산
→ 총 난이도 점수
→ Modeling 난이도 척도로 변환
```

### 활용 위치

계산된 난이도는 다음 단계에서 사용됩니다.

- `difficulty_score`
- 간편식 스타일 Soft Constraint
- OR-Tools Difficulty Bonus
- 식단 품질 검증
- 평균 조리 난이도 요약

<br>

## 12. 재료군 보정

RAG 후보에 `ingredient_groups`가 없으면 재료명 기반 Alias Map으로 보완합니다.

관련 파일:

```text
modeling/services/rag/ingredient_group_mapper.py
```

### 지원 재료군

```text
육류
해산물류
채소류
식물성 단백질류
계란 및 유제품류
곡류
양념류
```

### 처리 우선순위

```text
1. 기존 ingredient_groups가 존재
   → RAG 값 그대로 사용

2. ingredient_groups가 없음
   → ingredients에서 재료명 추출

3. ingredients가 없음
   → ingredient_usages[].ingredient_name 추출

4. Alias Map으로 재료군 추론
```

### 재료명 정규화

다음 최소 정규화를 수행합니다.

- 앞뒤 공백 제거
- 이름 사이의 공백 제거
- 괄호 이후 보조 설명 제거

예시:

```text
" 닭 가슴살 "
→ "닭가슴살"

"소고기(소고기 대체)"
→ "소고기"
```

관련 함수:

```python
normalize_ingredient_name()
map_ingredient_name_to_group()
infer_ingredient_groups_from_names()
extract_ingredient_names()
fill_missing_ingredient_groups()
```

### 매핑 상태

| 상태 | 의미 |
|---|---|
| `existing_groups_used` | RAG의 기존 재료군 사용 |
| `mapped_from_ingredient_names` | 재료명으로 재료군 보완 |
| `mapping_unavailable` | 보완 가능한 재료군 없음 |

### 진단 정보

```text
total_ingredient_count
mapped_ingredient_count
unknown_ingredient_count
coverage_rate
mapped_ingredients_preview
unknown_ingredients_preview
```

<table style="background-color:#FFF6C7; border-left:6px solid #E6C85C; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>⭐ 명시적 Alias Map</strong><br>
      현재 재료군 추론은 임의의 LLM 추론이 아니라 코드에 정의된 명시적 Alias Dictionary를 사용합니다.
      따라서 결과를 재현할 수 있지만, 사전에 등록되지 않은 재료는 <code>mapping_unavailable</code>로 남을 수 있습니다.
    </td>
  </tr>
</table>

<br>

## 13. RAG 데이터 품질 검사

각 후보 메뉴는 다음 함수로 품질을 검사합니다.

```python
validate_rag_candidate_menu(
    menu: dict,
) -> tuple[bool, list[str]]
```

### 주요 검사 항목

- 메뉴 ID 누락
- 메뉴명 누락 또는 빈 문자열
- 카테고리 누락
- 재료 목록 누락
- 유효하지 않은 재료명
- 재료군 누락
- 재료 사용량 누락
- 영양 정보 누락
- 칼로리 0 또는 누락
- 단백질 0 또는 누락
- 가격 정보 누락
- 레시피 정보 누락
- 영양 수치 이상치
- 총 칼로리와 영양소 환산 열량 불일치

### Hard Exclusion과 Soft Quality Issue

RAG 데이터에 일부 문제가 있다고 해서 모든 후보를 즉시 제거하지 않습니다.

```text
서비스가 사용할 수 없는 핵심 구조 오류
→ 후보 제외 가능

영양·가격·재료군 일부 누락
→ 후보 유지
→ Quality Issue 기록
→ Recommendation에서 패널티 적용
```

이를 통해 지나치게 많은 후보가 제거되어 월간 식단 생성이 실패하는 상황을 줄입니다.

<br>

## 14. 영양 이상치 진단

영양 데이터 이상치는 다음 함수에서 분석합니다.

```python
analyze_nutrition_outlier(
    menu: dict,
) -> dict
```

### 주요 검사

- 과도하게 높은 총 칼로리
- 극단적으로 높은 칼로리
- 탄수화물·단백질·지방 환산 열량과 총 칼로리 불일치
- 특정 영양소 하나의 환산 열량이 총 칼로리를 초과
- 극단적인 영양소 수치

### 영양소 환산 열량

```text
탄수화물 열량 = carbohydrate × 4
단백질 열량   = protein × 4
지방 열량     = fat × 9

macro_calories
= 탄수화물 열량
+ 단백질 열량
+ 지방 열량
```

이 값과 RAG가 제공한 총 `calories`를 비교합니다.

대표 Issue:

```text
calories_too_high
calories_extreme
nutrient_calorie_mismatch
nutrient_calorie_extreme_mismatch
carbohydrate_calories_exceed_total
protein_calories_exceed_total
fat_calories_exceed_total
```

영양 이상치는 후보 데이터의 신뢰도를 평가하고 Quality Penalty를 계산하는 근거로 사용됩니다.

<br>

## 15. RAG Quality Score

후보별 품질 이슈는 정해진 감점값을 이용해 RAG 데이터 품질 점수로 변환됩니다.

관련 함수:

```python
calculate_rag_data_quality_score(
    issues: list[str],
) -> int
```

개념적인 구조:

```text
기본 품질 점수
- Issue별 감점
= RAG Data Quality Score
```

매핑된 후보에는 다음 필드가 추가됩니다.

```text
rag_data_quality_score
rag_data_quality_issues
```

예시:

```json
{
  "rag_data_quality_score": 80,
  "rag_data_quality_issues": [
    "calories_zero_or_missing"
  ]
}
```

이 품질 점수는 Recommendation의 최종 점수 계산에서 Quality Penalty로 반영됩니다.

```text
final_score
= base_final_score
+ style_soft_constraint_score
- total_quality_penalty
```

<br>

## 16. Mapping Diagnostics

RAG Mapper는 개별 후보뿐 아니라 전체 매핑 결과에 대한 집계 정보도 기록합니다.

관련 함수:

```python
clear_rag_mapping_diagnostics()
record_rag_mapping_diagnostics()
get_rag_mapping_diagnostics()
merge_counter_dicts()
merge_quality_issue_examples()
```

### 집계 지표

```text
raw_menus
mapped_menus
excluded_menus
quality_issue_menus
quality_issue_type_count
quality_issue_examples
quality_issue_rate
ingredient_group_mapping_status_count
```

### 품질 이슈 비율

```text
quality_issue_rate
= quality_issue_menus
÷ mapped_menus
```

### 예시 제한

각 품질 이슈별 예시는 무제한으로 저장하지 않고 일부 Preview만 유지합니다.

이를 통해 다음 문제를 방지합니다.

- 대용량 로그 생성
- 사용자·메뉴 데이터 과다 노출
- 실험 결과 파일 크기 증가
- 진단 정보의 가독성 저하

로그 예시:

```text
[RAG Mapper]
raw_menus=3276
mapped_menus=3276
excluded_menus=0
quality_issue_menus=12
```

<br>

## 17. 후보 풀 진단

월간 식단 생성 전 후보 수가 Optimizer를 실행하기에 충분한지 진단합니다.

관련 파일:

```text
modeling/services/rag/rag_candidate_diagnostics.py
```

관련 함수:

```python
diagnose_monthly_candidate_pool(
    candidate_menus: list[dict],
    profile: dict,
    optimizer_candidate_limit: int,
) -> dict
```

### 진단 항목

```text
candidate_count
unique_menu_count
required_meal_count
optimizer_candidate_limit
shortage_reasons
recommended_action
additional_candidate_count
```

### 주요 부족 사유

```text
candidate_empty
below_optimizer_candidate_limit
unique_menu_shortage
```

### 필요한 전체 끼니 수

```text
required_meal_count
= period_days × meal_count_per_day
```

### Optimizer 후보 기준

Modeling Service에서는 보통 다음 값을 기준으로 후보 풀을 진단합니다.

```text
optimizer_candidate_limit
≈ required_meal_count × 1.2
```

후보 수가 많더라도 동일 메뉴가 반복되어 있다면 `unique_menu_count`가 부족할 수 있습니다.

<br>

## 18. 후보 부족 및 Fallback

초기 RAG 요청에서 후보가 없거나 부족하면 조건을 단계적으로 완화해 다시 요청합니다.

Fallback은 식단 스타일 후보와 월간 식단 후보에서 다르게 구성됩니다.

### 식단 스타일 Fallback

대표적인 순서:

```text
기본 조건 요청
→ 선호 카테고리 완화
→ 선호 재료 조건 완화
→ 카테고리와 재료 조건 동시 완화
```

### 월간 식단 Fallback

대표적인 순서:

```text
기본 요청
→ candidate_count 확대
→ 선호 카테고리 완화
→ 선호 재료군 확장
→ 복수 목표를 대표 목표로 완화
→ 복합 완화 조건 적용
```

### 완화하지 않는 조건

알레르기 재료는 안전 조건이므로 Fallback에서도 제거하거나 완화하지 않습니다.

```text
allergy_ingredients
→ 항상 유지
```

### Fallback 결과 정보

```json
{
  "fallback_used": true,
  "fallback_steps": [
    {
      "reason": "candidate_count_expanded",
      "candidate_count": 400,
      "result_count": 350
    }
  ],
  "final_candidate_count": 350,
  "candidate_diagnostics": {},
  "warnings": []
}
```

<table style="background-color:#FFF1E6; border-left:6px solid #E67E22; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>⚠️ 안전 조건 우선</strong><br>
      선호도나 목표는 후보 부족 상황에서 일부 완화할 수 있지만,
      알레르기 정보는 사용자 안전과 직접 관련되므로 Fallback 과정에서도 유지합니다.
    </td>
  </tr>
</table>

<br>

## 19. 추가 후보 병합

초기 Optimizer 실행이 실패하고 후보 부족이 원인일 가능성이 있으면 RAG에 추가 후보를 요청할 수 있습니다.

관련 함수:

```python
calculate_additional_candidate_count()
merge_candidate_menus()
```

### 추가 요청 수 계산

```text
Optimizer 후보 기준
- 현재 후보 수
= 기본 부족 수
```

부족 수와 최소 추가 요청 기준을 함께 고려해 추가 요청 개수를 결정합니다.

### 후보 병합

```text
기존 후보
+ 추가 RAG 후보
→ 메뉴 고유 식별자 기준 중복 제거
→ 병합 후보 목록
```

메뉴 식별에는 다음 함수가 사용됩니다.

```python
get_menu_identity(menu: dict) -> str
```

동일 메뉴 ID 또는 동일한 식별값을 가진 후보는 중복으로 추가하지 않습니다.

### 재실행 흐름

```text
초기 Optimizer 실패
→ 후보 풀 진단
→ 추가 RAG 후보 요청
→ 기존·추가 후보 병합
→ Recommendation 재계산
→ Optimizer Input 재생성
→ OR-Tools 재실행
```

<br>

## 20. Modeling Service 연동

RAG 모듈은 다음 서비스 흐름에서 사용됩니다.

관련 파일:

```text
modeling/services/modeling_service.py
```

### 식단 스타일 후보 생성

```text
create_meal_style_candidates()
→ Profile 생성
→ Style용 candidate_count 계산
→ RAG 요청 및 Fallback
→ 후보 메뉴 매핑
→ 식단 스타일 후보 생성
```

### 월간 식단 생성

```text
create_monthly_plan()
→ Profile 생성
→ 월간 candidate_count 계산
→ RAG 요청 및 Fallback
→ 후보 풀 진단
→ Recommendation 점수 계산
→ Optimizer 실행
→ 필요 시 추가 RAG 요청
→ 후보 병합 및 Optimizer 재실행
```

### 빈 후보 응답

Fallback을 모두 수행한 뒤에도 후보가 없으면 구조화된 실패 응답을 반환합니다.

```text
failure_reason = candidate_empty
```

후보 수는 존재하지만 월간 식단 구성에 충분하지 않으면 다음 실패 응답을 반환할 수 있습니다.

```text
failure_reason = candidate_insufficient
```

<br>

## 21. 실행 및 검증

프로젝트 루트에서 실행합니다.

### RAG 요청 Payload 확인

```bash
PYTHONPATH=modeling \
python - <<'PY'
from services.rag.rag_request_service import build_rag_request

profile = {
    "goals": ["다이어트", "간편식"],
    "meal_budget": 3333,
    "preferred_categories": ["한식"],
    "ingredient_preferences": ["육류", "채소류"],
    "allergy_ingredients": ["새우"],
}

payload = build_rag_request(
    user_id=4,
    profile=profile,
    candidate_count=30,
)

print(payload)
PY
```

### 후보 수 계산 확인

```bash
PYTHONPATH=modeling \
python - <<'PY'
from services.rag.rag_request_service import calculate_candidate_count

candidate_count = calculate_candidate_count(
    meal_count_per_day=3,
    period_days=7,
    buffer_multiplier=3,
)

print("candidate_count:", candidate_count)
PY
```

예상 결과:

```text
candidate_count: 63
```

### 재료군 매핑 확인

```bash
PYTHONPATH=modeling \
python - <<'PY'
from services.rag.ingredient_group_mapper import (
    infer_ingredient_groups_from_names,
)

groups, diagnostics = infer_ingredient_groups_from_names(
    [
        "닭가슴살",
        "양파",
        "현미",
        "알 수 없는 재료",
    ]
)

print("groups:", groups)
print("diagnostics:", diagnostics)
PY
```

예상 재료군:

```text
육류
채소류
곡류
```

### 샘플 RAG 응답 매핑

```bash
PYTHONPATH=modeling \
python - <<'PY'
import json

from services.rag.rag_response_mapper import (
    clear_rag_mapping_diagnostics,
    get_rag_mapping_diagnostics,
    map_rag_response_to_candidate_menus,
)

with open(
    "modeling/data/sample_rag_response_200.json",
    "r",
    encoding="utf-8",
) as file:
    rag_response = json.load(file)

clear_rag_mapping_diagnostics()

candidate_menus = map_rag_response_to_candidate_menus(
    rag_response=rag_response,
)

print("candidate_count:", len(candidate_menus))
print("diagnostics:", get_rag_mapping_diagnostics())
PY
```

### 문법 검사

```bash
python -m py_compile \
  modeling/services/rag/rag_client.py \
  modeling/services/rag/rag_request_service.py \
  modeling/services/rag/rag_response_mapper.py \
  modeling/services/rag/rag_candidate_diagnostics.py \
  modeling/services/rag/ingredient_group_mapper.py
```

### RAG 오류 상태 테스트

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest \
  modeling/tests/api/test_modeling_api_rag_error_status.py \
  -q
```

### 전체 Modeling 테스트

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest modeling/tests -q
```

<br>

## 22. 파일 구조

```text
modeling/
├── services/
│   └── rag/
│       ├── __init__.py
│       ├── rag_client.py
│       ├── rag_request_service.py
│       ├── rag_response_mapper.py
│       ├── rag_candidate_diagnostics.py
│       ├── ingredient_group_mapper.py
│       └── README.md
│
├── data/
│   └── sample_rag_response_200.json
│
├── tests/
│   └── api/
│       └── test_modeling_api_rag_error_status.py
│
└── experiments/
    └── docs/
        └── rag_diagnostics.md
```

### 파일별 역할

| 파일 | 역할 |
|---|---|
| `rag_client.py` | 외부 RAG API 호출과 오류 변환 |
| `rag_request_service.py` | Profile 기반 요청 Payload와 후보 수 생성 |
| `rag_response_mapper.py` | 메뉴·가격·난이도·품질 정보 매핑 |
| `rag_candidate_diagnostics.py` | 후보 수, 고유 메뉴 수 및 부족 상태 진단 |
| `ingredient_group_mapper.py` | 재료명 기반 재료군 보정 |
| `sample_rag_response_200.json` | RAG 응답 Mapping 검증용 샘플 |
| `rag_diagnostics.md` | RAG 품질과 후보 풀 상세 진단 문서 |

<br>

## 23. 현재 구현상 주의사항

### 재료군 Alias Map은 완전하지 않음

명시적으로 등록된 재료만 재료군으로 변환됩니다.

```text
등록된 재료
→ 재료군 매핑

등록되지 않은 재료
→ unknown_ingredients
→ mapping_unavailable 가능
```

새로운 RAG 재료명이 지속적으로 추가되면 Alias Map도 함께 관리해야 합니다.

### 재료명 정규화는 최소 수준

현재 정규화는 공백과 괄호 설명을 중심으로 수행합니다.

다음과 같은 차이는 자동으로 통합되지 않을 수 있습니다.

```text
브랜드명 포함
다른 띄어쓰기 변형
단수·복수 표현
영문·한글 혼용
오탈자
수식어가 앞에 붙은 재료명
```

### 일부 품질 이슈가 있어도 후보 유지

영양 정보나 재료군이 일부 부족한 후보는 즉시 제거되지 않을 수 있습니다.

이는 후보 부족 방지를 위한 정책이며, 품질 이슈는 다음 단계에서 감점됩니다.

```text
RAG Mapper
→ rag_data_quality_score

Recommendation
→ total_quality_penalty
```

### RAG 예상 비용은 Fallback 값

재료 사용량 기반 계산이 실패하면 RAG의 `estimated_cost`가 사용될 수 있습니다.

따라서 메뉴 비용의 출처는 후보별로 다를 수 있으며 `pricing_status`와 비용 상세 진단을 함께 확인해야 합니다.

### 비용 계산 단위 변환 제한

지원하지 않는 단위나 불완전한 상품 정보는 정확한 비용 계산을 어렵게 할 수 있습니다.

새로운 단위가 도입되면 `normalize_unit()`과 `convert_usage_to_base_unit()` 정책을 검토해야 합니다.

### 영양 이상치는 실제 오류와 특수 메뉴를 모두 포함할 수 있음

높은 칼로리나 특정 영양소 수치가 항상 잘못된 데이터라는 의미는 아닙니다.

대용량 메뉴나 다인분 레시피일 수도 있으므로, 이상치 결과는 하드 제거보다 품질 감점과 진단 목적으로 활용합니다.

### 후보 수와 고유 메뉴 수는 다름

RAG 후보가 300개여도 동일 메뉴가 여러 번 포함되면 실제 Optimizer가 사용할 수 있는 고유 메뉴 수는 더 적습니다.

```text
candidate_count
≠ unique_menu_count
```

후보 풀 진단에서는 두 값을 모두 확인해야 합니다.

### 알레르기 조건은 Fallback에서도 유지

선호 카테고리, 선호 재료군과 목표는 후보 부족 시 완화될 수 있지만 알레르기 조건은 유지됩니다.

### 추가 RAG 요청은 항상 성공을 보장하지 않음

추가 후보 요청을 수행해도 다음 상황에서는 새로운 고유 후보가 늘어나지 않을 수 있습니다.

- RAG 원본 후보 풀이 제한적
- 동일 조건에서 동일 메뉴 반복
- 알레르기 조건으로 검색 범위가 좁음
- 예산 조건이 지나치게 낮음
- 선호 조건이 복합적으로 제한적

### Mapping Diagnostics는 프로세스 메모리 기반

Mapping Diagnostics는 Mapper 호출 중 수집되는 진단 정보입니다.

다중 프로세스 또는 여러 서버 인스턴스에서는 각 프로세스의 진단 상태가 독립적일 수 있으므로, 운영 집계는 Prometheus나 외부 로그·분석 시스템을 사용하는 것이 적절합니다.

### 전체 응답 로그 금지

RAG 응답에는 메뉴, 레시피, 재료, 상품 및 가격 정보가 대량으로 포함될 수 있습니다.

운영 로그에는 전체 JSON 대신 다음 요약만 기록하는 것이 좋습니다.

```text
raw_menu_count
mapped_menu_count
excluded_menu_count
quality_issue_menu_count
quality_issue_rate
candidate_request_count
fallback_used
fallback_reason
elapsed_ms
```

<table style="background-color:#FFF6C7; border-left:6px solid #E6C85C; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>⭐ 설계 요약</strong><br>
      RAG 연동 모듈은 외부 후보 메뉴를 그대로 신뢰하지 않고,
      메뉴 비용·조리 난이도·재료군·영양 품질을 재계산하고 진단합니다.
      후보가 부족한 경우에는 사용자 안전 조건을 유지하면서 검색 조건을 단계적으로 완화하고,
      추가 후보를 병합하여 Recommendation과 Optimizer가 안정적으로 동작할 수 있는 후보 풀을 제공합니다.
    </td>
  </tr>
</table>

<br>

## 24. 관련 문서

RAG Mapping 과정의 데이터 품질 진단, 집계 결과와 관측 기준은 아래 문서에서 확인할 수 있습니다.

### Repository 문서

- [`experiments/docs/rag_diagnostics.md`](../../experiments/docs/rag_diagnostics.md)  
  RAG 후보 풀, Mapping 결과 및 데이터 품질 진단 결과

### Notion 문서

- [📊 RAG Mapping Diagnostics 및 데이터 품질 관측](https://app.notion.com/p/RAG-Mapping-Diagnostics-3829e3e335cc801aa90fddfd86300dea?source=copy_link)  
  진단 항목 설계, 품질 이슈 집계 구조 및 관측 방법
