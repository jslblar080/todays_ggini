# Optimizer Difficulty Diagnostics

## 1. 배경

월간 식단 최적화 실험 중 `US05_easy_cooking_low_skill` 시나리오에서 style validation fail이 발생했다.

해당 시나리오는 `간편식`을 목표로 하며, 사용자의 조리 실력과 허용 난이도가 모두 낮은 조건이다.

초기에는 optimizer가 쉬운 메뉴를 충분히 선택하지 못한 문제로 보일 수 있었지만, 추가 분석 결과 fail의 주요 원인은 optimizer 선택 문제가 아니라 후보풀의 difficulty score 분포 문제로 확인되었다.

---

## 2. 기존 문제

기존 validation 결과에서는 다음 정보만 확인할 수 있었다.

- validation_status: fail
- validation_message: 간편식 스타일에 비해 조리 난이도 부담이 있어 보완이 필요합니다.
- average_difficulty_score: 14.33

이 정보만으로는 다음 원인을 구분하기 어려웠다.

1. optimizer가 쉬운 후보를 선택하지 못한 문제
2. 후보풀 자체에 쉬운 메뉴가 부족한 문제
3. RAG difficulty mapping 산식이 난이도를 과대평가한 문제
4. validation threshold가 후보풀 현실성을 반영하지 못한 문제

---

## 3. 개선 방향

threshold를 임의로 낮추거나 특정 시나리오 예외를 추가하지 않고, 먼저 실패 원인을 분리하는 diagnostics를 추가했다.

추가된 diagnostics는 `style_validation.diagnostics.difficulty_feasibility`에 저장된다.

예시:

- status: absolute_pass_unreachable
- reason: candidate_difficulty_shortage
- candidate_count: 72
- candidate_avg_difficulty: 12.64
- candidate_p90_difficulty: 40.0
- candidate_max_difficulty: 70.0
- candidate_ge75_count: 0
- candidate_ge65_count: 1

---

## 4. Final Validation Summary 반영

final validation 분석 결과에 difficulty feasibility diagnostics 집계를 추가했다.

`final_replay_0038` 기준 결과는 다음과 같다.

difficulty_feasibility_status_count:

- pass_threshold_very_sparse: 5
- candidate_pool_has_pass_options: 6
- absolute_pass_unreachable: 4

difficulty_feasibility_reason_count:

- candidate_difficulty_sparse: 5
- candidate_pool_feasible: 6
- candidate_difficulty_shortage: 4

이를 통해 validation fail 또는 warning이 발생했을 때, 단순히 결과가 나쁘다는 정보뿐 아니라 후보풀 수준의 원인까지 함께 확인할 수 있다.

---

## 5. US05 분석 결과

`US05_easy_cooking_low_skill` 시나리오의 diagnostics는 다음과 같다.

- validation_status: fail
- difficulty_feasibility_status: absolute_pass_unreachable
- difficulty_feasibility_reason: candidate_difficulty_shortage
- difficulty_candidate_count: 72
- difficulty_candidate_p90_difficulty: 40.0
- difficulty_candidate_max_difficulty: 70.0
- difficulty_candidate_ge75_count: 0
- difficulty_candidate_ge65_count: 1

즉, 간편식 validation 기준인 75점을 만족하는 후보가 0개였기 때문에, 이 시나리오는 optimizer가 아무리 잘 선택하더라도 pass 기준을 달성할 수 없는 상태였다.

---

## 6. RAG Difficulty Mapping 분석 결과

RAG difficulty mapping 구성 요소를 분석한 결과, low skill 및 간편식 목표 시나리오에서 difficulty score가 매우 낮게 분포하는 것을 확인했다.

low skill 그룹 결과:

- menu_count: 450
- difficulty_score_avg: 8.71
- difficulty_score_p90: 40.0
- difficulty_score_max: 70.0
- ge75: 0
- ge65: 7
- ge40: 59
- eq0: 256

raw difficulty 분포:

- raw difficulty 2: 7
- raw difficulty 3: 52
- raw difficulty 4: 135
- raw difficulty 5: 256

즉, low skill 사용자에게 제공되는 후보 대부분이 raw difficulty 4~5로 매핑되고 있으며, 이로 인해 difficulty score가 0~40 구간에 몰리고 있다.

---

## 7. 산식 구성 요소 분석

low skill / 간편식 그룹의 difficulty 구성 요소 평균은 다음과 같다.

- ingredient_points_avg: 2.24
- step_points_avg: 1.86
- cooking_time_points_avg: 1.0
- action_points_avg: 1.57
- estimated_usage_points_avg: 0.94
- difficulty_points_avg: 약 7점대

현재 raw difficulty 변환 기준에서는 difficulty_points가 6~7이면 raw difficulty 4, 8 이상이면 raw difficulty 5가 된다.

따라서 일반적인 후보 메뉴도 다음과 같이 점수가 누적될 수 있다.

- 재료 수 점수 약 2점
- 조리 단계 점수 약 2점
- 조리 시간 점수 1점
- 조리 동작 점수 약 1.5점
- 사용량 추정 점수 약 1점
- 총합 약 7~8점
- raw difficulty 4~5
- low skill 사용자 기준 difficulty_score 10 또는 0

---

## 8. 현재 해석

현재까지의 결론은 다음과 같다.

- US05 fail은 optimizer objective 문제보다는 후보풀 difficulty mapping 문제에 가깝다.
- 간편식 threshold를 임의로 낮추기보다, RAG difficulty mapping 산식 개선이 우선이다.

특히 다음 요소가 난이도 과대평가 가능성이 있다.

1. cooking_time 20분 기본값이 항상 +1점으로 반영
2. estimated_usage_points가 조리 난이도에 포함
3. 기본 조리 동작도 action_points로 강하게 누적
4. 세분화된 step_count가 난이도 상승으로 연결

---

## 9. 산식 개선 후보

### 9.1 estimated_usage_points 분리

`estimated_usage_points`는 조리 난이도보다는 재료 사용량 또는 가격 추정의 불확실성에 가깝다.

따라서 difficulty에서 분리하고, 다음과 같은 별도 지표로 관리하는 것을 검토할 수 있다.

- data_quality_score
- pricing_confidence
- measurement_confidence

### 9.2 cooking_time 기본값 처리

`cooking_time_points_avg`가 모든 그룹에서 1.0으로 나타났다.

이는 cooking_time 20분이 실제 조리 시간이라기보다 기본값처럼 들어오는 경우가 많을 가능성을 시사한다.

개선 후보:

- cooking_time이 기본값인지 실제 추정값인지 구분
- 기본값 20분은 difficulty penalty에서 제외 또는 약화
- 30분 이상부터 명확한 penalty 적용

### 9.3 action_points 완화

현재 action_points는 대부분의 메뉴에 1~2점이 부여된다.

개선 후보:

- 섞다, 올리다, 곁들이다 등 기본 동작은 penalty 제외
- 굽다, 볶다, 끓이다, 익히다는 낮은 penalty
- 튀기다, 반죽, 숙성, 졸이기 등만 높은 penalty

### 9.4 step_count 기준 재검토

step_count는 레시피가 세분화되어 있을수록 높아질 수 있다.

개선 후보:

- 단순 단계 수보다 주요 조리 동작 수 기반 산정
- step_count threshold 완화
- 중복되거나 세분화된 안내 단계 제거

---

## 10. 후속 작업

다음 작업은 산식 변경 전후를 비교할 수 있도록 snapshot replay 기반 실험으로 진행한다.

추천 순서:

1. difficulty 산식 후보 정의
2. 기존 snapshot 기반 mapping replay
3. low skill / 간편식 후보풀 difficulty 분포 비교
4. final validation 재실행
5. validation_status_count 및 difficulty_feasibility_status_count 비교

산식 변경은 threshold 임시 완화가 아니라, 조리 난이도 의미에 맞지 않는 요소를 분리하거나 완화하는 방향으로 진행한다.

---

---

## 11. Estimated Usage Points 분리 실험 결과

RAG difficulty formula policy replay 결과, `estimated_usage_points`를 difficulty 합산에서 제외하는 후보는 low skill / 간편식 후보풀의 difficulty score 분포를 개선하는 효과가 있었다.

US05 기준 replay 결과:

- average_difficulty_score 개선 가능성 확인
- ge65 후보 증가
- difficulty_score 0점 후보 감소

그러나 실제 서비스 코드에 `estimated_usage_points` 제외를 적용한 뒤 full validation을 실행하는 과정에서 `US08_very_low_budget` 시나리오의 solver INFEASIBLE이 관측되었다.

이후 해당 변경을 rollback한 상태에서도 US08 단독 재실행에서 INFEASIBLE이 재현되었기 때문에, 이 현상을 estimated_usage_points 제외의 직접적인 regression으로 단정할 수는 없다.

`US08_very_low_budget` 관측 결과:

- solver_status: INFEASIBLE
- selected_menu_count: 0
- meal_coverage_rate: 0.0
- validation_status: unknown

US08은 difficulty 중심 시나리오가 아니라 very low budget 시나리오이며, 0038 성공 결과에서도 예산 여유가 약 1,153원에 불과했다. 따라서 현재는 very low budget 시나리오의 optimizer feasibility 취약성으로 분리해 분석한다.

따라서 `estimated_usage_points`를 단순히 difficulty 합산에서 제외하는 변경은 바로 적용하지 않고, budget feasibility diagnostics를 보강한 뒤 다시 검토한다.

현재 결론:

- estimated_usage_points는 조리 난이도와 의미적으로 분리하는 방향이 타당하다.
- 하지만 단순 제외 방식은 US08의 직접 원인으로 단정할 수 없다.
- 이후에는 budget feasibility, optimizer hard constraint, difficulty score 변화가 후보 선택에 미치는 영향을 함께 검토해야 한다.

후속 작업:

1. US08 very low budget 시나리오의 optimizer infeasible 원인 분석
2. budget hard constraint와 difficulty score 변화의 상호작용 확인
3. estimated_usage_points를 완전 제외하는 대신 별도 confidence metric으로 분리하는 방식 검토
4. 산식 변경 전후를 snapshot replay뿐 아니라 full validation regression 기준으로 비교
5. INFEASIBLE 발생 시에도 input snapshot과 budget feasibility diagnostics를 남기도록 보강

