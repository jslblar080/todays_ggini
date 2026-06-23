# 모델링 Validation 및 Optimizer 튜닝 검증 문서

## 1. 작업 배경

월간 식단 생성 파이프라인에서 일부 사용자 조건이 validation fail 또는 warning으로 분류되는 문제가 있었다.

특히 고단백 목표, 낮은 조리 실력, 낮은 예산, 좁은 선호 조건이 함께 적용되는 경우 RAG 후보풀 품질, optimizer 제약 조건, validation 기준 중 어느 부분이 원인인지 구분하기 어려웠다.

이에 따라 validation 기준 보정, RAG diagnostics, optimizer fallback, diversity repeat penalty, 고단백 가중치 튜닝을 순차적으로 진행했다.

---

## 2. 검증 대상

이번 검증은 다음 영역을 대상으로 진행했다.

- style validation warning 기준
- 사용자 안정성 시나리오
- RAG 후보풀 mapping 품질
- optimizer infeasible fallback
- diversity 기반 repeat penalty
- 고단백 목표 optimizer 가중치
- 전체 final validation 시나리오
- 전체 가중치 조합 기반 snapshot replay

---

## 3. 검증 파이프라인

모델링 파이프라인은 다음 흐름으로 구성된다.

    사용자 프로필 입력
    → RAG 후보 메뉴 생성
    → RAG response mapping
    → optimizer input builder
    → OR-Tools optimizer
    → plan validation
    → summary/diagnostics 생성

이번 작업에서는 각 단계에서 발생할 수 있는 문제를 분리해서 확인할 수 있도록 diagnostics와 summary 지표를 보강했다.

---

## 4. 주요 개선 내용

### 4.1 Style validation warning 기준 보정

일부 시나리오에서 실제 식단 생성은 성공했지만 후보풀 한계로 인해 validation fail로 분류되는 문제가 있었다.

이를 개선하기 위해 후보풀 자체에서 기준을 만족하기 어려운 경우, 단순 실패가 아니라 warning으로 분류할 수 있도록 validation 기준을 보정했다.

### 4.2 사용자 안정성 시나리오 추가

낮은 예산, 간편식, 좁은 선호 조건, 낮은 조리 실력 등 validation 취약 케이스를 분리하여 사용자 안정성 시나리오를 추가했다.

### 4.3 Final validation 자동화

final validation 실행 및 분석 스크립트를 추가하여 validation status, solver status, warning/fail 원인, runtime, duplicate rate 등을 자동으로 요약할 수 있도록 했다.

### 4.4 RAG diagnostics 추가

RAG 후보풀 품질을 확인하기 위해 raw menu 수, mapped menu 수, excluded menu 수, quality issue menu 수, ingredient group mapping 상태를 확인할 수 있도록 했다.

이를 통해 validation warning/fail의 원인이 RAG 후보풀 문제인지 optimizer 문제인지 분리해서 확인할 수 있도록 했다.

### 4.5 Optimizer infeasible fallback 추가

optimizer가 infeasible 또는 후보풀 부족 상태에 도달했을 때 fallback 처리 흐름을 추가했다.

fallback 과정에서 active constraint와 relaxation action을 diagnostics로 기록하여 어떤 제약이 문제였고 어떤 완화가 적용되었는지 확인할 수 있도록 했다.

### 4.6 Diversity repeat penalty 개선

월간 식단 생성 시 동일 메뉴가 과도하게 반복 선택되는 문제를 줄이기 위해 사용자 다양성 선호도 기반 repeat penalty를 개선했다.

### 4.7 고단백 목표 optimizer 가중치 조정

고단백 목표와 낮은 조리 실력 조건이 함께 적용될 때 protein objective와 difficulty bonus 사이의 trade-off가 발생할 수 있었다.

이를 개선하기 위해 고단백 목표 사용자에 대해 다음 기본 정책을 반영했다.

- repeat_penalty_weight: 5000
- protein_bonus_weight: 180
- protein_bonus_cap_grams: 35
- difficulty_bonus_weight: 0
- 고단백 목표에서는 difficulty bonus 자동 적용 제외

---

## 5. 최종 full validation 결과

전체 final validation 기준 최종 결과는 다음과 같다.

| 지표 | 값 |
|---|---:|
| scenario_count | 15 |
| success_count | 15 |
| fail_count | 0 |
| success_rate | 1.0 |
| validation_fail_count | 0 |
| validation_status_count | pass 7 / warning 8 |
| solver_success_rate | 1.0 |
| meal_coverage_rate | 1.0 |
| budget_absolute_unreachable_count | 0 |
| rag_mapping_success_rate | 1.0 |

주요 취약 시나리오였던 US11은 fail에서 warning으로 개선되었고, US13은 pass 상태를 유지했다.

---

## 6. RAG 포함 전체 grid search 결과

고단백 optimizer 가중치 후보를 전체 stability 시나리오 기준으로 비교하기 위해 RAG 포함 grid search를 수행했다.

검증 대상 grid는 다음과 같다.

- repeat_penalty_weight: 4500, 5000, 5500, 6000
- repeat_penalty_growth: quadratic
- protein_bonus_weight: 150, 180, 220
- protein_bonus_cap_grams: 35
- difficulty_bonus_weight: 0

총 12개 가중치 조합을 대상으로 실행했다.

### 6.1 Ranking eligible 후보

| rank | case_id | repeat_penalty_weight | protein_bonus_weight | validation_fail_count | validation_warning_count | duplicate_rate | unique_menu_ratio | objective_score |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | grid_0002 | 4500 | 180 | 2 | 6 | 0.2065 | 0.7935 | 594.8 |
| 2 | grid_0001 | 4500 | 150 | 2 | 7 | 0.1972 | 0.8028 | 572.24 |

### 6.2 해석

나머지 후보는 rag_api 오류로 ranking 대상에서 제외되었다.

특히 grid_0004 이후 대부분의 후보에서 전체 시나리오가 RAG 호출 단계에서 실패했다.

따라서 RAG 포함 grid search 결과만으로는 모든 가중치 조합의 순수 optimizer 성능을 비교하기 어렵다.

이에 따라 RAG 호출 영향을 제거한 snapshot replay 기반 추가 검증을 수행했다.

---

## 7. Snapshot replay 기반 추가 검증 결과

RAG API 호출 영향을 제거하고 동일한 후보풀 조건에서 optimizer 가중치만 비교하기 위해 snapshot replay를 수행했다.

snapshot_base_result.json에서 optimizer input snapshot을 추출했으며, 추출 결과는 다음과 같다.

| 지표 | 값 |
|---|---:|
| total_result_count | 15 |
| snapshot_count | 15 |
| missing_snapshot_count | 0 |

이후 64개 가중치 조합을 15개 snapshot 시나리오에 대해 replay했다.

### 7.1 Snapshot replay 상위 후보

| rank | case_id | repeat_penalty_weight | protein_bonus_weight | difficulty_bonus_weight | validation_status | duplicate_rate | unique_menu_ratio | objective_score |
|---:|---|---:|---:|---:|---|---:|---:|---:|
| 1 | replay_0061 | 6000 | 220 | 0 | pass 6 / warning 8 / fail 1 | 0.2170 | 0.7830 | 290.14 |
| 2 | replay_0037 | 4500 | 150 | 0 | pass 6 / warning 8 / fail 1 | 0.2239 | 0.7761 | 288.34 |
| 3 | replay_0042 | 4500 | 180 | 50 | pass 6 / warning 8 / fail 1 | 0.2352 | 0.7648 | 285.63 |
| 4 | replay_0053 | 6000 | 150 | 0 | pass 5 / warning 9 / fail 1 | 0.2087 | 0.7913 | 257.58 |
| 5 | replay_0021 | 3500 | 150 | 0 | pass 6 / warning 8 / fail 1 | 0.2478 | 0.7522 | 255.77 |

### 7.2 Snapshot replay 해석

snapshot replay 기준으로는 replay_0061이 가장 높은 objective score를 기록했다.

replay_0061의 설정은 다음과 같다.

- repeat_penalty_weight: 6000
- protein_bonus_weight: 220
- difficulty_bonus_weight: 0
- repeat_penalty_growth: quadratic

다만 기존 최종 후보였던 replay_0037도 2위로 확인되었으며, 두 후보의 objective score 차이는 작았다.

| 비교 항목 | replay_0061 | replay_0037 |
|---|---:|---:|
| objective_score | 290.14 | 288.34 |
| validation_fail_count | 1 | 1 |
| validation_warning_count | 8 | 8 |
| duplicate_warning_count | 11 | 11 |
| avg_unique_menu_ratio | 0.7830 | 0.7761 |
| avg_duplicate_rate | 0.2170 | 0.2239 |
| avg_duplicate_excess_rate | 0.0382 | 0.0396 |

따라서 snapshot replay 기준으로는 replay_0061이 후속 full validation 후보로 가장 적합하다.

하지만 replay_0061은 아직 RAG 포함 full validation까지 최종 확인된 후보는 아니므로, 운영 기본 정책을 즉시 변경하기보다는 후속 full validation 대상으로 기록한다.

---

## 8. 최종 정책 선택 근거

현재 기본 정책은 기존 full validation을 통과한 후보를 유지한다.

snapshot replay 결과에서는 replay_0061이 가장 높은 점수를 기록했지만, RAG 포함 full validation까지 확인된 최종 운영 후보는 기존 정책이다.

따라서 현재 결론은 다음과 같다.

- 운영 기본 정책은 기존 full validation 통과 후보를 유지한다.
- replay_0061은 후속 full validation 후보로 기록한다.
- RAG 포함 검증과 snapshot replay 결과를 함께 비교하여 최종 정책 변경 여부를 판단한다.

---

## 9. Optuna 미도입 사유

현재 튜닝 대상 파라미터 수가 제한적이고, 각 가중치의 의미를 명확히 해석해야 하는 단계였기 때문에 Optuna 기반 자동 탐색보다는 grid search 방식을 선택했다.

grid search는 후보별 결과를 비교하기 쉽고, 특정 시나리오에서 어떤 trade-off가 발생했는지 설명하기 용이하다.

Optuna는 향후 튜닝 대상 파라미터가 증가하거나, 시나리오 수가 늘어나 탐색 공간이 커질 경우 도입을 검토한다.

---

## 10. 결론 및 후속 작업

이번 작업을 통해 validation fail과 warning을 더 명확하게 구분할 수 있게 되었고, RAG 후보풀 문제와 optimizer 제약 문제를 분리해서 분석할 수 있는 기반을 마련했다.

또한 고단백 목표, 다양성 선호도, 후보풀 부족 상황에 대해 optimizer가 더 안정적으로 동작하도록 기본 정책을 개선했다.

추가 검증으로 RAG 포함 grid search와 snapshot replay를 모두 수행했다.

RAG 포함 grid search는 실제 서비스 흐름에 가깝지만 RAG API 오류의 영향을 받았고, snapshot replay는 RAG 영향을 제거한 상태에서 순수 optimizer 가중치를 비교하는 데 유용했다.

향후 작업은 다음 순서로 진행한다.

1. replay_0061 후보에 대한 RAG 포함 full validation 추가 수행
2. 필요 시 고단백 optimizer 기본 정책 재조정
3. 모델링 파이프라인 serving API 연결
4. 동기 API 검증 후 비동기 job 처리 및 Redis 기반 상태 관리 확장
