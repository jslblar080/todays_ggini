import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_SCENARIO_FILE = (
    "ai/modeling/experiments/scenarios/style_validation_user_stability_scenarios.json"
)


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def ensure_outputs_do_not_exist(paths: list[Path], force: bool) -> None:
    existing = [path for path in paths if path.exists()]

    if existing and not force:
        lines = "\n".join(f"- {path}" for path in existing)
        raise SystemExit(
            "Output files already exist. Use --force to overwrite.\n"
            f"{lines}"
        )


def run_command(command: list[str]) -> None:
    print()
    print("[COMMAND]", " ".join(command))
    subprocess.run(command, check=True)


def build_full_validation_command(args: argparse.Namespace, full_output_dir: Path) -> list[str]:
    command = [
        sys.executable,
        "ai/modeling/experiments/pipelines/run_optimizer_full_validation.py",
        "--scenario-file",
        args.scenario_file,
        "--run-name",
        args.run_name,
        "--output-dir",
        str(full_output_dir),
    ]

    if args.override_json:
        command.extend(["--override-json", args.override_json])

    cli_options = {
        "--repeat-penalty-weight": args.repeat_penalty_weight,
        "--protein-bonus-weight": args.protein_bonus_weight,
        "--difficulty-bonus-weight": args.difficulty_bonus_weight,
        "--repeat-penalty-growth": args.repeat_penalty_growth,
        "--protein-bonus-cap-grams": args.protein_bonus_cap_grams,
    }

    for option, value in cli_options.items():
        if value is not None:
            command.extend([option, str(value)])

    if args.force:
        command.append("--force")

    return command


def build_extract_command(result_output: Path, snapshot_output: Path) -> list[str]:
    return [
        sys.executable,
        "ai/modeling/experiments/tuning/extract_optimizer_snapshots.py",
        "--input",
        str(result_output),
        "--output",
        str(snapshot_output),
    ]


def build_replay_command(
    snapshot_file: Path,
    replay_output_dir: Path,
    max_cases: int | None,
    top_k: int,
) -> list[str]:
    command = [
        sys.executable,
        "ai/modeling/experiments/tuning/replay_optimizer_snapshots.py",
        "--snapshot-file",
        str(snapshot_file),
        "--output-dir",
        str(replay_output_dir),
        "--top-k",
        str(top_k),
    ]

    if max_cases is not None:
        command.extend(["--max-cases", str(max_cases)])

    return command


def summarize_replay(records_path: Path, top_k: int) -> list[dict]:
    records = read_json(records_path)
    if not isinstance(records, list):
        return []

    ranked = sorted(
        records,
        key=lambda item: item.get("objective_score", float("-inf")),
        reverse=True,
    )

    top_records = []
    for record in ranked[:top_k]:
        metrics = record.get("metrics") or {}
        top_records.append({
            "case_id": record.get("case_id"),
            "objective_score": record.get("objective_score"),
            "config": record.get("config"),
            "scenario_count": metrics.get("scenario_count"),
            "solver_success_rate": metrics.get("solver_success_rate"),
            "validation_status_count": metrics.get("validation_status_count"),
            "validation_fail_count": metrics.get("validation_fail_count"),
            "validation_warning_count": metrics.get("validation_warning_count"),
            "avg_unique_menu_ratio": metrics.get("avg_unique_menu_ratio"),
            "avg_duplicate_rate": metrics.get("avg_duplicate_rate"),
        })

    return top_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Full validation, optimizer snapshot extraction, snapshot replay를 "
            "하나의 pipeline으로 실행한다."
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
        help="pipeline 실행 결과를 저장할 디렉터리",
    )
    parser.add_argument(
        "--run-name",
        required=True,
        help="출력 파일 prefix",
    )
    parser.add_argument(
        "--override-json",
        default=None,
        help="full validation에 적용할 optimizer override JSON object 문자열",
    )
    parser.add_argument("--repeat-penalty-weight", type=int, default=None)
    parser.add_argument("--protein-bonus-weight", type=int, default=None)
    parser.add_argument("--difficulty-bonus-weight", type=int, default=None)
    parser.add_argument("--repeat-penalty-growth", default=None)
    parser.add_argument("--protein-bonus-cap-grams", type=int, default=None)
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    output_dir = Path(args.output_dir)
    full_output_dir = output_dir / "full_validation"
    snapshot_output_dir = output_dir / "snapshots"
    replay_output_dir = output_dir / "snapshot_replay"

    full_output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_output_dir.mkdir(parents=True, exist_ok=True)
    replay_output_dir.mkdir(parents=True, exist_ok=True)

    result_output = full_output_dir / f"{args.run_name}_result.json"
    summary_output = full_output_dir / f"{args.run_name}_summary.json"
    csv_output = full_output_dir / f"{args.run_name}_summary.csv"
    full_metadata_output = full_output_dir / f"{args.run_name}_metadata.json"

    snapshot_output = snapshot_output_dir / f"{args.run_name}_snapshots.json"

    replay_records_output = replay_output_dir / "snapshot_replay_records.json"
    replay_csv_output = replay_output_dir / "snapshot_replay_summary.csv"

    pipeline_metadata_output = output_dir / f"{args.run_name}_pipeline_metadata.json"

    ensure_outputs_do_not_exist(
        [
            result_output,
            summary_output,
            csv_output,
            full_metadata_output,
            snapshot_output,
            replay_records_output,
            replay_csv_output,
            pipeline_metadata_output,
        ],
        force=args.force,
    )

    full_validation_command = build_full_validation_command(args, full_output_dir)
    extract_command = build_extract_command(result_output, snapshot_output)
    replay_command = build_replay_command(
        snapshot_file=snapshot_output,
        replay_output_dir=replay_output_dir,
        max_cases=args.max_cases,
        top_k=args.top_k,
    )

    metadata = {
        "run_name": args.run_name,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "scenario_file": args.scenario_file,
        "output_dir": str(output_dir),
        "full_validation": {
            "result_output": str(result_output),
            "summary_output": str(summary_output),
            "csv_output": str(csv_output),
            "metadata_output": str(full_metadata_output),
        },
        "snapshot_extraction": {
            "snapshot_output": str(snapshot_output),
        },
        "snapshot_replay": {
            "output_dir": str(replay_output_dir),
            "records_output": str(replay_records_output),
            "csv_output": str(replay_csv_output),
            "top_k": args.top_k,
            "max_cases": args.max_cases,
        },
        "commands": {
            "full_validation": full_validation_command,
            "snapshot_extraction": extract_command,
            "snapshot_replay": replay_command,
        },
        "status": "dry_run" if args.dry_run else "running",
    }

    print("[PIPELINE] full validation command:")
    print(" ".join(full_validation_command))
    print()
    print("[PIPELINE] snapshot extraction command:")
    print(" ".join(extract_command))
    print()
    print("[PIPELINE] snapshot replay command:")
    print(" ".join(replay_command))

    if args.dry_run:
        print()
        print("[PIPELINE] dry-run only. No files were written.")
        return

    write_json(pipeline_metadata_output, metadata)

    try:
        run_command(full_validation_command)
        run_command(extract_command)
        run_command(replay_command)
    except subprocess.CalledProcessError as error:
        metadata["status"] = "failed"
        metadata["finished_at"] = datetime.now(timezone.utc).isoformat()
        metadata["returncode"] = error.returncode
        write_json(pipeline_metadata_output, metadata)
        raise SystemExit(error.returncode) from error

    full_summary_data = read_json(summary_output)
    full_summary = full_summary_data.get("summary", {})

    snapshot_data = read_json(snapshot_output)

    metadata["status"] = "success"
    metadata["finished_at"] = datetime.now(timezone.utc).isoformat()
    metadata["full_validation_summary"] = {
        "scenario_count": full_summary.get("scenario_count"),
        "success_count": full_summary.get("success_count"),
        "fail_count": full_summary.get("fail_count"),
        "success_rate": full_summary.get("success_rate"),
        "validation_status_count": full_summary.get("validation_status_count"),
        "validation_fail_count": full_summary.get("validation_fail_count"),
        "validation_warning_count": full_summary.get("validation_warning_count"),
        "solver_success_rate": full_summary.get("solver_success_rate"),
        "meal_coverage_rate": full_summary.get("meal_coverage_rate"),
        "unique_menu_ratio": full_summary.get("unique_menu_ratio"),
        "duplicate_rate": full_summary.get("duplicate_rate"),
        "rag_mapping_success_rate": full_summary.get("rag_mapping_success_rate"),
        "rag_quality_issue_rate": full_summary.get("rag_quality_issue_rate"),
    }
    metadata["snapshot_summary"] = {
        "total_result_count": snapshot_data.get("total_result_count"),
        "snapshot_count": snapshot_data.get("snapshot_count"),
        "missing_snapshot_count": snapshot_data.get("missing_snapshot_count"),
    }
    metadata["snapshot_replay_top_records"] = summarize_replay(
        replay_records_output,
        top_k=args.top_k,
    )

    write_json(pipeline_metadata_output, metadata)

    print()
    print("[PIPELINE] pipeline finished.")
    print(f"[PIPELINE] metadata: {pipeline_metadata_output}")


if __name__ == "__main__":
    main()
