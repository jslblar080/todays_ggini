import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_SCENARIO_FILE = (
    "modeling/experiments/scenarios/style_validation_user_stability_scenarios.json"
)


def parse_json_object(raw: str | None) -> dict:
    if not raw:
        return {}

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid JSON passed to --override-json: {error}") from error

    if not isinstance(data, dict):
        raise SystemExit("--override-json must be a JSON object")

    return data


def build_override_config(args: argparse.Namespace) -> dict:
    override = parse_json_object(args.override_json)

    cli_values = {
        "repeat_penalty_weight": args.repeat_penalty_weight,
        "protein_bonus_weight": args.protein_bonus_weight,
        "difficulty_bonus_weight": args.difficulty_bonus_weight,
        "repeat_penalty_growth": args.repeat_penalty_growth,
        "protein_bonus_cap_grams": args.protein_bonus_cap_grams,
    }

    for key, value in cli_values.items():
        if value is not None:
            override[key] = value

    return override


def ensure_outputs_do_not_exist(paths: list[Path], force: bool) -> None:
    existing = [path for path in paths if path.exists()]

    if existing and not force:
        lines = "\n".join(f"- {path}" for path in existing)
        raise SystemExit(
            "Output files already exist. Use --force to overwrite.\n"
            f"{lines}"
        )


def load_summary(summary_output: Path) -> dict:
    if not summary_output.exists():
        return {}

    data = json.loads(summary_output.read_text(encoding="utf-8"))
    return data.get("summary", {})


def write_metadata(path: Path, metadata: dict) -> None:
    path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Optimizer config override를 적용한 full validation pipeline을 실행한다. "
            "결과 파일명을 자동 지정하고 run metadata를 저장한다."
        )
    )

    parser.add_argument(
        "--scenario-file",
        default=DEFAULT_SCENARIO_FILE,
        help="실행할 validation scenario JSON 경로",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="result, summary, csv, metadata를 저장할 디렉터리",
    )
    parser.add_argument(
        "--run-name",
        required=True,
        help="출력 파일 prefix. 예: replay_0061_rag_full_validation",
    )
    parser.add_argument(
        "--override-json",
        default=None,
        help="OPTIMIZER_TUNING_OVERRIDE_JSON으로 전달할 JSON object 문자열",
    )
    parser.add_argument("--repeat-penalty-weight", type=int, default=None)
    parser.add_argument("--protein-bonus-weight", type=int, default=None)
    parser.add_argument("--difficulty-bonus-weight", type=int, default=None)
    parser.add_argument("--repeat-penalty-growth", default=None)
    parser.add_argument("--protein-bonus-cap-grams", type=int, default=None)
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="validation 실행은 생략하고 기존 result 파일을 분석한다.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="기존 output 파일이 있어도 덮어쓴다.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 실행하지 않고 command와 metadata만 출력한다.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result_output = output_dir / f"{args.run_name}_result.json"
    summary_output = output_dir / f"{args.run_name}_summary.json"
    csv_output = output_dir / f"{args.run_name}_summary.csv"
    metadata_output = output_dir / f"{args.run_name}_metadata.json"

    output_paths = [
        result_output,
        summary_output,
        csv_output,
        metadata_output,
    ]
    ensure_outputs_do_not_exist(output_paths, args.force)

    override_config = build_override_config(args)

    command = [
        sys.executable,
        "modeling/experiments/pipelines/run_final_validation_pipeline.py",
        "--scenario-file",
        args.scenario_file,
        "--result-output",
        str(result_output),
        "--summary-output",
        str(summary_output),
        "--csv-output",
        str(csv_output),
    ]

    if args.skip_run:
        command.append("--skip-run")

    env = os.environ.copy()

    if override_config:
        env["OPTIMIZER_TUNING_OVERRIDE_JSON"] = json.dumps(
            override_config,
            ensure_ascii=False,
        )

    metadata = {
        "run_name": args.run_name,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "scenario_file": args.scenario_file,
        "output_dir": str(output_dir),
        "result_output": str(result_output),
        "summary_output": str(summary_output),
        "csv_output": str(csv_output),
        "metadata_output": str(metadata_output),
        "optimizer_tuning_override": override_config,
        "command": command,
        "status": "dry_run" if args.dry_run else "running",
    }

    print("[PIPELINE] command:")
    print(" ".join(command))
    print()
    print("[PIPELINE] override:")
    print(json.dumps(override_config, ensure_ascii=False, indent=2))

    if args.dry_run:
        write_metadata(metadata_output, metadata)
        print(f"[PIPELINE] dry-run metadata saved: {metadata_output}")
        return

    write_metadata(metadata_output, metadata)

    try:
        subprocess.run(command, env=env, check=True)
    except subprocess.CalledProcessError as error:
        metadata["status"] = "failed"
        metadata["finished_at"] = datetime.now(timezone.utc).isoformat()
        metadata["returncode"] = error.returncode
        write_metadata(metadata_output, metadata)
        raise SystemExit(error.returncode) from error

    summary = load_summary(summary_output)

    metadata["status"] = "success"
    metadata["finished_at"] = datetime.now(timezone.utc).isoformat()
    metadata["summary"] = {
        "scenario_count": summary.get("scenario_count"),
        "success_count": summary.get("success_count"),
        "fail_count": summary.get("fail_count"),
        "success_rate": summary.get("success_rate"),
        "validation_status_count": summary.get("validation_status_count"),
        "validation_fail_count": summary.get("validation_fail_count"),
        "validation_warning_count": summary.get("validation_warning_count"),
        "solver_success_rate": summary.get("solver_success_rate"),
        "meal_coverage_rate": summary.get("meal_coverage_rate"),
        "unique_menu_ratio": summary.get("unique_menu_ratio"),
        "duplicate_rate": summary.get("duplicate_rate"),
        "rag_mapping_success_rate": summary.get("rag_mapping_success_rate"),
        "rag_quality_issue_rate": summary.get("rag_quality_issue_rate"),
    }
    write_metadata(metadata_output, metadata)

    print()
    print("[PIPELINE] metadata saved:")
    print(metadata_output)


if __name__ == "__main__":
    main()
