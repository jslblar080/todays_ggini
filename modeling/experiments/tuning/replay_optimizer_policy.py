import argparse
import csv
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

from replay_optimizer_snapshots import (
    apply_config,
    calculate_allowed_duplicate_rate,
    calculate_duplicate_excess_rate,
    calculate_duplicate_warning,
    calculate_objective_score,
    read_json,
    write_json,
)

from services.optimizer.ortools.monthly_plan_optimizer import (
    solve_monthly_plan_with_ortools,
)
from services.optimizer.ortools.result_mapper import build_ortools_monthly_plan
from services.plan.plan_validation_service import (
    build_style_validation,
    enrich_style_validation,
)


BASE_CONFIG = {
    "repeat_penalty_weight": 4500,
    "protein_bonus_weight": 150,
    "difficulty_bonus_weight": 0,
    "repeat_penalty_growth": "quadratic",
}


def collect_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        return " ".join(collect_text(v) for v in value.values())

    if isinstance(value, list):
        return " ".join(collect_text(v) for v in value)

    return str(value)


def snapshot_text(snapshot: dict) -> str:
    return " ".join([
        collect_text(snapshot.get("scenario_id")),
        collect_text(snapshot.get("description")),
        collect_text(snapshot.get("purpose")),
        collect_text(snapshot.get("profile")),
        collect_text(snapshot.get("selected_style")),
    ])


def has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def calculate_candidate_ratio(optimizer_input: dict) -> float:
    selected_menu_count = int(
        optimizer_input.get("required_meal_count")
        or len(optimizer_input.get("slots", []))
        or 0
    )

    available_recommendation_count = int(
        optimizer_input.get("original_recommendation_count")
        or optimizer_input.get("used_optimizer_candidate_count")
        or len(optimizer_input.get("menus", []))
        or 0
    )

    if selected_menu_count <= 0:
        return 0.0

    return available_recommendation_count / selected_menu_count


def policy_base_0037(snapshot: dict) -> dict:
    """
    replay_0037에서 나온 전역 최상위 후보를 그대로 적용하는 정책.
    """

    return dict(BASE_CONFIG)


def policy_candidate_aware(snapshot: dict) -> dict:
    """
    사용자 조건과 후보풀 여유도를 반영하는 정책.

    핵심 방향:
    - 후보풀이 넓으면 중복 패널티 강화
    - 후보풀이 좁으면 중복을 과하게 억제하지 않음
    - 고단백 목표는 protein bonus 강화
    - 간편식/낮은 조리 실력은 난이도 보너스 별도 부여
    """

    text = snapshot_text(snapshot)
    optimizer_input = snapshot.get("optimizer_input") or {}
    candidate_ratio = calculate_candidate_ratio(optimizer_input)

    config = dict(BASE_CONFIG)

    constrained = (
        candidate_ratio < 2.0
        or has_any(text, ["선호 조건이 매우 좁은", "좁은 선호", "알레르기", "매우 낮은 예산", "복합 제약"])
    )

    high_diversity = has_any(text, ["높은 다양성"])
    high_protein = has_any(text, ["고단백"])
    easy_cooking = has_any(text, ["간편식", "낮은 조리 실력"])

    if high_diversity or candidate_ratio >= 3.0:
        config["repeat_penalty_weight"] = 6000
    elif constrained:
        config["repeat_penalty_weight"] = 3500
    else:
        config["repeat_penalty_weight"] = 4500

    if high_protein:
        config["protein_bonus_weight"] = 220
    elif has_any(text, ["다이어트"]):
        config["protein_bonus_weight"] = 150
    else:
        config["protein_bonus_weight"] = 150

    if easy_cooking:
        config["difficulty_bonus_weight"] = 120
    else:
        config["difficulty_bonus_weight"] = 0

    return config


def policy_conservative(snapshot: dict) -> dict:
    """
    보수 정책.

    너무 강한 보정으로 특정 시나리오가 무너지는지 확인하기 위한 비교군.
    """

    text = snapshot_text(snapshot)
    optimizer_input = snapshot.get("optimizer_input") or {}
    candidate_ratio = calculate_candidate_ratio(optimizer_input)

    config = dict(BASE_CONFIG)

    constrained = (
        candidate_ratio < 2.0
        or has_any(text, ["선호 조건이 매우 좁은", "좁은 선호", "알레르기", "매우 낮은 예산", "복합 제약"])
    )

    if constrained:
        config["repeat_penalty_weight"] = 3500
    elif candidate_ratio >= 3.0:
        config["repeat_penalty_weight"] = 6000
    else:
        config["repeat_penalty_weight"] = 4500

    if has_any(text, ["고단백"]):
        config["protein_bonus_weight"] = 180
    else:
        config["protein_bonus_weight"] = 150

    if has_any(text, ["간편식", "낮은 조리 실력"]):
        config["difficulty_bonus_weight"] = 50
    else:
        config["difficulty_bonus_weight"] = 0

    return config


POLICIES = {
    "policy_base_0037": policy_base_0037,
    "policy_candidate_aware": policy_candidate_aware,
    "policy_conservative": policy_conservative,
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
    allowed_duplicate_rates = []
    duplicate_excess_rates = []

    for row in records:
        summary = row.get("summary") or {}

        if summary.get("unique_menu_ratio") is not None:
            unique_ratios.append(float(summary.get("unique_menu_ratio") or 0))

        if summary.get("duplicate_rate") is not None:
            duplicate_rates.append(float(summary.get("duplicate_rate") or 0))

        if summary.get("allowed_duplicate_rate") is not None:
            allowed_duplicate_rates.append(float(summary.get("allowed_duplicate_rate") or 0))

        if summary.get("duplicate_excess_rate") is not None:
            duplicate_excess_rates.append(float(summary.get("duplicate_excess_rate") or 0))

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


def evaluate_policy(policy_id: str, policy_func, snapshots: list[dict]) -> dict:
    scenario_records = []
    runtime_values = []

    for snapshot in snapshots:
        started_at = time.perf_counter()

        config = policy_func(snapshot)

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
                "applied_config": config,
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
            "applied_config": config,
        })

    metrics = summarize_records(scenario_records, runtime_values)
    objective_score = calculate_objective_score(metrics)

    return {
        "case_id": policy_id,
        "policy_id": policy_id,
        "ranking_eligible": metrics["solver_success_rate"] == 1.0,
        "objective_score": objective_score,
        "metrics": metrics,
        "rows": scenario_records,
    }


def write_policy_csv(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "policy_id",
        "ranking_eligible",
        "objective_score",
        "scenario_count",
        "solver_success_rate",
        "validation_pass_count",
        "validation_warning_count",
        "validation_fail_count",
        "duplicate_warning_count",
        "avg_unique_menu_ratio",
        "avg_duplicate_rate",
        "avg_allowed_duplicate_rate",
        "avg_duplicate_excess_rate",
        "avg_runtime_ms",
    ]

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for record in records:
            metrics = record.get("metrics") or {}
            writer.writerow({
                "policy_id": record.get("policy_id"),
                "ranking_eligible": record.get("ranking_eligible"),
                "objective_score": record.get("objective_score"),
                "scenario_count": metrics.get("scenario_count"),
                "solver_success_rate": metrics.get("solver_success_rate"),
                "validation_pass_count": metrics.get("validation_pass_count"),
                "validation_warning_count": metrics.get("validation_warning_count"),
                "validation_fail_count": metrics.get("validation_fail_count"),
                "duplicate_warning_count": metrics.get("duplicate_warning_count"),
                "avg_unique_menu_ratio": metrics.get("avg_unique_menu_ratio"),
                "avg_duplicate_rate": metrics.get("avg_duplicate_rate"),
                "avg_allowed_duplicate_rate": metrics.get("avg_allowed_duplicate_rate"),
                "avg_duplicate_excess_rate": metrics.get("avg_duplicate_excess_rate"),
                "avg_runtime_ms": metrics.get("avg_runtime_ms"),
            })


def print_ranking(records: list[dict]) -> None:
    ranked = sorted(
        [row for row in records if row.get("ranking_eligible")],
        key=lambda row: row.get("objective_score", -10**9),
        reverse=True,
    )

    print()
    print("=" * 100)
    print("[OPTIMIZER POLICY REPLAY RANKING]")
    print("=" * 100)

    for rank, record in enumerate(ranked, start=1):
        print()
        print("-" * 100)
        print("rank:", rank)
        print("policy_id:", record.get("policy_id"))
        print("objective_score:", record.get("objective_score"))
        print("metrics:", record.get("metrics"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay optimizer snapshots with scenario-aware policy functions."
    )
    parser.add_argument(
        "--snapshot-file",
        default="modeling/experiments/snapshots/style_validation_optimizer_snapshots.json",
    )
    parser.add_argument(
        "--output-dir",
        default="modeling/experiments/results/optimizer_policy_replay",
    )
    args = parser.parse_args()

    snapshot_file = Path(args.snapshot_file)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    snapshot_data = read_json(snapshot_file)
    snapshots = snapshot_data.get("snapshots", [])

    records = []

    print("=" * 100)
    print("[OPTIMIZER POLICY REPLAY START]")
    print("=" * 100)
    print("snapshot_file:", snapshot_file)
    print("snapshot_count:", len(snapshots))
    print("output_dir:", output_dir)
    print("policy_count:", len(POLICIES))

    for policy_id, policy_func in POLICIES.items():
        print()
        print("=" * 100)
        print(policy_id)
        print("=" * 100)

        record = evaluate_policy(
            policy_id=policy_id,
            policy_func=policy_func,
            snapshots=snapshots,
        )

        records.append(record)

        write_json(output_dir / "optimizer_policy_replay_records.json", records)
        write_policy_csv(output_dir / "optimizer_policy_replay_summary.csv", records)

        print("ranking_eligible:", record.get("ranking_eligible"))
        print("objective_score:", record.get("objective_score"))
        print("metrics:", record.get("metrics"))

    print_ranking(records)

    print()
    print("[INFO] optimizer policy replay finished.")
    print("[INFO] records:", output_dir / "optimizer_policy_replay_records.json")
    print("[INFO] csv:", output_dir / "optimizer_policy_replay_summary.csv")


if __name__ == "__main__":
    main()
