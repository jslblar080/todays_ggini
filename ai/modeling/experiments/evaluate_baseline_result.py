import argparse
import csv
import json
from pathlib import Path
from typing import Any


def load_json(path: str) -> dict:
    """JSON 파일을 읽어 dict로 반환한다."""
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def ensure_parent_dir(path: str) -> None:
    """출력 파일의 부모 폴더를 생성한다."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def safe_get(data: dict, path: list[str], default: Any = None) -> Any:
    """중첩 dict에서 안전하게 값을 가져온다."""
    current = data

    for key in path:
        if not isinstance(current, dict):
            return default

        if key not in current:
            return default

        current = current[key]

    return current


def calculate_budget_metrics(result: dict) -> dict:
    """예산 관련 지표를 계산한다."""
    response = result.get("response") or {}
    profile = response.get("modeling_profile") or result.get("profile") or {}
    summary = safe_get(response, ["monthly_plan", "summary"], default={}) or {}

    monthly_budget = profile.get("monthly_budget", 0) or 0
    monthly_total_cost = summary.get("total_estimated_cost", 0) or 0

    budget_usage_rate = (
        round(monthly_total_cost / monthly_budget, 4)
        if monthly_budget > 0
        else None
    )

    budget_overrun_amount = max(0, monthly_total_cost - monthly_budget)
    budget_violation_count = 1 if budget_overrun_amount > 0 else 0

    return {
        "monthly_budget": monthly_budget,
        "monthly_total_cost": monthly_total_cost,
        "budget_usage_rate": budget_usage_rate,
        "budget_overrun_amount": budget_overrun_amount,
        "budget_violation_count": budget_violation_count,
    }


def calculate_diversity_metrics(result: dict) -> dict:
    """다양성 관련 지표를 계산한다."""
    response = result.get("response") or {}
    summary = safe_get(response, ["monthly_plan", "summary"], default={}) or {}

    selected_menu_count = summary.get("selected_menu_count", 0) or 0
    unique_menu_count = summary.get("unique_menu_count", 0) or 0
    duplicate_menu_count = summary.get("duplicate_menu_count", 0) or 0

    unique_menu_ratio = (
        round(unique_menu_count / selected_menu_count, 4)
        if selected_menu_count > 0
        else None
    )

    return {
        "selected_menu_count": selected_menu_count,
        "unique_menu_count": unique_menu_count,
        "duplicate_menu_count": duplicate_menu_count,
        "unique_menu_ratio": unique_menu_ratio,
    }


def calculate_nutrition_metrics(result: dict) -> dict:
    """영양 관련 summary 지표를 가져온다."""
    response = result.get("response") or {}
    summary = safe_get(response, ["monthly_plan", "summary"], default={}) or {}

    return {
        "average_calories": summary.get("average_calories"),
        "average_protein": summary.get("average_protein"),
        "average_carbohydrate": summary.get("average_carbohydrate"),
        "average_fat": summary.get("average_fat"),
        "average_nutrition_score": summary.get("average_nutrition_score"),
    }


def calculate_preference_metrics(result: dict) -> dict:
    """사용자 적합도 관련 summary 지표를 가져온다."""
    response = result.get("response") or {}
    summary = safe_get(response, ["monthly_plan", "summary"], default={}) or {}

    return {
        "average_preference_score": summary.get("average_preference_score"),
        "average_budget_score": summary.get("average_budget_score"),
        "average_difficulty_score": summary.get("average_difficulty_score"),
        "average_diversity_score": summary.get("average_diversity_score"),
    }


def extract_failure_reason(result: dict) -> str:
    """실패 결과에서 실패 사유를 문자열로 추출한다."""
    if result.get("success"):
        return ""

    error = result.get("error") or {}
    error_type = error.get("type", "UnknownError")
    message = error.get("message", "")

    if "list index out of range" in message:
        return "candidate_empty_index_error"

    if "ValidationError" in error_type:
        return "profile_validation_error"

    return f"{error_type}: {message}"


def build_summary_row(result: dict) -> dict:
    """실험 결과 하나를 CSV row로 변환한다."""
    response = result.get("response") or {}
    meta = response.get("meta") or {}
    monthly_plan = response.get("monthly_plan") or {}
    style_validation = monthly_plan.get("style_validation") or {}

    row = {
        "scenario_id": result.get("scenario_id"),
        "description": result.get("description"),
        "planner": result.get("planner", "baseline_mmr_reranking"),
        "success": result.get("success"),
        "failure_reason": extract_failure_reason(result),
        "runtime_ms": result.get("runtime_ms"),
        "available_recommendation_count": meta.get("available_recommendation_count"),
        "style_validation_status": style_validation.get("status"),
        "style_validation_message": style_validation.get("message"),
    }

    row.update(calculate_budget_metrics(result))
    row.update(calculate_nutrition_metrics(result))
    row.update(calculate_diversity_metrics(result))
    row.update(calculate_preference_metrics(result))

    return row


def write_csv(path: str, rows: list[dict]) -> None:
    """CSV 파일로 저장한다."""
    ensure_parent_dir(path)

    if not rows:
        raise ValueError("CSV로 저장할 rows가 없습니다.")

    fieldnames = list(rows[0].keys())

    with open(path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def calculate_overall_summary(rows: list[dict]) -> dict:
    """전체 실험 요약을 계산한다."""
    total_count = len(rows)
    success_rows = [row for row in rows if row["success"]]
    fail_rows = [row for row in rows if not row["success"]]

    def avg(key: str):
        values = [
            row[key]
            for row in success_rows
            if isinstance(row.get(key), (int, float))
        ]

        return round(sum(values) / len(values), 4) if values else None

    return {
        "total_count": total_count,
        "success_count": len(success_rows),
        "fail_count": len(fail_rows),
        "success_rate": round(len(success_rows) / total_count, 4) if total_count else 0,
        "avg_runtime_ms_success_only": avg("runtime_ms"),
        "avg_budget_usage_rate": avg("budget_usage_rate"),
        "avg_monthly_total_cost": avg("monthly_total_cost"),
        "avg_duplicate_menu_count": avg("duplicate_menu_count"),
        "avg_unique_menu_ratio": avg("unique_menu_ratio"),
        "avg_preference_score": avg("average_preference_score"),
        "failure_reasons": {
            reason: sum(1 for row in fail_rows if row["failure_reason"] == reason)
            for reason in sorted(set(row["failure_reason"] for row in fail_rows))
        },
    }


def save_overall_summary(path: str, summary: dict) -> None:
    """전체 요약 JSON을 저장한다."""
    ensure_parent_dir(path)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="baseline MMR + Re-ranking 실험 결과를 CSV summary로 변환한다."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="baseline_mmr_result.json 경로",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="baseline_mmr_summary.csv 저장 경로",
    )
    parser.add_argument(
        "--overall-output",
        required=False,
        default=None,
        help="전체 요약 JSON 저장 경로",
    )

    args = parser.parse_args()

    data = load_json(args.input)
    results = data.get("results", [])

    rows = [build_summary_row(result) for result in results]

    write_csv(args.output, rows)

    overall_summary = calculate_overall_summary(rows)

    if args.overall_output:
        save_overall_summary(args.overall_output, overall_summary)

    print("[INFO] baseline evaluation finished.")
    print(f"[INFO] csv output: {args.output}")
    print("[INFO] overall summary:")
    print(json.dumps(overall_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
