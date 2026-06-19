import argparse
import csv
import json
import os
import subprocess
import sys
import time
from itertools import product
from pathlib import Path


DEFAULT_SCENARIO_FILE = (
    "ai/modeling/experiments/scenarios/"
    "style_validation_user_stability_scenarios.json"
)

DEFAULT_OUTPUT_DIR = (
    "ai/modeling/experiments/results/grid_search_optimizer_tuning"
)


PARAM_GRID = {
    "repeat_penalty_weight": [3500, 4500, 6000],
    "repeat_penalty_growth": ["quadratic"],
    "protein_bonus_weight": [150, 180, 220],
    "protein_bonus_cap_grams": [35],
    "difficulty_bonus_weight": [50, 80, 120],
}


METRIC_KEYS = [
    "scenario_count",
    "success_count",
    "fail_count",
    "success_rate",
    "solver_success_rate",
    "meal_coverage_rate",
    "validation_fail_count",
    "validation_warning_count",
    "duplicate_warning_count",
    "unique_menu_ratio",
    "duplicate_rate",
    "avg_runtime_ms",
    "p95_runtime_ms",
    "rag_mapping_success_rate",
    "rag_quality_issue_rate",
]


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_param_grid(
    param_grid_file: str | None = None,
    param_grid_json: str | None = None,
) -> dict:
    """
    optimizer tuning search space를 로드한다.

    기본값은 PARAM_GRID를 사용하고,
    특정 시나리오 튜닝이 필요한 경우 JSON 파일 또는 JSON 문자열로
    search space를 주입할 수 있다.
    """

    if param_grid_file and param_grid_json:
        raise ValueError("param_grid_file and param_grid_json cannot be used together")

    if param_grid_file:
        return read_json(Path(param_grid_file))

    if param_grid_json:
        return json.loads(param_grid_json)

    return PARAM_GRID


def build_grid_cases(
    param_grid: dict | None = None,
    max_cases: int | None = None,
) -> list[dict]:
    grid = param_grid or PARAM_GRID
    keys = list(grid.keys())
    values = [grid[key] for key in keys]

    cases = []

    for index, combination in enumerate(product(*values), start=1):
        config = dict(zip(keys, combination))

        cases.append({
            "case_id": f"grid_{index:04d}",
            "config": config,
        })

    if max_cases is not None:
        return cases[:max_cases]

    return cases


def extract_metrics(summary_path: Path) -> dict:
    if not summary_path.exists():
        return {}

    data = read_json(summary_path)
    summary = data.get("summary", {})

    return {
        key: summary.get(key)
        for key in METRIC_KEYS
    }


def collect_failure_reasons(result_path: Path) -> dict:
    """
    result 파일 내부의 시나리오 실패 원인을 수집한다.

    subprocess가 정상 종료되어도 내부 시나리오가 RAG API 장애 등으로
    실패할 수 있으므로, optimizer 성능 비교와 인프라 장애를 분리한다.
    """

    if not result_path.exists():
        return {
            "failure_type": "missing_result_file",
            "failure_reason_count": {
                "missing_result_file": 1,
            },
        }

    data = read_json(result_path)

    failure_reason_count: dict[str, int] = {}

    for result in data.get("results", []):
        if result.get("success"):
            continue

        error = result.get("error") or {}

        reason = (
            result.get("failure_reason")
            or error.get("failure_reason")
            or error.get("type")
            or "unknown"
        )

        failure_reason_count[reason] = (
            failure_reason_count.get(reason, 0) + 1
        )

    if not failure_reason_count:
        return {
            "failure_type": None,
            "failure_reason_count": {},
        }

    if (
        "rag_http_error" in failure_reason_count
        or "RagRequestError" in failure_reason_count
    ):
        failure_type = "rag_api"
    elif "missing_result_file" in failure_reason_count:
        failure_type = "missing_result_file"
    else:
        failure_type = "experiment"

    return {
        "failure_type": failure_type,
        "failure_reason_count": failure_reason_count,
    }


def is_experiment_successful(metrics: dict, failure_info: dict) -> bool:
    """
    실험 비교 대상으로 쓸 수 있는지 판단한다.

    validation_fail_count는 모델 품질 지표이므로 여기서는 실패 기준으로 보지 않는다.
    반면 success_rate, solver_success_rate, meal_coverage_rate가 깨지거나
    RAG API 장애가 있으면 optimizer 튜닝 비교 대상에서 제외한다.
    """

    if failure_info.get("failure_type") is not None:
        return False

    return (
        metrics.get("success_rate") == 1.0
        and metrics.get("solver_success_rate") == 1.0
        and metrics.get("meal_coverage_rate") == 1.0
    )


def calculate_objective_score(metrics: dict, ranking_eligible: bool) -> float:
    """
    optimizer tuning 목적 점수.

    점수 설계 의도:
    - solver / coverage 안정성은 전제 조건으로 보고, 깨지면 랭킹 제외
    - validation fail을 가장 크게 감점
    - warning, duplicate warning은 보조 감점
    - unique_menu_ratio는 다양성 개선으로 가산
    - duplicate_rate는 반복 메뉴 비율이므로 감점
    """

    if not ranking_eligible:
        return 0.0

    validation_fail_count = metrics.get("validation_fail_count") or 0
    validation_warning_count = metrics.get("validation_warning_count") or 0
    duplicate_warning_count = metrics.get("duplicate_warning_count") or 0
    unique_menu_ratio = metrics.get("unique_menu_ratio") or 0
    duplicate_rate = metrics.get("duplicate_rate") or 0

    score = 1000.0

    score -= validation_fail_count * 250
    score -= validation_warning_count * 30
    score -= duplicate_warning_count * 20
    score += unique_menu_ratio * 500
    score -= duplicate_rate * 300

    return round(score, 2)


def run_validation_case(
    case_id: str,
    config: dict,
    scenario_file: str,
    output_dir: Path,
    python_executable: str,
) -> dict:
    result_output = output_dir / f"{case_id}_result.json"
    summary_output = output_dir / f"{case_id}_summary.json"
    csv_output = output_dir / f"{case_id}_summary.csv"

    env = os.environ.copy()
    env["PYTHONPATH"] = "ai/modeling"
    env["OPTIMIZER_TUNING_OVERRIDE_JSON"] = json.dumps(
        config,
        ensure_ascii=False,
    )

    command = [
        python_executable,
        "ai/modeling/experiments/run_final_validation_pipeline.py",
        "--scenario-file",
        scenario_file,
        "--result-output",
        str(result_output),
        "--summary-output",
        str(summary_output),
        "--csv-output",
        str(csv_output),
    ]

    started_at = time.time()

    completed = subprocess.run(
        command,
        env=env,
        text=True,
        capture_output=True,
    )

    elapsed_seconds = round(time.time() - started_at, 2)

    metrics = extract_metrics(summary_output)
    failure_info = collect_failure_reasons(result_output)

    run_success = completed.returncode == 0
    experiment_success = is_experiment_successful(
        metrics=metrics,
        failure_info=failure_info,
    )

    ranking_eligible = run_success and experiment_success

    objective_score = calculate_objective_score(
        metrics=metrics,
        ranking_eligible=ranking_eligible,
    )

    record = {
        "case_id": case_id,
        "config": config,
        "run_success": run_success,
        "experiment_success": experiment_success,
        "ranking_eligible": ranking_eligible,
        "failure_type": failure_info.get("failure_type"),
        "failure_reason_count": failure_info.get("failure_reason_count"),
        "objective_score": objective_score,
        "metrics": metrics,
        "elapsed_seconds": elapsed_seconds,
        "result_output": str(result_output),
        "summary_output": str(summary_output),
        "csv_output": str(csv_output),
        "returncode": completed.returncode,
        "stderr_tail": completed.stderr[-3000:],
    }

    return record


def write_csv(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "case_id",
        "run_success",
        "experiment_success",
        "ranking_eligible",
        "failure_type",
        "objective_score",
        "elapsed_seconds",
        "result_output",
        "summary_output",
    ]

    config_keys = sorted({
        key
        for record in records
        for key in (record.get("config") or {}).keys()
    })

    metric_keys = sorted({
        key
        for record in records
        for key in (record.get("metrics") or {}).keys()
    })

    fieldnames.extend(f"config.{key}" for key in config_keys)
    fieldnames.extend(f"metric.{key}" for key in metric_keys)
    fieldnames.append("failure_reason_count")

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for record in records:
            row = {
                "case_id": record.get("case_id"),
                "run_success": record.get("run_success"),
                "experiment_success": record.get("experiment_success"),
                "ranking_eligible": record.get("ranking_eligible"),
                "failure_type": record.get("failure_type"),
                "objective_score": record.get("objective_score"),
                "elapsed_seconds": record.get("elapsed_seconds"),
                "result_output": record.get("result_output"),
                "summary_output": record.get("summary_output"),
                "failure_reason_count": json.dumps(
                    record.get("failure_reason_count") or {},
                    ensure_ascii=False,
                ),
            }

            for key in config_keys:
                row[f"config.{key}"] = (record.get("config") or {}).get(key)

            for key in metric_keys:
                row[f"metric.{key}"] = (record.get("metrics") or {}).get(key)

            writer.writerow(row)


def print_ranking(records: list[dict], top_k: int) -> None:
    eligible_records = [
        record
        for record in records
        if record.get("ranking_eligible")
    ]

    ranked = sorted(
        eligible_records,
        key=lambda record: record.get("objective_score", 0),
        reverse=True,
    )

    print()
    print("=" * 100)
    print("[GRID SEARCH RANKING - ELIGIBLE ONLY]")
    print("=" * 100)

    if not ranked:
        print("No eligible records.")
    else:
        for rank, record in enumerate(ranked[:top_k], start=1):
            print()
            print("-" * 100)
            print("rank:", rank)
            print("case_id:", record.get("case_id"))
            print("objective_score:", record.get("objective_score"))
            print("config:", record.get("config"))
            print("metrics:", record.get("metrics"))
            print("summary_output:", record.get("summary_output"))

    excluded_records = [
        record
        for record in records
        if not record.get("ranking_eligible")
    ]

    if excluded_records:
        print()
        print("=" * 100)
        print("[EXCLUDED CASES]")
        print("=" * 100)

        for record in excluded_records:
            print()
            print("-" * 100)
            print("case_id:", record.get("case_id"))
            print("run_success:", record.get("run_success"))
            print("experiment_success:", record.get("experiment_success"))
            print("failure_type:", record.get("failure_type"))
            print("failure_reason_count:", record.get("failure_reason_count"))
            print("metrics:", record.get("metrics"))
            print("config:", record.get("config"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario-file", default=DEFAULT_SCENARIO_FILE)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument(
        "--param-grid-file",
        default=None,
        help="optimizer tuning parameter grid JSON file path",
    )
    parser.add_argument(
        "--param-grid-json",
        default=None,
        help="optimizer tuning parameter grid JSON string",
    )
    args = parser.parse_args()

    scenario_file = args.scenario_file
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    param_grid = load_param_grid(
        param_grid_file=args.param_grid_file,
        param_grid_json=args.param_grid_json,
    )

    cases = build_grid_cases(
        param_grid=param_grid,
        max_cases=args.max_cases,
    )

    records = []

    print("=" * 100)
    print("[GRID SEARCH OPTIMIZER TUNING START]")
    print("=" * 100)
    print("scenario_file:", scenario_file)
    print("output_dir:", output_dir)
    print("param_grid:", param_grid)
    print("case_count:", len(cases))

    for index, case in enumerate(cases, start=1):
        case_id = case["case_id"]
        config = case["config"]

        print()
        print("=" * 100)
        print(f"[{index}/{len(cases)}] {case_id}")
        print("=" * 100)
        print("config:", config)

        record = run_validation_case(
            case_id=case_id,
            config=config,
            scenario_file=scenario_file,
            output_dir=output_dir,
            python_executable=sys.executable,
        )

        records.append(record)

        write_json(output_dir / "grid_search_records.json", records)
        write_csv(output_dir / "grid_search_summary.csv", records)

        print("run_success:", record.get("run_success"))
        print("experiment_success:", record.get("experiment_success"))
        print("ranking_eligible:", record.get("ranking_eligible"))
        print("failure_type:", record.get("failure_type"))
        print("failure_reason_count:", record.get("failure_reason_count"))
        print("objective_score:", record.get("objective_score"))
        print("metrics:", record.get("metrics"))
        print("elapsed_seconds:", record.get("elapsed_seconds"))

        if not record.get("run_success"):
            print("stderr_tail:", record.get("stderr_tail"))

    print_ranking(records, top_k=args.top_k)

    print()
    print("[INFO] grid search finished.")
    print("[INFO] records:", output_dir / "grid_search_records.json")
    print("[INFO] csv:", output_dir / "grid_search_summary.csv")


if __name__ == "__main__":
    main()
