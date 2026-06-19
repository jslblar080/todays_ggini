# 최종 월간 식단 Validation 실행 가이드

## 1. 목적

최종 월간 식단 Validation은 OR-Tools 기반 월간 식단 생성 결과가 실제 서비스에 적용 가능한 품질인지 검증하기 위한 절차이다.

이 Validation은 단순히 월간 식단 생성 성공 여부만 확인하지 않고, 요청/응답 구조, 생성 성공률, solver 상태, fallback 발생 여부, 후보 풀 충분성, 스타일 반영 여부, 중복 메뉴 및 다양성 지표까지 함께 확인한다.

기존 Style Validation이 선택한 식단 스타일의 가중치와 focus_key 반영 여부를 확인하는 구조였다면, 최종 Validation은 이를 포함하여 월간 식단 생성 파이프라인 전체가 운영 가능한 품질인지 확인하는 단계이다.

---

## 2. 실행 대상

기본 실행 대상 시나리오는 다음 파일이다.

    ai/modeling/experiments/scenarios/style_validation_user_stability_scenarios.json

현재 포함된 사용자 안정성 시나리오는 다음과 같다.

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

---

## 3. 전체 Validation 실행

시나리오 실행부터 결과 저장, 최종 분석 summary 생성까지 한 번에 수행한다.

    ./scripts/run_final_validation.sh

기본 출력 파일은 다음과 같다.

    ai/modeling/experiments/results/final_validation_user_stability_result.json
    ai/modeling/experiments/results/final_validation_user_stability_summary.json
    ai/modeling/experiments/results/final_validation_user_stability_summary.csv

---

## 4. 기존 결과 파일만 다시 분석

이미 생성된 result JSON을 기반으로 분석만 다시 수행할 때 사용한다.

    ./scripts/analyze_final_validation.sh

이 명령은 실험을 재실행하지 않고 기존 result 파일을 분석한다.

---

## 5. 직접 Python pipeline 실행

shell script를 사용하지 않고 직접 실행할 수도 있다.

    PYTHONPATH=ai/modeling python ai/modeling/experiments/run_final_validation_pipeline.py \
      --scenario-file ai/modeling/experiments/scenarios/style_validation_user_stability_scenarios.json \
      --result-output ai/modeling/experiments/results/final_validation_user_stability_result.json \
      --summary-output ai/modeling/experiments/results/final_validation_user_stability_summary.json \
      --csv-output ai/modeling/experiments/results/final_validation_user_stability_summary.csv

기존 결과만 분석하려면 --skip-run 옵션을 사용한다.

    PYTHONPATH=ai/modeling python ai/modeling/experiments/run_final_validation_pipeline.py \
      --scenario-file ai/modeling/experiments/scenarios/style_validation_user_stability_scenarios.json \
      --result-output ai/modeling/experiments/results/final_validation_user_stability_result.json \
      --summary-output ai/modeling/experiments/results/final_validation_user_stability_summary.json \
      --csv-output ai/modeling/experiments/results/final_validation_user_stability_summary.csv \
      --skip-run

---

## 6. 주요 Validation 지표

### 실행 안정성

    scenario_count
    success_count
    fail_count
    success_rate
    error_rate

### 응답 시간

    avg_runtime_ms
    p50_runtime_ms
    p95_runtime_ms
    p99_runtime_ms
    max_runtime_ms

### OR-Tools solver 상태

    solver_status_count
    solver_success_count
    solver_success_rate
    optimal_count
    optimal_rate
    feasible_count
    feasible_rate
    non_success_solver_count
    non_success_solver_rate

### 후보 풀 및 fallback

    fallback_count
    fallback_rate
    fallback_reason_count
    candidate_pool_enough_count
    candidate_pool_enough_rate
    candidate_pool_shortage_count
    candidate_pool_shortage_rate
    candidate_shortage_reason_count
    recommended_next_step_count
    candidate_to_required_ratio

### 월간 식단 완성도

    required_meal_count
    selected_menu_count
    meal_coverage_rate
    available_recommendation_count

### 스타일 및 품질 검증

    validation_status_count
    validation_warning_count
    validation_warning_rate
    validation_fail_count
    validation_fail_rate
    secondary_warning_type_count
    secondary_warning_level_count

### 중복 메뉴 및 다양성

    unique_menu_count
    duplicate_menu_count
    unique_menu_ratio
    duplicate_rate
    duplicate_warning_count
    duplicate_warning_rate

---

## 7. 현재 보류 중인 지표

다음 지표는 아직 result JSON에 구조화되어 저장되지 않기 때문에 현재 분석 대상에서 제외한다.

    timeout_count
    timeout_rate
    raw_menus
    mapped_menus
    excluded_menus
    quality_issue_menus
    quality_issue_rate
    mapping_success_rate

해당 지표를 추가하려면 서비스 응답 payload가 아니라 실험 결과 artifact에 별도 diagnostics로 저장하는 방식으로 확장한다.

---

## 8. 기준

현재 최종 Validation은 실제 result JSON에 존재하는 구조화 필드만 기반으로 분석한다.

추정값이나 임의 기준에 의존하는 휴리스틱 지표는 추가하지 않는다.

---

## 9. 현재 실행 예시 결과

사용자 안정성 6개 시나리오 기준 최근 실행 결과는 다음과 같다.

    scenario_count: 6
    success_count: 6
    fail_count: 0
    success_rate: 1.0
    error_rate: 0.0

    solver_status_count:
    - FEASIBLE: 3
    - OPTIMAL: 3

    solver_success_rate: 1.0
    fallback_rate: 0.1667
    candidate_pool_enough_rate: 1.0
    meal_coverage_rate: 1.0
    duplicate_rate: 0.3588

이 결과를 통해 현재 OR-Tools 기반 월간 식단 생성은 사용자 안정성 시나리오 기준으로 실행 안정성과 식단 완성도는 확보되었으며, 중복 메뉴 및 validation warning은 후속 품질 개선 지표로 관리한다.
