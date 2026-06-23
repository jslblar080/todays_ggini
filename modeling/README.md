# 🧠 오늘의 끼니 — AI Modeling

<p align="center">
  <img src="../assets/images/modeling-logic.png" width="1100" alt="오늘의 끼니 모델링 추천 및 최적화 흐름" />
</p>

<h3 align="center">사용자 조건 기반 개인화 추천·월간 식단 최적화 엔진</h3>

<p align="center">
  사용자 입력을 추천 조건으로 변환하고,<br>
  RAG 후보 메뉴 평가부터 재랭킹, 월간 식단 최적화, 대체 메뉴 생성 및 품질 검증까지 수행합니다.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Language-Python_3.11-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/API-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Optimizer-OR--Tools-4285F4?style=flat-square" />
  <img src="https://img.shields.io/badge/Re--ranking-MMR-7C3AED?style=flat-square" />
  <img src="https://img.shields.io/badge/Deploy-Docker-2496ED?style=flat-square&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/Monitoring-Prometheus_&_Grafana-E6522C?style=flat-square" />
</p>

<br>

## 목차

1. [Modeling 파트 소개](#1-modeling-파트-소개)
2. [전체 처리 흐름](#2-전체-처리-흐름)
3. [주요 기능](#3-주요-기능)
4. [RAG 후보 요청과 데이터 품질 처리](#4-rag-후보-요청과-데이터-품질-처리)
5. [후보 메뉴 점수 계산](#5-후보-메뉴-점수-계산)
6. [MMR 기반 재랭킹](#6-mmr-기반-재랭킹)
7. [OR-Tools 월간 식단 최적화](#7-or-tools-월간-식단-최적화)
8. [대체 메뉴 생성](#8-대체-메뉴-생성)
9. [식단 품질 검증](#9-식단-품질-검증)
10. [Modeling API](#10-modeling-api)
11. [프로젝트 구조](#11-프로젝트-구조)
12. [로컬 실행 방법](#12-로컬-실행-방법)
13. [실행 환경 및 Optimizer 설정](#13-실행-환경-및-optimizer-설정)
14. [테스트 및 계약 검증](#14-테스트-및-계약-검증)
15. [실험 및 자동 튜닝](#15-실험-및-자동-튜닝)
16. [배포 구조](#16-배포-구조)
17. [모니터링](#17-모니터링)
18. [상세 문서](#18-상세-문서)
19. [Modeling 담당 범위](#19-modeling-담당-범위)

<br>

## 1. Modeling 파트 소개

오늘의 끼니 Modeling은 Backend와 RAG 사이에서 동작하는 개인화 추천·최적화 엔진입니다.

1차 페르소나 생성 단계에서는 가구 형태, 가구원 신체 정보, 활동량, 식단 목적을 바탕으로 사용자 페르소나와 권장 하루 칼로리를 생성합니다.

이후 식단 추천 단계에서는 Backend로부터 전달받은 예산, 식사 횟수, 식단 목표, 조리 수준, 선호도, 알레르기 등의 조건을 추천 프로필로 변환합니다. RAG가 제공한 후보 메뉴를 평가한 뒤 재랭킹과 OR-Tools 최적화를 수행하여 월간 식단과 대체 메뉴를 구성합니다.

```text
Backend 사용자 요청
→ 사용자·가구 프로필 생성
→ 권장 하루 칼로리 및 추천 가중치 생성
→ RAG 후보 메뉴 요청
→ 후보 데이터 매핑 및 품질 진단
→ 후보 메뉴 점수 계산
→ 점수 기반 정렬
→ MMR 다양성 재랭킹
→ OR-Tools 월간 식단 최적화
→ 월간 식단 및 대체 메뉴 매핑
→ 식단 요약 및 품질 검증
→ Backend 응답
```

<table style="background-color:#EAF4FF; border-left:6px solid #4D96D9; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>💡 Modeling 핵심 역할</strong><br>
      단순히 점수가 높은 메뉴를 순서대로 선택하는 것이 아니라,
      사용자 조건과 월 전체 식단의 예산·영양·조리 난이도·반복 정도를 함께 고려해
      식단 조합을 최적화합니다.
    </td>
  </tr>
</table>

<br>

## 2. 전체 처리 흐름

```text
Persona Profile Build Input
  ├── 가구 형태
  ├── 가구원 신체 정보
  ├── 활동량
  └── 식단 목적
          ↓
Persona & Recommended Calorie Builder
  ├── BMR 계산
  ├── 활동량 기반 TDEE 계산
  ├── 식단 목적별 열량 보정
  └── 권장 하루 칼로리 및 페르소나 후보 생성
          ↓
User Profile Input
  ├── 식단 목표
  ├── 예산 및 식사 횟수
  ├── 조리 수준
  ├── 선호 음식·재료
  ├── 알레르기
  └── 다양성 수준
          ↓
Profile Builder
  ├── 한 끼 기준 예산 계산
  ├── 끼니별 목표 칼로리 계산
  ├── 목표별 추천 가중치 생성
  └── 필터 및 제약조건 생성
          ↓
RAG Candidate Request & Fallback
          ↓
RAG Response Mapping & Diagnostics
          ↓
Weighted Scoring
  ├── 예산 적합도
  ├── 영양·칼로리 적합도
  ├── 선호도
  ├── 조리 난이도
  └── 다양성
          ↓
Style Soft Constraint & Quality Penalty
          ↓
Score-based Re-ranking
          ↓
MMR Re-ranking
          ↓
Optimizer Input Builder
          ↓
OR-Tools CP-SAT Monthly Plan Optimizer
          ↓
Monthly Plan & Alternative Menu Mapping
          ↓
Plan Summary
          ↓
Style / Quality Validation
          ↓
Backend Response Mapper
```

| 단계 | 주요 처리 |
|---|---|
| Persona Profile Input | 가구 형태, 가구원 신체 정보, 활동량, 식단 목적 입력 |
| Persona Builder | 페르소나 후보와 사용자·가구 기준 권장 하루 칼로리 생성 |
| User Profile Input | 예산, 식사 횟수, 목표, 조리 수준, 선호도, 알레르기 입력 |
| Profile Builder | 끼니별 예산·칼로리, 추천 가중치 및 제약조건 생성 |
| RAG Request | 사용자 조건에 적합한 메뉴 후보 요청 및 후보 부족 대응 |
| Response Mapper | RAG 응답을 Modeling 내부 메뉴 구조로 변환 |
| Diagnostics | 누락된 영양·재료·난이도·가격 데이터 검사 |
| Weighted Scoring | 예산, 영양·칼로리, 선호도, 난이도, 다양성 평가 |
| Soft Constraint | 선택한 식단 스타일을 추가 점수 보정 방식으로 반영 |
| Quality Penalty | RAG 데이터 품질 문제를 감점으로 반영 |
| Score-based Re-ranking | `final_score`를 기준으로 후보 메뉴 우선 정렬 |
| MMR Re-ranking | 추천 점수와 메뉴 유사도를 함께 고려해 다양성 중심 재정렬 |
| Optimizer | OR-Tools를 사용한 월 전체 식단 조합 최적화 |
| Plan Mapping | 선택 메뉴와 대체 메뉴를 월간 식단 응답 구조로 변환 |
| Summary | 비용·칼로리·영양·반복 정도 등 결과 요약 |
| Validator | 예산, 영양, 난이도, 중복 및 스타일 적합성 검증 |
| Response Mapper | 월간 식단, 대체 메뉴, 요약, 경고 및 검증 결과 반환 |

<br>

## 3. 주요 기능

### 👤 사용자 프로필 생성

사용자 입력을 추천 점수 계산과 월간 식단 최적화에 사용할 수 있는 구조로 변환합니다.

#### 1차 페르소나 생성 입력

- 사용자 ID
- 가구 형태 및 가구원 수
- 가구원별 성별, 나이, 키, 체중
- 월 식비 예산
- 하루 식사 횟수
- 식단 목적
- 활동량

#### 식단 추천 입력

- 사용자 ID
- 식단 목표
- 월 식비 예산
- 하루 식사 횟수
- 권장 하루 칼로리
- 요리 실력
- 선호 음식 카테고리
- 선호 재료군
- 알레르기 및 제외 재료
- 원하는 식단 다양성
- 식단 생성 기간

#### 주요 변환 결과

- 사용자·가구 기준 권장 하루 칼로리
- 끼니별 목표 칼로리
- 한 끼 기준 예산
- 식단 목표별 추천 가중치
- 조리 난이도 기준
- 선호 재료 및 카테고리 조건
- 알레르기 재료 필터
- 다양성 및 반복 제어 정책
- RAG 후보 요청 조건
- 월간 식단 최적화 입력 프로필

```text
가구원 신체 정보
→ BMR 계산
→ 활동량 기반 TDEE 계산
→ 식단 목적별 열량 보정
→ 권장 하루 칼로리 생성

권장 하루 칼로리
÷ 하루 식사 횟수
→ 끼니별 목표 칼로리 생성

월 예산
÷ 식단 기간의 전체 끼니 수
→ 한 끼 기준 예산 계산
```

권장 칼로리와 끼니별 목표 칼로리는 후보 메뉴의 `nutrition_score` 계산과 최종 식단 요약·스타일 검증에 활용됩니다.

관련 모듈:

```text
services/persona/
├── persona_service.py
└── persona_catalog.py

services/profile/
├── profile_service.py
├── user_input_service.py
└── weight_service.py
```

### 🔥 권장 칼로리 생성

가구원별 성별, 나이, 키, 체중을 사용해 기초대사량을 계산하고, 활동량 계수를 반영해 TDEE를 계산합니다.

이후 사용자의 식단 목적에 따라 열량을 보정하여 가구원별 권장 하루 칼로리를 생성합니다.

```text
가구원 신체 정보
→ BMR
→ 활동량 계수 적용
→ TDEE
→ 식단 목적별 보정
→ 가구원별 권장 칼로리
→ 사용자·가구 기준 권장 하루 칼로리
```

생성된 권장 칼로리는 식단 추천 요청의 `recommended_daily_calories`로 전달되며, `Profile Builder`에서 하루 식사 횟수로 나누어 `meal_calorie_target`을 생성합니다.

### 🧑‍🤝‍🧑 페르소나 후보 생성

사용자의 가구 형태, 예산, 식단 목적, 활동량과 가구원 정보를 기반으로 가능한 페르소나 조합을 구성합니다.

사용자 조건과 페르소나 카탈로그의 다음 항목을 비교하여 후보를 우선순위에 따라 반환합니다.

- 가구 형태
- 식사당 예산 구간
- 식단 목적
- 활동량
- 가구원 구성

관련 모듈:

```text
services/persona/
├── persona_catalog.py
└── persona_service.py
```

### 🥗 식단 스타일 후보 생성

사용자 프로필과 목적별 가중치를 바탕으로 여러 식단 스타일 후보를 제공합니다.

각 스타일 후보는 다음 정보를 포함할 수 있습니다.

- 스타일 ID 및 이름
- 사용자 식단 목표
- 주요 추천 기준
- 3일치 샘플 식단
- 예산·영양·선호도·난이도·다양성 특성

관련 모듈:

```text
services/style/
├── meal_style_service.py
└── style_selection_service.py
```

<br>

## 4. RAG 후보 요청과 데이터 품질 처리

Modeling은 RAG API에 사용자 조건과 필요한 후보 수를 전달하고, 반환된 메뉴·재료·영양·가격 데이터를 추천 가능한 내부 구조로 변환합니다.

```text
사용자 프로필
→ RAG 요청 Payload 생성
→ 후보 메뉴 응답
→ 필드 매핑
→ 재료군 보정
→ 품질 진단
→ 추천 후보 생성
```

### 주요 처리

- 후보 메뉴 요청 Payload 생성
- RAG 네트워크 오류 및 HTTP 상태 코드 변환
- 메뉴·재료·영양·가격 필드 매핑
- 재료군 정보 보정
- 누락 필드와 비정상 값 진단
- 후보 부족 시 추가 요청 또는 완화 정책 적용
- RAG 품질 이슈를 추천 점수의 패널티로 반영
- 영양 성분과 총열량 사이의 불일치 진단

### 주요 품질 진단 예시

- 칼로리 누락 또는 0
- 단백질 등 영양 정보 누락
- 비정상적으로 높은 칼로리
- 총열량과 탄수화물·단백질·지방 환산 열량 간 불일치
- 재료 목록 누락
- 재료군 매핑 실패
- 가격 또는 난이도 정보 부족

관련 모듈:

```text
services/rag/
├── rag_client.py
├── rag_request_service.py
├── rag_response_mapper.py
├── rag_candidate_diagnostics.py
└── ingredient_group_mapper.py
```

<table style="background-color:#FFF1E6; border-left:6px solid #E67E22; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>⚠️ 데이터 품질 처리</strong><br>
      영양 정보나 재료군 정보가 일부 누락됐다는 이유만으로 모든 후보를 즉시 제거하지 않습니다.
      반드시 제외해야 하는 조건과 점수 감점으로 보정할 조건을 분리하여,
      후보 부족 문제를 완화하면서 추천 품질을 관리합니다.
    </td>
  </tr>
</table>

<br>

## 5. 후보 메뉴 점수 계산

각 후보 메뉴는 사용자 프로필, 끼니별 목표 칼로리, 한 끼 예산과 선택한 식단 스타일을 기준으로 평가합니다.

| 점수·보정 항목 | 설명 |
|---|---|
| `budget_score` | 한 끼 예산 대비 메뉴 비용 적합도 |
| `nutrition_score` | 목표 칼로리와 단백질·탄수화물·지방 등 영양 조건에 대한 적합도 |
| `preference_score` | 선호 음식 카테고리와 재료군의 일치 정도 |
| `difficulty_score` | 사용자의 요리 실력 대비 조리 난이도 적합도 |
| `diversity_score` | 기존 선택 메뉴와의 반복 및 유사도 완화 정도 |
| `style_soft_constraint_score` | 선택한 식단 스타일에 따른 추가 점수 보정 |
| `total_quality_penalty` | RAG 데이터 품질 문제에 대한 총 감점 |

### 칼로리 반영 방식

사용자별 하루 권장 칼로리를 식사 횟수에 맞춰 끼니별 목표로 변환하고, 후보 메뉴의 칼로리가 해당 범위에 얼마나 적합한지를 `nutrition_score`에 반영합니다.

```text
권장 하루 칼로리
÷ 하루 식사 횟수
→ 끼니별 목표 칼로리

끼니별 목표 칼로리
↔ 후보 메뉴 칼로리 비교
→ 다이어트·고단백·영양 균형 점수 계산
→ nutrition_score 반영
```

식단 목표별 칼로리 반영 방식은 다르게 적용됩니다.

- 다이어트: 목표 칼로리와 지방 함량 중심
- 고단백: 단백질 함량을 우선하되 과도한 열량은 감점
- 영양 균형: 칼로리 범위와 탄수화물·단백질·지방 비율을 함께 평가

### 최종 점수 구조

```text
final_score
= base_final_score
+ style_soft_constraint_score
- total_quality_penalty
```

`base_final_score`는 다음 항목의 가중합으로 구성됩니다.

```text
budget_score × budget_weight
+ nutrition_score × nutrition_weight
+ preference_score × preference_weight
+ difficulty_score × difficulty_weight
+ diversity_score × diversity_weight
```

### Weighted Scoring

사용자의 식단 목표에 따라 각 점수의 중요도를 다르게 적용합니다.

예시:

- 식비 절약: 예산 적합도 비중 강화
- 영양 균형: 칼로리와 주요 영양소 비율 강화
- 다이어트: 칼로리와 지방 적합도 강화
- 고단백: 단백질 적합도 강화
- 간편식: 조리 난이도 비중 강화
- 맛 중심: 선호도 비중 강화

관련 모듈:

```text
services/recommendation/
├── recommendation_service.py
└── scoring_service.py
```

<br>

## 6. MMR 기반 재랭킹

후보 메뉴의 개별 점수만 사용하면 비슷한 메뉴가 상위에 반복될 수 있습니다.

Modeling은 먼저 `final_score`를 기준으로 후보 메뉴를 정렬하고, 이후 MMR을 적용하여 추천 적합도와 메뉴 간 차이를 함께 고려합니다.

```text
final_score 계산
→ final_score 기준 1차 정렬
→ 메뉴 간 유사도 계산
→ MMR 점수 계산
→ MMR 기준 2차 재랭킹
```

MMR 적용 목적:

- 동일 메뉴 반복 완화
- 유사한 재료와 조리법의 과도한 반복 방지
- 월간 식단의 메뉴 다양성 확보
- 대체 메뉴 후보 간 유사도 완화
- 사용자가 설정한 다양성 수준 반영

```text
MMR Score
= 추천 관련성
- 기존 선택 메뉴와의 유사성 패널티
```

다양성 수준이 낮으면 기존 추천 점수를 더 중요하게 보고, 다양성 수준이 높으면 메뉴 간 차이를 더 크게 반영합니다.

관련 모듈:

```text
services/plan/
├── mmr_service.py
├── menu_similarity_service.py
├── menu_diversity_service.py
└── diversity_service.py
```

<br>

## 7. OR-Tools 월간 식단 최적화

월간 식단은 OR-Tools CP-SAT Solver를 사용하여 구성합니다.

단순히 점수가 높은 메뉴를 순서대로 선택하는 방식이 아니라, 전체 식단 기간을 하나의 최적화 문제로 정의합니다.

### 주요 목적

- 필요한 전체 끼니 수 충족
- 사용자 월 예산 범위 반영
- 반복 메뉴 최소화
- 추천 점수가 높은 메뉴 우선 선택
- 단백질 식품 및 영양 조건 보정
- 식단 스타일과 조리 난이도 반영
- 후보 메뉴 부족 상황 대응
- 실행 시간과 결과 품질 간 균형 유지
- 후보 메뉴의 칼로리 및 영양 정보를 최적화 입력 데이터에 포함
- 최적화 결과의 칼로리와 영양 상태를 요약 및 Validator 단계에서 확인

### 최적화 처리 흐름

```text
추천 후보 메뉴
→ Optimizer 입력 데이터 생성
→ 후보·예산·반복 정책 구성
→ 의사결정 변수 및 제약조건 생성
→ 목적함수 구성
→ CP-SAT Solver 실행
→ OPTIMAL / FEASIBLE / INFEASIBLE / UNKNOWN 판정
→ 선택 결과 매핑
```

### 주요 Optimizer 입력

- 식단 기간
- 하루 식사 횟수
- 필요한 총 끼니 수
- 월 예산
- 후보 메뉴 목록
- 후보별 최종 추천 점수
- 후보별 예상 비용
- 후보별 영양·칼로리 정보
- 메뉴 최대 반복 횟수
- Solver 실행 제한시간
- 비용·반복·영양·난이도 보정 정책

### 실패 및 완화 정책

Solver가 식단을 구성하지 못하는 경우 즉시 임의 결과를 반환하지 않고, 실패 원인과 후보 상태를 분석합니다.

주요 대응:

- 후보 메뉴 수 부족 여부 확인
- 필요 끼니 대비 후보 비율 확인
- 예산 제약의 타이트함 진단
- 추가 저비용 후보 확보
- 추가 RAG 후보 요청
- 일부 정책 완화 후 Solver 재실행
- 최종 실패 사유와 사용자 안내를 구조화된 응답으로 반환

관련 모듈:

```text
services/optimizer/
├── optimizer_input_builder.py
├── optimizer_metrics_service.py
├── baselines/
│   └── least_cost_baseline.py
└── ortools/
    ├── monthly_plan_optimizer.py
    ├── infeasible_policy.py
    └── result_mapper.py
```

<br>

## 8. 대체 메뉴 생성

OR-Tools가 선택한 기본 메뉴를 유지하면서 각 끼니에 사용할 대체 메뉴 후보를 월간 식단 응답에 함께 구성합니다.

대체 메뉴는 다음 조건을 기준으로 평가합니다.

- 원본 메뉴와의 유사도
- 선택한 식단 스타일 적합도
- 예산 차이
- 영양 조건
- 조리 난이도
- 중복 여부
- 이미 기본 식단에 선택된 메뉴인지 여부

```text
Optimizer 선택 메뉴
→ 사용 가능한 후보 메뉴 조회
→ 선택 메뉴 제외
→ 점수·유사도·중복 조건 확인
→ 대체 메뉴 후보 정렬
→ 월간 식단 응답에 포함
```

최적화에서 선택한 기본 메뉴 자체를 대체 메뉴 생성 과정에서 변경하지 않고, 변경 가능한 후보 목록만 별도로 제공합니다.

관련 모듈:

```text
services/plan/
├── meal_candidate_service.py
├── meal_change_service.py
├── meal_selector_service.py
├── meal_payload_service.py
└── plan_payload_service.py
```

<br>

## 9. 식단 품질 검증

최적화가 성공했더라도 사용자 조건과 선택한 식단 스타일에 적합한 결과인지 별도의 Validator에서 확인합니다.

### 주요 검증 항목

- 필요한 끼니 수 충족 여부
- 전체 기간 식단 커버리지
- 사용자 예산 초과 여부
- 평균 칼로리와 지방 수준
- 평균 단백질 수준
- 탄수화물·단백질·지방 비율
- 메뉴 중복률
- 고유 메뉴 비율
- 조리 난이도 적합성
- 선택한 식단 스타일과 결과의 일치도
- 대체 메뉴 생성 여부
- 후보 메뉴 및 RAG 데이터 품질
- Solver 결과와 Optimizer 입력 상태

### 스타일별 검증 예시

| 스타일 | 주요 검증 기준 |
|---|---|
| 다이어트 | 평균 칼로리와 지방 수준 |
| 고단백 | 평균 단백질 함량 |
| 영양 균형 | 탄수화물·단백질·지방 비율 |
| 식비 절약 | 월 예산 및 평균 비용 |
| 간편식 | 평균 조리 난이도 |
| 다양성 | 메뉴 중복률 및 고유 메뉴 비율 |

### 검증 상태

| 상태 | 의미 |
|---|---|
| `pass` | 주요 기준을 충족한 정상 결과 |
| `warning` | 식단은 생성됐지만 일부 지표 확인 필요 |
| `fail` | 핵심 조건 또는 스타일 기준을 만족하지 못한 결과 |

검증 결과에는 상태뿐 아니라 측정값, 기준값, 경고 메시지와 개선 안내를 함께 포함할 수 있습니다.

관련 모듈:

```text
services/plan/
├── plan_validation_service.py
├── plan_summary_service.py
└── period_plan_service.py
```

<br>

## 10. Modeling API

Modeling은 Backend와 분리된 FastAPI 서버로 실행합니다.

### 주요 Endpoint

| Method | Endpoint | 설명 |
|---|---|---|
| `GET` | `/health` | Modeling 서버 상태 확인 |
| `POST` | `/meal-style-candidates` | 사용자 기반 식단 스타일 후보 생성 |
| `POST` | `/monthly-plan` | 월간 식단 최적화 및 품질 검증 |
| `GET` | `/metrics` | Prometheus 메트릭 제공 |

### 인증

운영 환경에서는 `X-API-Key` 헤더를 사용합니다.

```text
X-API-Key: <MODELING_API_KEY>
```

`ENV=prod` 환경에서는 API Key가 필수이며, Swagger·Redoc·OpenAPI 문서를 외부에 노출하지 않도록 구성합니다.

### 예외 처리

| 상황 | 응답 |
|---|---|
| 요청 스키마 오류 | `422 Unprocessable Entity` |
| API Key 오류 | `401 Unauthorized` |
| RAG 인증 오류 | RAG 상태에 대응하는 HTTP 오류 |
| RAG 요청 실패 | 외부 API 오류에 대응하는 상태 코드 |
| 최적화 불가능 | `optimizer_infeasible` 구조화 응답 |
| Solver 상태 불명확 | `optimizer_unknown` 구조화 응답 |
| 내부 처리 오류 | `500 Internal Server Error` |

API 구현:

```text
api/
├── server.py
└── metrics.py
```

서비스 진입 함수:

```python
create_meal_style_candidates(request_data: dict) -> dict
create_monthly_plan(request_data: dict) -> dict
```

위 함수는 다음 파일에서 관리합니다.

```text
services/modeling_service.py
```

<br>

## 11. 프로젝트 구조

```text
modeling/
├── api/                       # FastAPI 서버 및 Prometheus 메트릭
├── data/                      # 샘플 사용자·메뉴·RAG 데이터
├── deploy/                    # Docker, EC2, Nginx 및 모니터링 설정
│   ├── monitoring/
│   └── scripts/
├── docs/                      # Modeling 관련 문서
├── experiments/               # 실험, 분석, 튜닝 및 검증 도구
│   ├── analysis/
│   ├── contract/
│   ├── docs/
│   ├── fixtures/
│   ├── flows/
│   ├── optimizer/
│   ├── pipelines/
│   ├── results/
│   ├── runners/
│   ├── scenarios/
│   └── tuning/
├── schemas/                   # 사용자 및 페르소나 입력 스키마
├── services/
│   ├── data/
│   ├── optimizer/
│   ├── persona/
│   ├── plan/
│   ├── profile/
│   ├── rag/
│   ├── recommendation/
│   └── style/
├── tests/                     # API, 계약, 최적화 및 페르소나 테스트
└── utils/                     # 공통 계산 유틸리티
```

<br>

## 12. 로컬 실행 방법

프로젝트 루트에서 실행합니다.

### 가상환경 및 의존성 설치

```bash
python3.11 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r modeling/requirements.txt
```

### Modeling API 실행

```bash
ENV=local \
PYTHONPATH=modeling \
RAG_API_URL="https://api.kkini.cloud/api/v1/meal-candidates" \
python -m uvicorn api.server:app \
  --host 0.0.0.0 \
  --port 8001 \
  --reload
```

API 문서:

```text
http://127.0.0.1:8001/docs
```

상태 확인:

```bash
curl -fsS http://127.0.0.1:8001/health
```

### Docker 실행

```bash
MODELING_API_KEY=local-secret-key \
docker compose \
  -f docker-compose.modeling.yml \
  up --build
```

Docker 상태 확인:

```bash
docker compose \
  -f docker-compose.modeling.yml \
  ps

curl -fsS http://127.0.0.1:8001/health
```

<br>

## 13. 실행 환경 및 Optimizer 설정

### 주요 환경변수

| 환경변수 | 설명 |
|---|---|
| `ENV` | 실행 환경 구분 (`local`, `prod`) |
| `MODELING_API_KEY` | 운영 Modeling API 인증 키 |
| `RAG_API_URL` | RAG 후보 메뉴 API 주소 |
| `LOG_LEVEL` | 서버 로그 레벨 |
| `PYTHONPATH` | Modeling 모듈 탐색 경로 |

환경변수의 실제 값과 운영 Secret은 Git에 커밋하지 않습니다.

### 주요 Optimizer 설정

Optimizer 정책은 요청의 `optimizer_config` 또는 내부 기본 설정으로 관리합니다.

| 설정 항목 | 설명 |
|---|---|
| `solver_time_limit_seconds` | Solver 최대 실행시간 |
| `max_repeat_per_menu` | 메뉴별 최대 반복 허용 횟수 |
| `score_weight` | 추천 점수 반영 가중치 |
| `cost_penalty_weight` | 비용 차이에 대한 감점 가중치 |
| `cost_penalty_divisor` | 비용 감점 계산 단위 |
| `repeat_penalty_weight` | 반복 메뉴 감점 가중치 |
| `repeat_penalty_growth` | 반복 횟수에 따른 패널티 증가 방식 |
| `optimizer_candidate_multiplier` | 필요 끼니 대비 Optimizer 후보 배수 |
| `optimizer_candidate_limit` | Optimizer에 전달할 후보 수 제한 |
| `low_cost_candidate_limit` | 추가 저비용 후보 수 제한 |
| `enable_protein_bonus` | 단백질 보정 활성화 여부 |
| `protein_bonus_weight` | 단백질 메뉴 보정 가중치 |
| `protein_bonus_cap_grams` | 단백질 보정 상한 기준 |
| `enable_difficulty_bonus` | 조리 난이도 보정 활성화 여부 |
| `difficulty_bonus_weight` | 조리 난이도 보정 가중치 |
| `enable_nutrition_outlier_penalty` | 영양 이상치 감점 활성화 여부 |
| `nutrition_outlier_penalty_weight` | 영양 이상치 감점 가중치 |
| `enable_optimizer_retry_fallback` | 최적화 실패 시 재시도 정책 활성화 여부 |

Optimizer 설정은 Snapshot, Grid Search, Policy Replay 및 전체 시나리오 회귀 검증을 거쳐 기본 정책에 반영합니다.

<br>

## 14. 테스트 및 계약 검증

### 전체 Modeling 테스트

```bash
ENV=prod \
MODELING_API_KEY=ci-secret-key \
PYTHONPATH=modeling \
python -m pytest modeling/tests -q
```

현재 테스트 영역:

- API 메트릭
- RAG 오류 상태 매핑
- 요청 스키마 검증
- 최적화 실패 응답 계약
- OR-Tools 대체 메뉴
- 페르소나 프로필 생성

### Backend 계약 검증

```bash
python modeling/experiments/contract/run_backend_contract_validation.py
```

개별 실행:

```bash
PYTHONPATH=modeling \
python modeling/experiments/contract/validate_backend_contract_requests.py

python modeling/experiments/contract/validate_backend_contract_responses.py
```

계약 검증에서는 다음 내용을 확인합니다.

- Backend 요청이 Modeling Pydantic Schema와 호환되는지
- 월간 식단 요청에 선택한 스타일 정보가 포함됐는지
- 스타일 후보 응답의 필수 필드가 존재하는지
- 월간 식단 성공·실패 응답 구조가 유효한지
- Modeling 서비스 진입 함수가 호출 가능한지

### Modeling Service Smoke Test

안전 모드:

```bash
python modeling/experiments/contract/run_modeling_service_contract_smoke.py
```

실제 서비스 함수 호출:

```bash
PYTHONPATH=modeling:modeling/experiments/contract \
python modeling/experiments/contract/run_modeling_service_contract_smoke.py \
  --run-service
```

`--run-service` 옵션은 실제 RAG 호출이 발생할 수 있으므로 의도적으로 실행합니다.

### HTTP Smoke Test

```bash
PYTHONPATH=modeling \
python modeling/experiments/contract/run_modeling_api_http_smoke.py \
  --base-url http://127.0.0.1:8001 \
  --api-key local-secret-key \
  --fixture modeling/experiments/fixtures/backend_monthly_plan_request.json
```

<br>

## 15. 실험 및 자동 튜닝

`experiments/`는 운영 서비스 코드와 실험·분석 코드를 분리하기 위한 디렉터리입니다.

### 주요 실험 영역

| 경로 | 설명 |
|---|---|
| `analysis/` | 검증 결과 비교 및 원인 분석 |
| `contract/` | Backend ↔ Modeling 계약 검증 |
| `docs/` | 실험 및 검증 문서 |
| `fixtures/` | 테스트 및 실험 입력 데이터 |
| `flows/` | 전체 추천 흐름 수동 실행 |
| `optimizer/` | Optimizer 결과 비교 |
| `pipelines/` | 통합 검증 파이프라인 |
| `results/` | 대표 실험 및 검증 결과 |
| `runners/` | 개별 실험 실행 진입점 |
| `scenarios/` | 사용자·최적화 검증 시나리오 |
| `tuning/` | 파라미터 탐색과 자동 튜닝 |

### 최종 검증 파이프라인

```bash
PYTHONPATH=modeling \
python modeling/experiments/pipelines/run_final_validation_pipeline.py \
  --help
```

최종 검증에서는 다음 영역을 함께 확인합니다.

- RAG 후보 요청과 응답 매핑
- 후보 메뉴 점수 계산
- Optimizer 실행 상태
- 월간 식단 커버리지
- 반복률과 고유 메뉴 비율
- 예산 및 조리 난이도
- 식단 스타일 검증
- RAG 데이터 품질
- 실행시간 및 프로파일링

### Baseline 비교

MMR Baseline:

```bash
PYTHONPATH=modeling \
python modeling/experiments/runners/run_baseline_mmr.py \
  --help
```

최저가 Baseline:

```bash
PYTHONPATH=modeling \
python modeling/experiments/runners/run_least_cost_baseline.py \
  --help
```

Baseline 결과와 OR-Tools 결과를 비교해 추천 품질, 비용, 반복률 및 식단 구성 안정성을 분석합니다.

### Optimizer 자동 튜닝

```text
Optimizer Input Snapshot 추출
→ Grid Search
→ 후보 정책 비교
→ Snapshot Replay
→ Policy Replay
→ 전체 시나리오 재검증
→ Validation Summary 비교
→ 기본 정책 반영
```

관련 스크립트:

```text
experiments/tuning/
├── extract_optimizer_snapshots.py
├── grid_search_optimizer_tuning.py
├── replay_optimizer_snapshots.py
├── replay_optimizer_policy.py
└── full_scenario_optimizer_grid.json
```

실험 결과는 `experiments/results/`에 생성됩니다. 대용량 또는 일회성 결과는 Git에 포함하지 않고, 재현에 필요한 분석 도구·시나리오·대표 결과만 관리하는 것을 권장합니다.

<br>

## 16. 배포 구조

Modeling API는 Backend와 분리된 Docker 컨테이너로 AWS EC2에서 운영합니다.

```text
Backend
→ HTTPS
→ Nginx
→ Modeling FastAPI Container
→ RAG Cloud API
```

FastAPI 컨테이너는 외부 포트에 직접 노출하지 않고, EC2 내부의 `127.0.0.1:8000`에만 바인딩합니다.

### 자동 배포 흐름

```text
main Push
→ GitHub Actions
→ 테스트 및 Docker Build
→ GHCR 이미지 업로드
→ EC2 이미지 Pull
→ Docker Compose 컨테이너 교체
→ 내부 Health Check
→ 외부 HTTPS Health Check
→ 실패 시 이전 이미지 Rollback
```

운영 도메인:

```text
https://modeling.todays-ggini.shop
```

상태 확인:

```bash
curl -fsS https://modeling.todays-ggini.shop/health
```

배포는 커밋 SHA 기반의 변경 불가능한 이미지 태그를 사용하여 실행 버전을 추적합니다.

상세 배포 문서:

- [`deploy/README.md`](deploy/README.md)

<br>

## 17. 모니터링

Modeling API는 Prometheus 형식의 메트릭을 `/metrics` Endpoint로 제공합니다.

### 현재 수집 지표

| 메트릭 | 설명 |
|---|---|
| `modeling_http_requests_total` | Endpoint·HTTP Method·상태 코드별 누적 요청 수 |
| `modeling_http_request_duration_seconds` | Endpoint별 요청 처리시간 Histogram |
| `modeling_http_requests_in_progress` | 현재 처리 중인 요청 수 |
| `modeling_api_errors_total` | Endpoint·오류 유형·상태 코드별 API 오류 수 |

`/health`와 `/metrics` 요청은 비즈니스 트래픽 통계를 왜곡하지 않도록 HTTP 요청 메트릭에서 제외합니다.

등록되지 않은 요청 경로는 원문을 Label로 사용하지 않고 `/unmatched`로 통합하여 Prometheus Label Cardinality 증가와 불필요한 시계열 생성을 방지합니다.

### 구성

```text
Modeling FastAPI /metrics
→ Prometheus Scrape
→ Grafana Dashboard
→ 운영 상태 확인
```

로컬 모니터링 실행:

```bash
docker compose \
  -f modeling/deploy/monitoring/docker-compose.monitoring.local.yml \
  up -d
```

Prometheus 설정:

```text
modeling/deploy/monitoring/prometheus/prometheus.yml
```

### 현재 확인 가능한 운영 지표

- 요청 수와 상태 코드 분포
- Endpoint별 오류율
- API 인증 및 의미 기반 오류 수
- 평균 및 분위수 응답시간
- 현재 처리 중인 요청 수

p95와 p99 응답시간은 Histogram Bucket 데이터를 기반으로 PromQL에서 계산합니다.

### 확장 예정 지표

- Solver 상태별 실행 횟수
- Optimizer 전용 실행시간
- 검증 실패 및 경고 비율
- 후보 메뉴 수 대비 필요 끼니 비율
- Fallback 발생 횟수
- 대체 메뉴 생성 상태
- RAG 데이터 품질 문제 비율

향후에는 오류율, p95·p99 응답시간, 인증 오류 및 최적화 실패율을 기준으로 경고 정책을 구성합니다.

<br>

## 18. 상세 문서

| 작업 영역 | 대표 문서 | 설명 |
|---|---|---|
| Persona | [`services/persona/README.md`](services/persona/README.md) | 페르소나 후보 생성, BMR·TDEE 및 권장 칼로리 계산 |
| Profile | [`services/profile/README.md`](services/profile/README.md) | 사용자 입력 검증, 한 끼 예산, 칼로리 기준 및 추천 가중치 생성 |
| RAG | [`services/rag/README.md`](services/rag/README.md) | RAG 요청, 응답 매핑, 가격·난이도 계산, 데이터 품질 진단 및 Fallback |
| Recommendation | [`services/recommendation/README.md`](services/recommendation/README.md) | 후보 메뉴 점수 계산, Soft Constraint 및 Quality Penalty |
| Meal Style | [`services/style/README.md`](services/style/README.md) | 샘플 식단 스타일 후보 생성 및 선택 결과 처리 |
| Optimizer | [`services/optimizer/README.md`](services/optimizer/README.md) | OR-Tools 월간 식단 최적화, 제약조건, 목적함수 및 재시도 정책 |
| Plan | [`services/plan/README.md`](services/plan/README.md) | 월간 식단 매핑, 대체 메뉴, 요약 및 품질 검증 |
| API | [`api/README.md`](api/README.md) | FastAPI 엔드포인트, 인증, 오류 처리 및 모니터링 |
| Tests | [`tests/README.md`](tests/README.md) | 단위·통합·회귀·HTTP 테스트 실행 방법 |
| Experiments | [`experiments/README.md`](experiments/README.md) | 실험, 검증, Snapshot Replay 및 결과 비교 |
| Data Contract | [`experiments/contract/README.md`](experiments/contract/README.md) | Backend와 Modeling 사이의 요청·응답 계약 검증 |
| Deployment | [`deploy/README.md`](deploy/README.md) | Docker, GHCR, EC2, Nginx 및 HTTPS 배포 |

<br>

## 19. Modeling 담당 범위

### Modeling 담당

- 사용자 및 가구원 입력 스키마 관리
- 가구원별 BMR·TDEE 및 권장 칼로리 계산
- 사용자 프로필과 추천 가중치 생성
- 페르소나 및 식단 스타일 후보 생성
- RAG 요청 Payload 구성
- RAG 응답 매핑 및 품질 진단
- 후보 메뉴 점수 계산
- 점수 기반 정렬과 MMR 다양성 재랭킹
- OR-Tools 월간 식단 최적화
- Optimizer 실패·재시도·완화 정책
- 대체 메뉴 생성
- 식단 요약 및 품질 검증
- Modeling FastAPI 서버
- Backend 연동 계약 검증
- 실험·튜닝·회귀 검증
- Docker 이미지 및 Modeling 배포
- 운영 메트릭과 모니터링

### Backend 연동 범위

- 인증된 사용자 기반 요청 생성
- Celery·Redis 비동기 작업 처리
- Modeling API 호출
- Modeling 응답 매핑
- 식단 결과 데이터베이스 저장
- Frontend 응답 제공

<table style="background-color:#FFF6C7; border-left:6px solid #E6C85C; padding:12px; width:100%;">
  <tr>
    <td>
      <strong>⭐ 설계 원칙</strong><br>
      추천·최적화 로직, 실험 도구, API 서빙, 배포 설정을 역할별 디렉터리로 분리하고,
      Backend와는 명시적인 Request·Response 계약을 기준으로 연동합니다.
      운영 코드의 변경은 계약 검증, 단위 테스트, 시나리오 검증 및 배포 Health Check를 거쳐 반영합니다.
    </td>
  </tr>
</table>
