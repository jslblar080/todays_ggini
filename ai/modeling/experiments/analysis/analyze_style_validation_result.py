import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_INPUT_PATH = (
    "ai/modeling/experiments/results/style_validation_baseline_latest_result.json"
)
DEFAULT_OUTPUT_JSON_PATH = (
    "ai/modeling/experiments/results/style_validation_baseline_latest_summary.json"
)
DEFAULT_OUTPUT_CSV_PATH = (
    "ai/modeling/experiments/results/style_validation_baseline_latest_summary.csv"
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


def flatten_checked_metrics(checked_metrics: dict) -> dict:
    return {
        f"metric_{key}": value
        for key, value in (checked_metrics or {}).items()
    }


def calculate_duplicate_rate(summary: dict) -> float:
    selected_menu_count = summary.get("selected_menu_count") or 0
    duplicate_menu_count = summary.get("duplicate_menu_count") or 0

    if selected_menu_count <= 0:
        return 0

    return round(duplicate_menu_count / selected_menu_count, 4)


def find_warning_by_type(warnings: list[dict], warning_type: str) -> dict:
    for warning in warnings or []:
        if warning.get("type") == warning_type:
            return warning

    return {}


def analyze_result_file(input_path: str) -> dict:
    data = load_json(input_path)
    results = data.get("results", [])

    rows = []

    status_counter = Counter()
    focus_key_counter = Counter()
    style_name_counter = Counter()
    warning_type_counter = Counter()
    warning_level_counter = Counter()
    status_by_focus_key = defaultdict(Counter)

    total_selected_menu_count = 0
    total_unique_menu_count = 0
    total_duplicate_menu_count = 0
    duplicate_rate_values = []

    success_count = 0
    fail_count = 0

    for result in results:
        scenario_id = result.get("scenario_id")
        description = result.get("description")
        runner_success = result.get("success")

        if runner_success:
            success_count += 1
        else:
            fail_count += 1

        response = result.get("response") or {}
        selected_style = response.get("selected_style") or {}
        monthly_plan = response.get("monthly_plan") or {}
        plan_summary = monthly_plan.get("summary") or {}
        style_validation = monthly_plan.get("style_validation") or {}

        style_name = selected_style.get("style_name")
        source_goal = selected_style.get("source_goal")
        focus_key = selected_style.get("focus_key")

        status = style_validation.get("status", "unknown")
        message = style_validation.get("message")
        checked_metrics = style_validation.get("checked_metrics") or {}
        secondary_warnings = style_validation.get("secondary_warnings") or []
        recommendation_hint = style_validation.get("recommendation_hint")

        warning_types = [
            warning.get("type")
            for warning in secondary_warnings
            if warning.get("type")
        ]
        warning_levels = [
            warning.get("level")
            for warning in secondary_warnings
            if warning.get("level")
        ]

        duplicate_warning = find_warning_by_type(
            warnings=secondary_warnings,
            warning_type="duplicate_menu",
        )

        selected_menu_count = plan_summary.get("selected_menu_count", 0)
        unique_menu_count = plan_summary.get("unique_menu_count", 0)
        duplicate_menu_count = plan_summary.get("duplicate_menu_count", 0)
        duplicate_rate = calculate_duplicate_rate(plan_summary)

        total_selected_menu_count += selected_menu_count
        total_unique_menu_count += unique_menu_count
        total_duplicate_menu_count += duplicate_menu_count

        if selected_menu_count > 0:
            duplicate_rate_values.append(duplicate_rate)

        status_counter[status] += 1
        focus_key_counter[focus_key] += 1
        style_name_counter[style_name] += 1
        status_by_focus_key[focus_key][status] += 1
        warning_type_counter.update(warning_types)
        warning_level_counter.update(warning_levels)

        row = {
            "scenario_id": scenario_id,
            "description": description,
            "runner_success": runner_success,
            "style_name": style_name,
            "source_goal": source_goal,
            "focus_key": focus_key,
            "validation_status": status,
            "validation_message": message,
            "recommendation_hint": recommendation_hint,
            "secondary_warning_count": len(secondary_warnings),
            "secondary_warning_types": "|".join(warning_types),
            "secondary_warning_levels": "|".join(warning_levels),
            "selected_menu_count": selected_menu_count,
            "unique_menu_count": unique_menu_count,
            "duplicate_menu_count": duplicate_menu_count,
            "duplicate_rate": duplicate_rate,
            "duplicate_menu_warning_level": duplicate_warning.get("level"),
            "duplicate_menu_warning_rate": duplicate_warning.get("rate"),
            "duplicate_menu_recommended_maximum_rate": duplicate_warning.get(
                "recommended_maximum_rate"
            ),
            "average_calories": plan_summary.get("average_calories"),
            "average_protein": plan_summary.get("average_protein"),
            "average_carbohydrate": plan_summary.get("average_carbohydrate"),
            "average_fat": plan_summary.get("average_fat"),
            "average_nutrition_score": plan_summary.get("average_nutrition_score"),
            "average_budget_score": plan_summary.get("average_budget_score"),
            "average_preference_score": plan_summary.get(
                "average_preference_score"
            ),
            "average_difficulty_score": plan_summary.get(
                "average_difficulty_score"
            ),
            "average_diversity_score": plan_summary.get(
                "average_diversity_score"
            ),
            **flatten_checked_metrics(checked_metrics),
        }

        rows.append(row)

    average_duplicate_rate = (
        round(sum(duplicate_rate_values) / len(duplicate_rate_values), 4)
        if duplicate_rate_values
        else 0
    )

    summary = {
        "scenario_count": len(rows),
        "success_count": success_count,
        "fail_count": fail_count,
        "status_count": dict(status_counter),
        "focus_key_count": dict(focus_key_counter),
        "style_name_count": dict(style_name_counter),
        "secondary_warning_type_count": dict(warning_type_counter),
        "secondary_warning_level_count": dict(warning_level_counter),
        "status_by_focus_key": {
            focus_key: dict(counter)
            for focus_key, counter in status_by_focus_key.items()
        },
        "selected_menu_count": total_selected_menu_count,
        "unique_menu_count": total_unique_menu_count,
        "duplicate_menu_count": total_duplicate_menu_count,
        "average_duplicate_rate": average_duplicate_rate,
    }

    return {
        "analysis_name": "style_validation_latest_analysis",
        "input_path": input_path,
        "summary": summary,
        "rows": rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="월간 식단 실험 결과 JSON에서 style_validation 결과를 분석한다."
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

    print("[INFO] style validation analysis finished.")
    print(f"[INFO] input: {args.input}")
    print(f"[INFO] output json: {args.output_json}")
    print(f"[INFO] output csv: {args.output_csv}")
    print(f"[INFO] summary: {analysis_result['summary']}")


if __name__ == "__main__":
    main()
