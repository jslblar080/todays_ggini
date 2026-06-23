import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUT_PATH = (
    "modeling/experiments/results/ortools_default_policy_compare_result.json"
)

DEFAULT_OUTPUT_JSON_PATH = (
    "modeling/experiments/results/nutrition_outlier_penalty_summary.json"
)

DEFAULT_OUTPUT_CSV_PATH = (
    "modeling/experiments/results/nutrition_outlier_penalty_summary.csv"
)


def load_json(path: str) -> dict:
    """JSON 파일을 읽어 dict로 반환한다."""

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: str, data: dict) -> None:
    """dict 데이터를 JSON 파일로 저장한다."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def save_csv(path: str, rows: list[dict]) -> None:
    """분석 row 목록을 CSV로 저장한다."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        output_path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())

    with open(output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def safe_number(value: Any, default: float = 0) -> float:
    """숫자로 변환할 수 없는 값을 안전하게 기본값으로 변환한다."""

    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def divide(numerator: float, denominator: float) -> float:
    """0 나누기를 피하면서 비율을 계산한다."""

    if denominator == 0:
        return 0

    return round(numerator / denominator, 4)


def get_monthly_plan(result: dict) -> dict:
    """실험 결과에서 monthly_plan을 추출한다."""

    response = result.get("response") or {}
    return response.get("monthly_plan") or {}


def extract_selected_menus(result: dict) -> list[dict]:
    """월간 식단 결과에서 selected_menu 목록을 추출한다."""

    monthly_plan = get_monthly_plan(result)
    selected_menus = []

    for day in monthly_plan.get("days", []):
        for meal in day.get("meals", []):
            selected_menu = meal.get("selected_menu")

            if selected_menu:
                selected_menus.append(selected_menu)

    return selected_menus


def calculate_menu_metrics(menus: list[dict]) -> dict:
    """
    선택 메뉴의 영양 이상치 및 penalty 반영 점수 지표를 계산한다.

    adjusted_final_score는 실제 서비스 점수를 바꾸지 않고,
    실험 분석용으로만 final_score - nutrition_outlier_penalty를 계산한다.
    """

    selected_count = len(menus)

    if selected_count == 0:
        return {
            "selected_menu_count": 0,
            "outlier_menu_count": 0,
            "extreme_outlier_menu_count": 0,
            "outlier_menu_rate": 0,
            "extreme_outlier_menu_rate": 0,
            "total_nutrition_outlier_penalty": 0,
            "average_nutrition_outlier_penalty": 0,
            "average_final_score": 0,
            "average_adjusted_final_score": 0,
            "average_final_score_gap": 0,
            "max_nutrition_outlier_penalty": 0,
            "outlier_issue_types": "",
        }

    total_final_score = 0
    total_adjusted_final_score = 0
    total_penalty = 0
    max_penalty = 0

    outlier_menu_count = 0
    extreme_outlier_menu_count = 0
    issue_types = set()

    for menu in menus:
        final_score = safe_number(menu.get("final_score"))
        penalty = safe_number(menu.get("nutrition_outlier_penalty"))
        adjusted_final_score = max(final_score - penalty, 0)

        total_final_score += final_score
        total_adjusted_final_score += adjusted_final_score
        total_penalty += penalty
        max_penalty = max(max_penalty, penalty)

        issues = menu.get("nutrition_outlier_issues") or []

        if issues:
            outlier_menu_count += 1
            issue_types.update(str(issue) for issue in issues)

        if menu.get("is_extreme_nutrition_outlier"):
            extreme_outlier_menu_count += 1

    average_final_score = total_final_score / selected_count
    average_adjusted_final_score = total_adjusted_final_score / selected_count

    return {
        "selected_menu_count": selected_count,
        "outlier_menu_count": outlier_menu_count,
        "extreme_outlier_menu_count": extreme_outlier_menu_count,
        "outlier_menu_rate": divide(outlier_menu_count, selected_count),
        "extreme_outlier_menu_rate": divide(
            extreme_outlier_menu_count,
            selected_count,
        ),
        "total_nutrition_outlier_penalty": round(total_penalty, 2),
        "average_nutrition_outlier_penalty": round(total_penalty / selected_count, 2),
        "average_final_score": round(average_final_score, 2),
        "average_adjusted_final_score": round(average_adjusted_final_score, 2),
        "average_final_score_gap": round(
            average_final_score - average_adjusted_final_score,
            2,
        ),
        "max_nutrition_outlier_penalty": round(max_penalty, 2),
        "outlier_issue_types": "|".join(sorted(issue_types)),
    }


def build_result_row(result: dict) -> dict:
    """단일 시나리오 결과를 분석 row로 변환한다."""

    selected_menus = extract_selected_menus(result)
    metrics = calculate_menu_metrics(selected_menus)

    response = result.get("response") or {}
    monthly_plan = get_monthly_plan(result)
    optimizer = monthly_plan.get("optimizer") or {}
    summary = monthly_plan.get("summary") or {}

    return {
        "scenario_id": result.get("scenario_id"),
        "description": result.get("description"),
        "runner_success": result.get("success"),
        "response_failure_reason": response.get("failure_reason"),
        "solver_status": optimizer.get("solver_status"),
        "runtime_ms": result.get("runtime_ms"),
        "total_estimated_cost": summary.get("total_estimated_cost"),
        "unique_menu_count": summary.get("unique_menu_count"),
        "duplicate_menu_count": summary.get("duplicate_menu_count"),
        **metrics,
    }


def summarize_rows(rows: list[dict]) -> dict:
    """전체 row의 집계 지표를 만든다."""

    total_count = len(rows)

    if total_count == 0:
        return {
            "scenario_count": 0,
            "scenario_with_outlier_count": 0,
            "scenario_with_extreme_outlier_count": 0,
        }

    scenario_with_outlier_count = sum(
        1 for row in rows if row["outlier_menu_count"] > 0
    )
    scenario_with_extreme_outlier_count = sum(
        1 for row in rows if row["extreme_outlier_menu_count"] > 0
    )

    selected_menu_count = sum(row["selected_menu_count"] for row in rows)
    outlier_menu_count = sum(row["outlier_menu_count"] for row in rows)
    extreme_outlier_menu_count = sum(
        row["extreme_outlier_menu_count"] for row in rows
    )

    total_penalty = sum(row["total_nutrition_outlier_penalty"] for row in rows)

    return {
        "scenario_count": total_count,
        "scenario_with_outlier_count": scenario_with_outlier_count,
        "scenario_with_extreme_outlier_count": scenario_with_extreme_outlier_count,
        "scenario_with_outlier_rate": divide(
            scenario_with_outlier_count,
            total_count,
        ),
        "scenario_with_extreme_outlier_rate": divide(
            scenario_with_extreme_outlier_count,
            total_count,
        ),
        "selected_menu_count": selected_menu_count,
        "outlier_menu_count": outlier_menu_count,
        "extreme_outlier_menu_count": extreme_outlier_menu_count,
        "outlier_menu_rate": divide(outlier_menu_count, selected_menu_count),
        "extreme_outlier_menu_rate": divide(
            extreme_outlier_menu_count,
            selected_menu_count,
        ),
        "total_nutrition_outlier_penalty": round(total_penalty, 2),
        "average_penalty_per_scenario": round(total_penalty / total_count, 2),
    }


def analyze_result_file(input_path: str) -> dict:
    """실험 결과 파일 전체를 분석한다."""

    data = load_json(input_path)
    results = data.get("results", [])

    rows = [build_result_row(result) for result in results]
    summary = summarize_rows(rows)

    return {
        "analysis_name": "nutrition_outlier_penalty_analysis",
        "input_path": input_path,
        "summary": summary,
        "rows": rows,
    }


def parse_args() -> argparse.Namespace:
    """CLI 인자를 파싱한다."""

    parser = argparse.ArgumentParser(
        description="영양 이상치 penalty 반영 효과를 실험 결과 JSON에서 분석한다."
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
    """CLI entrypoint."""

    args = parse_args()

    analysis_result = analyze_result_file(args.input)

    save_json(args.output_json, analysis_result)
    save_csv(args.output_csv, analysis_result["rows"])

    print("[INFO] nutrition outlier penalty analysis finished.")
    print(f"[INFO] input: {args.input}")
    print(f"[INFO] output json: {args.output_json}")
    print(f"[INFO] output csv: {args.output_csv}")
    print(f"[INFO] summary: {analysis_result['summary']}")


if __name__ == "__main__":
    main()
