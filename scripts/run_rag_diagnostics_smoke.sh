#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

SCENARIO_FILE="${1:-ai/modeling/experiments/scenarios/style_validation_user_stability_scenarios.json}"
RESULT_OUTPUT="${2:-ai/modeling/experiments/results/rag_diagnostics_smoke_result.json}"

export PYTHONPATH="ai/modeling"
export RAG_DIAGNOSTICS_RESULT_OUTPUT="$RESULT_OUTPUT"

echo "[INFO] RAG diagnostics smoke test start"
echo "[INFO] project root: $PROJECT_ROOT"
echo "[INFO] scenario file: $SCENARIO_FILE"
echo "[INFO] result output: $RESULT_OUTPUT"

python -m py_compile \
  ai/modeling/services/rag/rag_response_mapper.py \
  ai/modeling/experiments/runners/run_baseline_mmr.py \
  ai/modeling/services/modeling_service.py

python ai/modeling/experiments/runners/run_baseline_mmr.py \
  --scenario-file "$SCENARIO_FILE" \
  --output "$RESULT_OUTPUT"

python - <<'PY'
import json
import os
from pathlib import Path

path = Path(os.environ["RAG_DIAGNOSTICS_RESULT_OUTPUT"])
data = json.loads(path.read_text(encoding="utf-8"))

print()
print("=" * 80)
print("[RAG DIAGNOSTICS SMOKE SUMMARY]")
print("=" * 80)

for result in data.get("results", []):
    rag_mapping = (
        result.get("diagnostics", {})
        .get("rag_mapping", {})
    )

    print()
    print("scenario_id:", result.get("scenario_id"))
    print("success:", result.get("success"))
    print("event_count:", rag_mapping.get("event_count"))
    print("raw_menus:", rag_mapping.get("raw_menus"))
    print("mapped_menus:", rag_mapping.get("mapped_menus"))
    print("excluded_menus:", rag_mapping.get("excluded_menus"))
    print("quality_issue_menus:", rag_mapping.get("quality_issue_menus"))
    print("mapping_success_rate:", rag_mapping.get("mapping_success_rate"))
    print("quality_issue_rate:", rag_mapping.get("quality_issue_rate"))
    print("quality_issue_type_count:")
    for issue, count in (rag_mapping.get("quality_issue_type_count") or {}).items():
        print(f"  - {issue}: {count}")

    print("ingredient_group_mapping_status_count:")
    for status, count in (
        rag_mapping.get("ingredient_group_mapping_status_count") or {}
    ).items():
        print(f"  - {status}: {count}")

    print("quality_issue_examples:")
    for issue, examples in (rag_mapping.get("quality_issue_examples") or {}).items():
        print(f"  - {issue}:")
        for example in examples[:2]:
            print(
                "    *",
                example.get("menu_id"),
                example.get("name"),
                {
                    "ingredients_count": example.get("ingredients_count"),
                    "ingredient_groups_count": example.get("ingredient_groups_count"),
                    "ingredient_usages_count": example.get("ingredient_usages_count"),
                    "protein": example.get("protein"),
                },
            )

print()
print("[INFO] RAG diagnostics smoke summary finished.")
PY

echo "[INFO] RAG diagnostics smoke test done"
