import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_INPUT_PATH = (
    "ai/modeling/experiments/results/style_validation_user_stability_latest_result.json"
)
DEFAULT_OUTPUT_JSON_PATH = (
    "ai/modeling/experiments/results/final_validation_summary.json"
)
DEFAULT_OUTPUT_CSV_PATH = (
    "ai/modeling/experiments/results/final_validation_summary.csv"
)


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: str, data: dict) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_csv(path: str, rows: list[dict]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        output_path.write_text("", encoding="utf-8")
        return

    fieldnames = []

    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def percentile(values: list[float], percent: float) -> float | None:
    if not values:
        return None

    sorted_values = sorted(values)
    index = (len(sorted_values) - 1) * percent
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)

    if lower == upper:
        return round(sorted_values[lower], 2)

    weight = index - lower
    value = sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight

    return round(value, 2)


def safe_rate(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0

    return round(numerator / denominator, 4)


def extract_warning_types(secondary_warnings: list[dict]) -> list[str]:
    return [
        warning.get("type")
        for warning in secondary_warnings
        if warning.get("type")
    ]


def extract_warning_levels(secondary_warnings: list[dict]) -> list[str]:
    return [
        warning.get("level")
        for warning in secondary_warnings
        if warning.get("level")
    ]


def find_duplicate_warning(secondary_warnings: list[dict]) -> dict | None:
    for warning in secondary_warnings:
        if warning.get("type") == "duplicate_menu":
            return warning

    return None


def collect_response_shape(response: dict) -> dict:
    monthly_plan = response.get("monthly_plan") or {}

    return {
        "has_selected_style": bool(response.get("selected_style")),
        "has_meta": bool(response.get("meta")),
        "has_modeling_profile": bool(response.get("modeling_profile")),
        "has_applied_style_adjustment": bool(
            response.get("applied_style_adjustment")
        ),
        "has_monthly_plan": bool(monthly_plan),
        "has_summary": bool(monthly_plan.get("summary")),
        "has_style_validation": bool(monthly_plan.get("style_validation")),
        "has_days": bool(monthly_plan.get("days")),
    }


def collect_optimizer_info(monthly_plan: dict) -> dict:
    optimizer = monthly_plan.get("optimizer") or {}

    return {
        "optimizer_enabled": bool(optimizer.get("enabled")),
        "solver": optimizer.get("solver"),
        "solver_status": optimizer.get("solver_status"),
        "objective_value": optimizer.get("objective_value"),
    }


def analyze_result_file(input_path: str) -> dict:
    data = load_json(input_path)
    results = data.get("results", [])

    rows = []

    success_count = 0
    fail_count = 0

    runtime_values = []

    validation_status_counter = Counter()
    warning_type_counter = Counter()
    warning_level_counter = Counter()
    solver_status_counter = Counter()
    failure_reason_counter = Counter()
    focus_key_counter = Counter()

    total_selected_menu_count = 0
    total_required_meal_count = 0
    total_unique_menu_count = 0
    total_duplicate_menu_count = 0
    total_available_recommendation_count = 0

    for result in results:
        scenario_id = result.get("scenario_id")
        description = result.get("description")
        runner_success = bool(result.get("success"))

        runtime_ms = result.get("runtime_ms")
        if isinstance(runtime_ms, (int, float)):
            runtime_values.append(runtime_ms)

        if runner_success:
            success_count += 1
        else:
            fail_count += 1
            error = result.get("error") or {}
            failure_reason_counter[error.get("failure_reason", "unknown")] += 1

        response = result.get("response") or {}
        selected_style = response.get("selected_style") or {}
        monthly_plan = response.get("monthly_plan") or {}

        summary = monthly_plan.get("summary") or {}
        style_validation = monthly_plan.get("style_validation") or {}
        secondary_warnings = style_validation.get("secondary_warnings") or []

        response_shape = collect_response_shape(response)
        optimizer_info = collect_optimizer_info(monthly_plan)

        selected_menu_count = summary.get("selected_menu_count", 0) or 0
        unique_menu_count = summary.get("unique_menu_count", 0) or 0
        duplicate_menu_count = summary.get("duplicate_menu_count", 0) or 0

        required_meal_count = monthly_plan.get("required_meal_count", 0) or 0
        available_recommendation_count = (
            monthly_plan.get("available_recommendation_count", 0) or 0
        )

        duplicate_rate = safe_rate(duplicate_menu_count, selected_menu_count)
        unique_menu_ratio = safe_rate(unique_menu_count, selected_menu_count)
        meal_coverage_rate = safe_rate(selected_menu_count, required_meal_count)
        candidate_to_required_ratio = safe_rate(
            available_recommendation_count,
            required_meal_count,
        )

        validation_status = style_validation.get("status", "unknown")
        focus_key = selected_style.get("focus_key")

        warning_types = extract_warning_types(secondary_warnings)
        warning_levels = extract_warning_levels(secondary_warnings)
        duplicate_warning = find_duplicate_warning(secondary_warnings) or {}

        validation_status_counter[validation_status] += 1
        warning_type_counter.update(warning_types)
        warning_level_counter.update(warning_levels)
        focus_key_counter[focus_key] += 1

        solver_status = optimizer_info.get("solver_status")
        if solver_status:
            solver_status_counter[solver_status] += 1

        total_selected_menu_count += selected_menu_count
        total_required_meal_count += required_meal_count
        total_unique_menu_count += unique_menu_count
        total_duplicate_menu_count += duplicate_menu_count
        total_available_recommendation_count += available_recommendation_count

        row = {
            "scenario_id": scenario_id,
            "description": description,
            "runner_success": runner_success,
            "runtime_ms": runtime_ms,

            "style_id": selected_style.get("style_id"),
            "style_name": selected_style.get("style_name"),
            "source_goal": selected_style.get("source_goal"),
            "focus_key": focus_key,

            **response_shape,

            "required_meal_count": required_meal_count,
            "available_recommendation_count": available_recommendation_count,
            "candidate_to_required_ratio": candidate_to_required_ratio,
            "selected_menu_count": selected_menu_count,
            "unique_menu_count": unique_menu_count,
            "duplicate_menu_count": duplicate_menu_count,
            "unique_menu_ratio": unique_menu_ratio,
            "duplicate_rate": duplicate_rate,
            "meal_coverage_rate": meal_coverage_rate,

            "average_calories": summary.get("average_calories"),
            "average_protein": summary.get("average_protein"),
            "average_carbohydrate": summary.get("average_carbohydrate"),
            "average_fat": summary.get("average_fat"),
            "average_nutrition_score": summary.get("average_nutrition_score"),
            "average_budget_score": summary.get("average_budget_score"),
            "average_preference_score": summary.get("average_preference_score"),
            "average_difficulty_score": summary.get("average_difficulty_score"),
            "average_diversity_score": summary.get("average_diversity_score"),

            "validation_status": validation_status,
            "validation_message": style_validation.get("message"),
            "secondary_warning_count": len(secondary_warnings),
            "secondary_warning_types": "|".join(warning_types),
            "secondary_warning_levels": "|".join(warning_levels),
            "recommendation_hint": style_validation.get("recommendation_hint"),

            "duplicate_menu_warning_level": duplicate_warning.get("level"),
            "duplicate_menu_warning_rate": duplicate_warning.get("rate"),
            "duplicate_menu_recommended_maximum_rate": duplicate_warning.get(
                "recommended_maximum_rate"
            ),

            **optimizer_info,
        }

        checked_metrics = style_validation.get("checked_metrics") or {}
        for key, value in checked_metrics.items():
            row[f"metric_{key}"] = value

        rows.append(row)

    scenario_count = len(results)

    summary = {
        "scenario_count": scenario_count,
        "success_count": success_count,
        "fail_count": fail_count,
        "success_rate": safe_rate(success_count, scenario_count),
        "error_rate": safe_rate(fail_count, scenario_count),

        "avg_runtime_ms": (
            round(sum(runtime_values) / len(runtime_values), 2)
            if runtime_values
            else None
        ),
        "p50_runtime_ms": percentile(runtime_values, 0.50),
        "p95_runtime_ms": percentile(runtime_values, 0.95),
        "p99_runtime_ms": percentile(runtime_values, 0.99),
        "max_runtime_ms": (
            round(max(runtime_values), 2)
            if runtime_values
            else None
        ),

        "validation_status_count": dict(validation_status_counter),
        "focus_key_count": dict(focus_key_counter),
        "secondary_warning_type_count": dict(warning_type_counter),
        "secondary_warning_level_count": dict(warning_level_counter),
        "solver_status_count": dict(solver_status_counter),
        "failure_reason_count": dict(failure_reason_counter),

        "required_meal_count": total_required_meal_count,
        "selected_menu_count": total_selected_menu_count,
        "meal_coverage_rate": safe_rate(
            total_selected_menu_count,
            total_required_meal_count,
        ),
        "available_recommendation_count": total_available_recommendation_count,
        "candidate_to_required_ratio": safe_rate(
            total_available_recommendation_count,
            total_required_meal_count,
        ),

        "unique_menu_count": total_unique_menu_count,
        "duplicate_menu_count": total_duplicate_menu_count,
        "unique_menu_ratio": safe_rate(
            total_unique_menu_count,
            total_selected_menu_count,
        ),
        "duplicate_rate": safe_rate(
            total_duplicate_menu_count,
            total_selected_menu_count,
        ),
    }

    return {
        "analysis_name": "final_monthly_plan_validation_analysis",
        "input_path": input_path,
        "summary": summary,
        "rows": rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="월간 식단 최종 validation 결과를 분석한다."
    )

    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_PATH,
        help="분석할 실험 결과 JSON 경로",
    )
    parser.add_argument(
        "--output-json",
        default=DEFAULT_OUTPUT_JSON_PATH,
        help="분석 요약 JSON 출력 경로",
    )
    parser.add_argument(
        "--output-csv",
        default=DEFAULT_OUTPUT_CSV_PATH,
        help="분석 row CSV 출력 경로",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    analysis_result = analyze_result_file(args.input)

    save_json(args.output_json, analysis_result)
    save_csv(args.output_csv, analysis_result["rows"])

    print("[INFO] final validation analysis finished.")
    print(f"[INFO] input: {args.input}")
    print(f"[INFO] output json: {args.output_json}")
    print(f"[INFO] output csv: {args.output_csv}")
    print(f"[INFO] summary: {analysis_result['summary']}")


if __name__ == "__main__":
    main()
