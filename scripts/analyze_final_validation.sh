#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

SCENARIO_FILE="${1:-modeling/experiments/scenarios/style_validation_user_stability_scenarios.json}"
RESULT_OUTPUT="${2:-modeling/experiments/results/final_validation_user_stability_result.json}"
SUMMARY_OUTPUT="${3:-modeling/experiments/results/final_validation_user_stability_summary.json}"
CSV_OUTPUT="${4:-modeling/experiments/results/final_validation_user_stability_summary.csv}"

export PYTHONPATH="modeling"

echo "[INFO] final validation analysis start"
echo "[INFO] project root: $PROJECT_ROOT"
echo "[INFO] result input: $RESULT_OUTPUT"
echo "[INFO] summary output: $SUMMARY_OUTPUT"
echo "[INFO] csv output: $CSV_OUTPUT"

python modeling/experiments/pipelines/run_final_validation_pipeline.py \
  --scenario-file "$SCENARIO_FILE" \
  --result-output "$RESULT_OUTPUT" \
  --summary-output "$SUMMARY_OUTPUT" \
  --csv-output "$CSV_OUTPUT" \
  --skip-run

echo "[INFO] final validation analysis done"
