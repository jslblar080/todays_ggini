# RAG Mapping Diagnostics 및 최종 Validation 확장 결과

## 1. 목적

이 문서는 최종 월간 식단 Validation 과정에서 RAG 후보 메뉴가 Modeling 내부 후보 구조로 정상 변환되는지 확인하기 위한 diagnostics 결과를 정리한다.

기존에는 RAG Mapper 로그에서만 raw_menus, mapped_menus, excluded_menus, quality_issue_menus를 확인할 수 있었다. 이 방식은 터미널 로그를 직접 확인해야 했기 때문에 실험 결과 artifact와 연결해서 분석하기 어려웠다.

이번 작업에서는 RAG mapping diagnostics를 서비스 응답 payload에는 포함하지 않고, experiment result artifact의 diagnostics.rag_mapping 필드에만 저장하도록 확장하였다.

이를 통해 최종 validation summary에서 RAG 후보 데이터 품질과 mapping 안정성을 함께 확인할 수 있게 되었다.

---

## 2. 수집 지표

RAG mapping diagnostics에서 수집하는 지표는 다음과 같다.

    rag_mapping_event_count
    - 시나리오 실행 중 RAG mapper가 호출된 횟수

    rag_raw_menus
    - RAG 응답에서 전달된 원본 후보 메뉴 수

    rag_mapped_menus
    - Modeling 내부 candidate menu 구조로 변환된 메뉴 수

    rag_excluded_menus
    - 구조적으로 유효하지 않아 제외된 메뉴 수

    rag_quality_issue_menus
    - 변환은 되었지만 데이터 품질 이슈가 기록된 메뉴 수

    rag_mapping_success_rate
    - rag_mapped_menus / rag_raw_menus

    rag_quality_issue_rate
    - rag_quality_issue_menus / rag_mapped_menus

---

## 3. 구현 방식

RAG mapping diagnostics는 다음 방식으로 수집한다.

    1. map_rag_response_to_candidate_menus 실행 시 mapping 결과를 기록한다.
    2. 실험 runner는 시나리오 실행 시작 전에 diagnostics collector를 초기화한다.
    3. 시나리오 실행이 끝나면 diagnostics.rag_mapping 필드에 누적 결과를 저장한다.
    4. analyze_final_validation_result.py는 result artifact의 diagnostics.rag_mapping을 읽어 row와 summary에 반영한다.

중요한 기준은 다음과 같다.

    - 백엔드/프론트 연동용 Modeling 응답 payload는 변경하지 않는다.
    - diagnostics는 실험 결과 artifact에만 저장한다.
    - ContextVar 기반으로 시나리오 실행 단위 diagnostics를 분리한다.
    - 전역 리스트 누적으로 인한 서비스 런타임 오염을 방지한다.

---

## 4. 실행 방법

RAG diagnostics가 정상 수집되는지 확인하려면 smoke script를 실행한다.

    ./scripts/run_rag_diagnostics_smoke.sh

이 스크립트는 다음 작업을 한 번에 수행한다.

    1. 관련 Python 파일 py_compile
    2. 사용자 안정성 시나리오 실행
    3. rag_diagnostics_smoke_result.json 생성
    4. diagnostics.rag_mapping summary 출력

---

## 5. 15개 최종 Validation 시나리오

기존 사용자 안정성 시나리오는 6개였고, 최종 validation 범위를 넓히기 위해 15개로 확장하였다.

현재 시나리오는 다음과 같다.

    US01_balanced_default
    - 기본 균형형 사용자

    US02_low_budget_saving
    - 식비 절약 + 낮은 예산 사용자

    US03_high_protein
    - 고단백 목표 사용자

    US04_diet_calorie_control
    - 다이어트 + 칼로리 제한 사용자

    US05_easy_cooking_low_skill
    - 간편식 + 낮은 조리 실력 사용자

    US06_narrow_preference
    - 선호 조건이 매우 좁은 사용자

    US07_allergy_strict
    - 알레르기 조건 포함 사용자

    US08_very_low_budget
    - 매우 낮은 예산 사용자

    US09_high_diversity
    - 높은 다양성 선호 사용자

    US10_taste_dessert_preference
    - 맛 중심 + 디저트 선호 사용자

    US11_complex_constraints
    - 복합 제약 조건 사용자

    US12_high_meal_count
    - 하루 식사 수가 많은 사용자

    US13_multi_family
    - 다인 가구형 조건 사용자

    US14_narrow_preference_high_budget
    - 예산 충분 + 선호 조건 좁은 사용자

    US15_diet_allergy_low_skill
    - 다이어트 + 알레르기 + 낮은 조리 실력 사용자

---

## 6. 15개 시나리오 실행 결과

15개 사용자 안정성 시나리오 기준 최근 실행 결과는 다음과 같다.

    scenario_count: 15
    success_count: 15
    fail_count: 0
    success_rate: 1.0
    error_rate: 0.0

    solver_status_count:
    - FEASIBLE: 9
    - OPTIMAL: 5
    - INFEASIBLE: 1

    solver_success_rate: 0.9333
    fallback_rate: 0.1333
    candidate_pool_enough_rate: 1.0
    meal_coverage_rate: 0.9318
    duplicate_rate: 0.3138

    rag_mapping_event_count: 19
    rag_raw_menus: 3276
    rag_mapped_menus: 3276
    rag_excluded_menus: 0
    rag_quality_issue_menus: 3276
    rag_mapping_success_rate: 1.0
    rag_quality_issue_rate: 1.0

---

## 7. 결과 해석

### 실행 안정성

15개 시나리오 모두 runner 기준으로 성공하였다.

즉, 요청 처리, 시나리오 실행, result artifact 생성, summary 분석까지의 실험 파이프라인은 정상 동작한다.

다만 runner success와 solver success는 분리해서 해석해야 한다.

    runner success_rate: 1.0
    solver_success_rate: 0.9333

runner success는 실험 실행 자체가 정상 완료되었음을 의미하고, solver success는 OR-Tools가 OPTIMAL 또는 FEASIBLE 결과를 반환했음을 의미한다.

---

### Solver 안정성

15개 중 1개 시나리오에서 INFEASIBLE이 발생하였다.

    US08_very_low_budget
    - solver_status: INFEASIBLE
    - selected_menu_count: 0
    - meal_coverage_rate: 0.0
    - candidate_pool_is_enough: True

이 결과는 후보 수 부족 때문이 아니라, 매우 낮은 예산 조건에서 OR-Tools 제약을 만족하는 월간 조합을 찾지 못한 것으로 해석한다.

따라서 해당 케이스는 단순 실행 실패가 아니라, 운영 환경에서 별도 fallback 또는 사용자 안내가 필요한 엣지 케이스로 관리한다.

---

### Validation fail 사례

US05와 US11은 runner와 solver 관점에서는 성공했지만 validation_status가 fail로 나타났다.

    US05_easy_cooking_low_skill
    - solver_status: OPTIMAL
    - meal_coverage_rate: 1.0
    - validation_status: fail
    - 원인: 간편식 스타일 대비 평균 난이도 점수 부족

    US11_complex_constraints
    - solver_status: FEASIBLE
    - fallback_used: True
    - validation_status: fail
    - 원인: 복합 제약 조건에서 고단백 기준 미달

이는 생성 자체의 실패가 아니라, 선택한 스타일 또는 사용자 조건에 비해 품질 기준을 만족하지 못한 케이스이다.

따라서 최종 validation에서는 success_count만 보는 것이 아니라 validation_fail_rate와 fallback_rate를 함께 확인해야 한다.

---

### RAG Mapping 안정성

RAG mapping 결과는 다음과 같다.

    rag_mapping_success_rate: 1.0
    rag_excluded_menus: 0

즉, RAG가 반환한 후보 메뉴는 모두 Modeling 내부 후보 구조로 변환되었고, 구조적으로 제외된 후보는 없었다.

하지만 다음 지표가 동시에 확인되었다.

    rag_quality_issue_rate: 1.0

이는 모든 후보가 변환은 되었지만, 각 후보에 데이터 품질 이슈가 기록되었다는 의미이다.

따라서 현재 RAG 후보 데이터의 구조적 mapping은 안정적이지만, 영양값, 가격, 카테고리, 재료군 등 데이터 품질 보강이 후속 개선 과제로 남아 있다.

---

## 8. 현재 판단

현재 최종 validation 파이프라인은 다음을 확인할 수 있다.

    - 사용자 조건별 실행 성공률
    - OR-Tools solver 성공률
    - INFEASIBLE 발생 여부
    - fallback 발생 여부와 원인
    - 후보 풀 충분성
    - 월간 식단 coverage
    - 중복 메뉴 비율
    - RAG mapping 성공률
    - RAG 데이터 품질 이슈 비율

이를 통해 단순히 월간 식단이 생성되었는지가 아니라, 어떤 조건에서 품질 저하, fallback, infeasible, 데이터 품질 문제가 발생하는지 구분할 수 있다.

---

## 9. 후속 개선 방향

다음 개선 작업은 별도 브랜치에서 진행한다.

    1. 매우 낮은 예산 조건에서 solver infeasible 발생 시 fallback 전략 보강
    2. 간편식 스타일의 difficulty score 기준 개선
    3. 복합 제약 조건에서 고단백 기준을 만족하지 못하는 원인 분석
    4. duplicate_rate를 낮추기 위한 OR-Tools 반복 penalty 조정
    5. RAG quality_issue_rate를 낮추기 위한 후보 데이터 품질 보강
    6. raw_menus, mapped_menus, quality_issue_menus를 운영 모니터링 지표로 확장
