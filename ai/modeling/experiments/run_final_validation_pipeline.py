import argparse
import json
import subprocess
import sys
from pathlib import Path


DEFAULT_SCENARIO_FILE = (
    "ai/modeling/experiments/scenarios/style_validation_user_stability_scenarios.json"
)
DEFAULT_RESULT_OUTPUT = (
    "ai/modeling/experiments/results/final_validation_result.json"
)
DEFAULT_SUMMARY_OUTPUT = (
    "ai/modeling/experiments/results/final_validation_summary.json"
)
DEFAULT_CSV_OUTPUT = (
    "ai/modeling/experiments/results/final_validation_summary.csv"
)


def run_command(command: list[str]) -> None:
    """
    하위 실험/분석 스크립트를 실행한다.
    실패 시 즉시 중단하여 잘못된 결과 파일이 후속 단계로 전달되지 않도록 한다.
    """

    print()
    print("[COMMAND]", " ".join(command))

    result = subprocess.run(command)

    if result.returncode != 0:
        raise SystemExit(result.returncode)


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def print_summary(summary_path: str) -> None:
    """
    최종 validation summary 핵심 지표를 터미널에 출력한다.
    """

    data = load_json(summary_path)
    summary = data.get("summary", {})

    print()
    print("=" * 80)
    print("[FINAL VALIDATION SUMMARY]")
    print("=" * 80)

    keys = [
        "scenario_count",
        "success_count",
        "fail_count",
        "success_rate",
        "error_rate",
        "avg_runtime_ms",
        "p95_runtime_ms",
        "p99_runtime_ms",
        "max_runtime_ms",
        "validation_status_count",
        "solver_status_count",
        "required_meal_count",
        "selected_menu_count",
        "meal_coverage_rate",
        "available_recommendation_count",
        "candidate_to_required_ratio",
        "unique_menu_count",
        "duplicate_menu_count",
        "unique_menu_ratio",
        "duplicate_rate",
        "rag_mapping_event_count",
        "rag_raw_menus",
        "rag_mapped_menus",
        "rag_excluded_menus",
        "rag_quality_issue_menus",
        "rag_mapping_success_rate",
        "rag_quality_issue_rate",
        "secondary_warning_type_count",
        "secondary_warning_level_count",
        "failure_reason_count",
    ]

    for key in keys:
        print(f"{key}: {summary.get(key)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "월간 식단 최종 validation 실험 실행과 분석을 한 번에 수행한다."
        )
    )

    parser.add_argument(
        "--scenario-file",
        default=DEFAULT_SCENARIO_FILE,
        help="실행할 validation 시나리오 JSON 경로",
    )
    parser.add_argument(
        "--result-output",
        default=DEFAULT_RESULT_OUTPUT,
        help="실험 실행 결과 JSON 출력 경로",
    )
    parser.add_argument(
        "--summary-output",
        default=DEFAULT_SUMMARY_OUTPUT,
        help="최종 validation summary JSON 출력 경로",
    )
    parser.add_argument(
        "--csv-output",
        default=DEFAULT_CSV_OUTPUT,
        help="최종 validation row CSV 출력 경로",
    )
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="실험 실행은 생략하고 기존 result-output 파일을 분석한다.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.skip_run:
        run_command([
            sys.executable,
            "ai/modeling/experiments/run_baseline_mmr_test.py",
            "--scenario-file",
            args.scenario_file,
            "--output",
            args.result_output,
        ])
    else:
        print("[INFO] skip-run enabled. Use existing result file.")
        print(f"[INFO] result input: {args.result_output}")

    run_command([
        sys.executable,
        "ai/modeling/experiments/analysis/analyze_final_validation_result.py",
        "--input",
        args.result_output,
        "--output-json",
        args.summary_output,
        "--output-csv",
        args.csv_output,
    ])

    print_summary(args.summary_output)

    print()
    print("[INFO] final validation pipeline finished.")
    print(f"[INFO] scenario file: {args.scenario_file}")
    print(f"[INFO] result output: {args.result_output}")
    print(f"[INFO] summary output: {args.summary_output}")
    print(f"[INFO] csv output: {args.csv_output}")


if __name__ == "__main__":
    main()
