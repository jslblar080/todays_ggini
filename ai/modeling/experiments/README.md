# Modeling Experiments

모델링 실험, 검증, 분석 및 파라미터 튜닝 도구를 관리하는 디렉터리입니다.

## Directory structure

- `analysis/`: 실험 결과 비교 및 분석
- `contract/`: 백엔드·모델링 API 계약 검증 도구
- `docs/`: 실험 및 검증 관련 문서
- `fixtures/`: 테스트 및 실험 입력 데이터
- `flows/`: 전체 추천 흐름 수동 실행
- `optimizer/`: 옵티마이저 관련 실험
- `persona/`: 페르소나 관련 실험 도구
- `pipelines/`: 통합 검증 파이프라인
- `runners/`: 개별 실험 실행 진입점
- `scenarios/`: 검증 시나리오
- `tuning/`: 파라미터 탐색 및 자동 튜닝

## Main commands

### Final validation

```bash
PYTHONPATH=ai/modeling \
python ai/modeling/experiments/pipelines/run_final_validation_pipeline.py --help
```

### Baseline MMR

```bash
PYTHONPATH=ai/modeling \
python ai/modeling/experiments/runners/run_baseline_mmr.py --help
```

### Least-cost baseline

```bash
PYTHONPATH=ai/modeling \
python ai/modeling/experiments/runners/run_least_cost_baseline.py --help
```

## Documents

- `docs/final_validation.md`: 최종 검증 파이프라인 안내
- `docs/rag_diagnostics.md`: RAG 진단 실행 안내
- `docs/modeling_validation_optimizer_report.md`: 모델링 검증 및 옵티마이저 보고서
- `docs/optimizer_difficulty_diagnostics.md`: 난이도 관련 진단 문서

실험 실행 결과는 각 `results/` 디렉터리에 생성되며 Git 추적 대상에서 제외됩니다.
