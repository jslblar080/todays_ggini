import argparse
import csv
import json
from pathlib import Path
from typing import Any


def load_json(path: str) -> dict:
    """JSON 파일을 읽어 dict로 반환한다."""
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def safe_get_response_success(result: dict) -> bool:
    """
    response 성공 여부를 안정적으로 판단한다.

    성공 응답에는 success 키가 없을 수 있으므로,
    response.success가 False인 경우만 실패로 본다.
    """

    if not result.get("success"):
        return False

    response = result.get("response")

    if not response:
        return False

    return response.get("success") is not False


def extract_result_rows(planner_name: str, data: dict) -> list[dict[str, Any]]:
    """실험 결과 JSON에서 비교용 row를 추출한다."""

    rows = []

    for result in data.get("results", []):
        response = result.get("response") or {}
        monthly_plan = response.get("monthly_plan", {})
        optimizer = monthly_plan.get("optimizer", {})
        summary = monthly_plan.get("summary", {})

        rows.append({
            "planner": planner_name,
            "scenario_id": result.get("scenario_id"),
            "execution_success": result.get("success"),
            "response_success": safe_get_response_success(result),
            "runtime_ms": result.get("runtime_ms"),
            "solver_status": optimizer.get("solver_status"),
            "selected_menu_count": summary.get("selected_menu_count", 0),
            "unique_menu_count": summary.get("unique_menu_count", 0),
            "duplicate_menu_count": summary.get("duplicate_menu_count", 0),
            "unique_menu_ratio": calculate_unique_menu_ratio(summary),
            "total_estimated_cost": summary.get("total_estimated_cost", 0),
            "average_daily_cost": summary.get("average_daily_cost", 0),
            "failure_reason": response.get("failure_reason"),
        })

    return rows


def calculate_unique_menu_ratio(summary: dict) -> float:
    """고유 메뉴 비율을 계산한다."""

    selected_menu_count = summary.get("selected_menu_count", 0) or 0
    unique_menu_count = summary.get("unique_menu_count", 0) or 0

    if selected_menu_count <= 0:
        return 0.0

    return round(unique_menu_count / selected_menu_count, 4)


def build_pivot_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    시나리오별로 planner 결과를 한 줄에 비교하기 위한 pivot summary를 만든다.
    """

    scenario_ids = sorted({row["scenario_id"] for row in rows})
    planners = list(dict.fromkeys(row["planner"] for row in rows))

    pivot_rows = []

    for scenario_id in scenario_ids:
        scenario_rows = [
            row for row in rows
            if row["scenario_id"] == scenario_id
        ]

        pivot_row = {
            "scenario_id": scenario_id,
        }

        for planner in planners:
            matched = next(
                (
                    row for row in scenario_rows
                    if row["planner"] == planner
                ),
                None,
            )

            if matched is None:
                continue

            prefix = planner

            pivot_row[f"{prefix}_response_success"] = matched["response_success"]
            pivot_row[f"{prefix}_solver_status"] = matched["solver_status"]
            pivot_row[f"{prefix}_runtime_ms"] = matched["runtime_ms"]
            pivot_row[f"{prefix}_total_estimated_cost"] = matched["total_estimated_cost"]
            pivot_row[f"{prefix}_duplicate_menu_count"] = matched["duplicate_menu_count"]
            pivot_row[f"{prefix}_unique_menu_count"] = matched["unique_menu_count"]
            pivot_row[f"{prefix}_unique_menu_ratio"] = matched["unique_menu_ratio"]
            pivot_row[f"{prefix}_failure_reason"] = matched["failure_reason"]

        pivot_rows.append(pivot_row)

    return pivot_rows


def save_csv(path: str, rows: list[dict[str, Any]]) -> None:
    """rows를 CSV로 저장한다."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        output_path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())

    with open(output_path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Baseline / OR-Tools 결과를 비교하는 CSV를 생성한다."
    )
    parser.add_argument(
        "--baseline",
        required=True,
        help="baseline 결과 JSON 경로",
    )
    parser.add_argument(
        "--ortools-first",
        required=True,
        help="OR-Tools 1차 결과 JSON 경로",
    )
    parser.add_argument(
        "--ortools-penalty",
        required=True,
        help="OR-Tools penalty 결과 JSON 경로",
    )
    parser.add_argument(
        "--detail-output",
        required=True,
        help="planner별 상세 비교 CSV 저장 경로",
    )
    parser.add_argument(
        "--pivot-output",
        required=True,
        help="시나리오별 pivot 비교 CSV 저장 경로",
    )

    args = parser.parse_args()

    file_map = {
        "baseline_mmr": args.baseline,
        "ortools_first": args.ortools_first,
        "ortools_penalty": args.ortools_penalty,
    }

    detail_rows = []

    for planner_name, path in file_map.items():
        data = load_json(path)
        detail_rows.extend(
            extract_result_rows(
                planner_name=planner_name,
                data=data,
            )
        )

    pivot_rows = build_pivot_summary(detail_rows)

    save_csv(args.detail_output, detail_rows)
    save_csv(args.pivot_output, pivot_rows)

    print("[INFO] optimizer comparison finished.")
    print(f"[INFO] detail_output: {args.detail_output}")
    print(f"[INFO] pivot_output: {args.pivot_output}")


if __name__ == "__main__":
    main()
