import argparse
import csv
import itertools
import json
import time
from collections import Counter
from pathlib import Path

from services.optimizer.ortools.monthly_plan_optimizer import (
    solve_monthly_plan_with_ortools,
)
from services.optimizer.ortools.result_mapper import build_ortools_monthly_plan
from services.plan.plan_validation_service import (
    build_style_validation,
    enrich_style_validation,
)


GRID = {
    "repeat_penalty_weight": [2500, 3500, 4500, 6000],
    "protein_bonus_weight": [0, 150, 180, 220],
    "difficulty_bonus_weight": [0, 50, 80, 120],
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        return

    fieldnames = [
        "case_id",
        "ranking_eligible",
        "objective_score",
        "scenario_count",
        "solver_success_count",
        "solver_success_rate",
        "validation_fail_count",
        "validation_warning_count",
        "validation_pass_count",
        "duplicate_warning_count",
        "avg_unique_menu_ratio",
        "avg_duplicate_rate",
        "avg_allowed_duplicate_rate",
        "avg_duplicate_excess_rate",
        "avg_runtime_ms",
        "repeat_penalty_weight",
        "protein_bonus_weight",
        "difficulty_bonus_weight",
    ]

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            config = row.get("config", {})
            metrics = row.get("metrics", {})

            writer.writerow({
                "case_id": row.get("case_id"),
                "ranking_eligible": row.get("ranking_eligible"),
                "objective_score": row.get("objective_score"),
                "scenario_count": metrics.get("scenario_count"),
                "solver_success_count": metrics.get("solver_success_count"),
                "solver_success_rate": metrics.get("solver_success_rate"),
                "validation_fail_count": metrics.get("validation_fail_count"),
                "validation_warning_count": metrics.get("validation_warning_count"),
                "validation_pass_count": metrics.get("validation_pass_count"),
                "duplicate_warning_count": metrics.get("duplicate_warning_count"),
                "avg_unique_menu_ratio": metrics.get("avg_unique_menu_ratio"),
                "avg_duplicate_rate": metrics.get("avg_duplicate_rate"),
                "avg_allowed_duplicate_rate": metrics.get("avg_allowed_duplicate_rate"),
                "avg_duplicate_excess_rate": metrics.get("avg_duplicate_excess_rate"),
                "avg_runtime_ms": metrics.get("avg_runtime_ms"),
                "repeat_penalty_weight": config.get("repeat_penalty_weight"),
                "protein_bonus_weight": config.get("protein_bonus_weight"),
                "difficulty_bonus_weight": config.get("difficulty_bonus_weight"),
            })


def build_cases(max_cases: int | None = None) -> list[dict]:
    keys = list(GRID.keys())
    values = [GRID[key] for key in keys]

    cases = []

    for index, combination in enumerate(itertools.product(*values), start=1):
        config = dict(zip(keys, combination))

        cases.append({
            "case_id": f"replay_{index:04d}",
            "config": {
                **config,
                "repeat_penalty_growth": "quadratic",
            },
        })

    if max_cases:
        return cases[:max_cases]

    return cases


def apply_config(optimizer_input: dict, config: dict) -> dict:
    updated = json.loads(json.dumps(optimizer_input, ensure_ascii=False))

    for key, value in config.items():
        updated[key] = value

    optimizer_config = updated.get("optimizer_config") or {}

    for key, value in config.items():
        optimizer_config[key] = value

    updated["optimizer_config"] = optimizer_config

    return updated




def calculate_allowed_duplicate_rate(
    selected_menu_count: int,
    available_recommendation_count: int,
) -> float:
    """
    시나리오별 후보풀 여유도에 따라 허용 중복률을 다르게 계산한다.

    후보 메뉴가 충분하면 중복을 더 엄격하게 보고,
    후보 메뉴가 부족하면 현실적으로 중복을 더 허용한다.
    """

    if selected_menu_count <= 0:
        return 0.3

    candidate_ratio = available_recommendation_count / selected_menu_count

    if candidate_ratio >= 3.0:
        return 0.15

    if candidate_ratio >= 2.0:
        return 0.25

    if candidate_ratio >= 1.5:
        return 0.35

    return 0.45


def calculate_duplicate_excess_rate(
    duplicate_rate: float,
    allowed_duplicate_rate: float,
) -> float:
    """
    실제 중복률이 허용 중복률을 초과한 정도만 패널티 대상으로 계산한다.
    """

    return max(0.0, duplicate_rate - allowed_duplicate_rate)


def calculate_duplicate_warning(style_validation: dict) -> bool:
    secondary_warnings = style_validation.get("secondary_warnings") or []

    if not isinstance(secondary_warnings, list):
        return False

    for warning in secondary_warnings:
        if isinstance(warning, dict) and warning.get("type") == "duplicate_menu":
            return True

    return False


def evaluate_case(case_id: str, config: dict, snapshots: list[dict]) -> dict:
    scenario_records = []
    runtime_values = []

    for snapshot in snapshots:
        started_at = time.perf_counter()

        optimizer_input = apply_config(
            optimizer_input=snapshot["optimizer_input"],
            config=config,
        )

        optimizer_result = solve_monthly_plan_with_ortools(
            optimizer_input=optimizer_input,
        )

        runtime_ms = round((time.perf_counter() - started_at) * 1000, 2)
        runtime_values.append(runtime_ms)

        solver_status = optimizer_result.get("solver_status")
        solver_success = solver_status in ["OPTIMAL", "FEASIBLE"]

        if not solver_success:
            scenario_records.append({
                "scenario_id": snapshot.get("scenario_id"),
                "description": snapshot.get("description"),
                "solver_status": solver_status,
                "solver_success": False,
                "validation_status": "unknown",
                "runtime_ms": runtime_ms,
                "message": optimizer_result.get("message"),
            })
            continue

        monthly_plan = build_ortools_monthly_plan(
            optimizer_result=optimizer_result,
            optimizer_input=optimizer_input,
            recommendations=[],
            profile=snapshot.get("profile") or {},
        )

        summary = monthly_plan.get("summary", {})

        selected_menu_count = int(summary.get("selected_menu_count", 0) or 0)
        unique_menu_count = int(summary.get("unique_menu_count", 0) or 0)
        duplicate_menu_count = int(summary.get("duplicate_menu_count", 0) or 0)

        available_recommendation_count = int(
            optimizer_input.get("original_recommendation_count")
            or optimizer_input.get("used_optimizer_candidate_count")
            or len(optimizer_input.get("menus", []))
            or 0
        )

        if selected_menu_count > 0:
            summary["unique_menu_ratio"] = round(
                unique_menu_count / selected_menu_count,
                4,
            )
            summary["duplicate_rate"] = round(
                duplicate_menu_count / selected_menu_count,
                4,
            )

        summary["available_recommendation_count"] = available_recommendation_count

        allowed_duplicate_rate = calculate_allowed_duplicate_rate(
            selected_menu_count=selected_menu_count,
            available_recommendation_count=available_recommendation_count,
        )
        duplicate_excess_rate = calculate_duplicate_excess_rate(
            duplicate_rate=float(summary.get("duplicate_rate") or 0),
            allowed_duplicate_rate=allowed_duplicate_rate,
        )

        summary["allowed_duplicate_rate"] = round(allowed_duplicate_rate, 4)
        summary["duplicate_excess_rate"] = round(duplicate_excess_rate, 4)

        selected_style = snapshot.get("selected_style") or {}
        profile = snapshot.get("profile") or {}

        base_style_validation = build_style_validation(
            selected_style=selected_style,
            summary=summary,
            profile=profile,
        )

        style_validation = enrich_style_validation(
            style_validation=base_style_validation,
            selected_style=selected_style,
            summary=summary,
        )

        monthly_plan["style_validation"] = style_validation

        scenario_records.append({
            "scenario_id": snapshot.get("scenario_id"),
            "description": snapshot.get("description"),
            "solver_status": solver_status,
            "solver_success": True,
            "validation_status": style_validation.get("status"),
            "validation_message": style_validation.get("message"),
            "duplicate_warning": calculate_duplicate_warning(style_validation),
            "runtime_ms": runtime_ms,
            "summary": summary,
            "style_validation": style_validation,
        })

    metrics = summarize_records(scenario_records, runtime_values)

    objective_score = calculate_objective_score(metrics)

    return {
        "case_id": case_id,
        "config": config,
        "ranking_eligible": metrics["solver_success_rate"] == 1.0,
        "objective_score": objective_score,
        "metrics": metrics,
        "scenario_records": scenario_records,
        "rows": scenario_records,
    }


def summarize_records(records: list[dict], runtime_values: list[float]) -> dict:
    scenario_count = len(records)
    solver_success_count = sum(1 for row in records if row.get("solver_success"))

    status_counter = Counter(
        row.get("validation_status", "unknown")
        for row in records
    )

    duplicate_warning_count = sum(
        1 for row in records
        if row.get("duplicate_warning")
    )

    unique_ratios = []
    duplicate_rates = []
    duplicate_excess_rates = []
    allowed_duplicate_rates = []

    for row in records:
        summary = row.get("summary") or {}

        selected_menu_count = int(summary.get("selected_menu_count", 0) or 0)
        unique_menu_count = int(summary.get("unique_menu_count", 0) or 0)
        duplicate_menu_count = int(summary.get("duplicate_menu_count", 0) or 0)

        if selected_menu_count > 0:
            unique_ratio = unique_menu_count / selected_menu_count
            duplicate_rate = duplicate_menu_count / selected_menu_count

            unique_ratios.append(unique_ratio)
            duplicate_rates.append(duplicate_rate)

            if summary.get("allowed_duplicate_rate") is not None:
                allowed_duplicate_rates.append(
                    float(summary.get("allowed_duplicate_rate") or 0)
                )

            if summary.get("duplicate_excess_rate") is not None:
                duplicate_excess_rates.append(
                    float(summary.get("duplicate_excess_rate") or 0)
                )

            continue

        if summary.get("unique_menu_ratio") is not None:
            unique_ratios.append(float(summary.get("unique_menu_ratio") or 0))

        if summary.get("duplicate_rate") is not None:
            duplicate_rates.append(float(summary.get("duplicate_rate") or 0))

    return {
        "scenario_count": scenario_count,
        "solver_success_count": solver_success_count,
        "solver_success_rate": round(
            solver_success_count / scenario_count,
            4,
        ) if scenario_count else 0,
        "validation_status_count": dict(status_counter),
        "validation_pass_count": status_counter.get("pass", 0),
        "validation_warning_count": status_counter.get("warning", 0),
        "validation_fail_count": status_counter.get("fail", 0),
        "duplicate_warning_count": duplicate_warning_count,
        "avg_unique_menu_ratio": round(
            sum(unique_ratios) / len(unique_ratios),
            4,
        ) if unique_ratios else 0,
        "avg_duplicate_rate": round(
            sum(duplicate_rates) / len(duplicate_rates),
            4,
        ) if duplicate_rates else 0,
        "avg_allowed_duplicate_rate": round(
            sum(allowed_duplicate_rates) / len(allowed_duplicate_rates),
            4,
        ) if allowed_duplicate_rates else 0,
        "avg_duplicate_excess_rate": round(
            sum(duplicate_excess_rates) / len(duplicate_excess_rates),
            4,
        ) if duplicate_excess_rates else 0,
        "avg_runtime_ms": round(
            sum(runtime_values) / len(runtime_values),
            2,
        ) if runtime_values else 0,
    }


def calculate_objective_score(metrics: dict) -> float:
    """
    튜닝용 목적 점수.

    우선순위:
    1. solver가 모든 시나리오에서 성공해야 함
    2. validation fail을 가장 강하게 줄임
    3. warning과 duplicate warning을 줄임
    4. unique menu ratio를 높임
    5. 시나리오별 허용 중복률을 초과한 중복만 감점
    """

    if metrics.get("solver_success_rate") < 1.0:
        return 0.0

    score = 1000.0
    score -= metrics.get("validation_fail_count", 0) * 300
    score -= metrics.get("validation_warning_count", 0) * 35
    score -= metrics.get("duplicate_warning_count", 0) * 25
    score += metrics.get("avg_unique_menu_ratio", 0) * 200
    score -= metrics.get("avg_duplicate_excess_rate", 0) * 300

    return round(score, 4)


def print_ranking(records: list[dict], top_k: int) -> None:
    eligible = [
        record for record in records
        if record.get("ranking_eligible")
    ]

    ranked = sorted(
        eligible,
        key=lambda row: row.get("objective_score", 0),
        reverse=True,
    )

    print()
    print("=" * 100)
    print("[SNAPSHOT REPLAY RANKING]")
    print("=" * 100)

    if not ranked:
        print("No eligible records.")
        return

    for rank, record in enumerate(ranked[:top_k], start=1):
        print()
        print("-" * 100)
        print("rank:", rank)
        print("case_id:", record.get("case_id"))
        print("objective_score:", record.get("objective_score"))
        print("config:", record.get("config"))
        print("metrics:", record.get("metrics"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay optimizer snapshots without calling RAG API."
    )
    parser.add_argument(
        "--snapshot-file",
        default="modeling/experiments/snapshots/style_validation_optimizer_snapshots.json",
    )
    parser.add_argument(
        "--output-dir",
        default="modeling/experiments/results/optimizer_snapshot_replay",
    )
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()

    snapshot_file = Path(args.snapshot_file)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    snapshot_data = read_json(snapshot_file)
    snapshots = snapshot_data.get("snapshots", [])

    cases = build_cases(max_cases=args.max_cases)

    records = []

    print("=" * 100)
    print("[OPTIMIZER SNAPSHOT REPLAY START]")
    print("=" * 100)
    print("snapshot_file:", snapshot_file)
    print("snapshot_count:", len(snapshots))
    print("output_dir:", output_dir)
    print("case_count:", len(cases))

    for index, case in enumerate(cases, start=1):
        print()
        print("=" * 100)
        print(f"[{index}/{len(cases)}] {case['case_id']}")
        print("=" * 100)
        print("config:", case["config"])

        record = evaluate_case(
            case_id=case["case_id"],
            config=case["config"],
            snapshots=snapshots,
        )

        records.append(record)

        write_json(output_dir / "snapshot_replay_records.json", records)
        write_csv(output_dir / "snapshot_replay_summary.csv", records)

        print("ranking_eligible:", record.get("ranking_eligible"))
        print("objective_score:", record.get("objective_score"))
        print("metrics:", record.get("metrics"))

    print_ranking(records, top_k=args.top_k)

    print()
    print("[INFO] snapshot replay finished.")
    print("[INFO] records:", output_dir / "snapshot_replay_records.json")
    print("[INFO] csv:", output_dir / "snapshot_replay_summary.csv")


if __name__ == "__main__":
    main()
