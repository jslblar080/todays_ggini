import argparse
import csv
import json
import statistics
from pathlib import Path
from typing import Any


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def safe_number(value: Any, default: float = 0) -> float:
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0

    sorted_values = sorted(values)
    index = int(round((len(sorted_values) - 1) * ratio))
    return sorted_values[index]


def extract_selected_menus(response: dict) -> list[dict]:
    monthly_plan = response.get("monthly_plan", {})
    days = monthly_plan.get("days", [])

    menus = []

    for day in days:
        for meal in day.get("meals", []):
            selected_menu = meal.get("selected_menu", {})
            if not selected_menu:
                continue

            menus.append({
                "day": day.get("day"),
                "meal_order": meal.get("meal_order"),
                "menu": selected_menu,
            })

    return menus


def build_cost_summary_row(result: dict) -> dict:
    scenario_id = result.get("scenario_id")
    description = result.get("description", "")
    runtime_ms = result.get("runtime_ms", 0)

    if not result.get("success"):
        error = result.get("error", {})
        return {
            "scenario_id": scenario_id,
            "description": description,
            "success": False,
            "failure_reason": error.get("message", "execution_failed"),
        }

    response = result.get("response", {})

    if response.get("success") is False:
        return {
            "scenario_id": scenario_id,
            "description": description,
            "success": False,
            "failure_reason": response.get("failure_reason", "service_failed"),
        }

    monthly_plan = response.get("monthly_plan", {})
    summary = monthly_plan.get("summary", {})
    profile = response.get("modeling_profile", {})

    selected_menus = extract_selected_menus(response)

    estimated_costs = [
        safe_number(item["menu"].get("estimated_cost"))
        for item in selected_menus
    ]
    rag_estimated_costs = [
        safe_number(item["menu"].get("rag_estimated_cost"))
        for item in selected_menus
    ]

    meal_budget = safe_number(profile.get("meal_budget"))
    monthly_budget = safe_number(profile.get("monthly_budget"))

    summary_total_estimated_cost = safe_number(
        summary.get("total_estimated_cost")
    )

    estimated_cost_sum = sum(estimated_costs)
    rag_estimated_cost_sum = sum(rag_estimated_costs)

    estimated_cost_avg = statistics.mean(estimated_costs) if estimated_costs else 0
    rag_estimated_cost_avg = statistics.mean(rag_estimated_costs) if rag_estimated_costs else 0

    over_meal_budget_count = 0
    if meal_budget > 0:
        over_meal_budget_count = sum(
            1 for cost in estimated_costs
            if cost > meal_budget
        )

    selected_menu_count = len(selected_menus)

    return {
        "scenario_id": scenario_id,
        "description": description,
        "success": True,
        "failure_reason": "",
        "runtime_ms": runtime_ms,
        "monthly_budget": int(monthly_budget),
        "meal_budget": int(meal_budget),
        "selected_menu_count": selected_menu_count,

        "summary_total_estimated_cost": int(summary_total_estimated_cost),
        "sum_estimated_cost": int(estimated_cost_sum),
        "sum_rag_estimated_cost": int(rag_estimated_cost_sum),

        "summary_matches_estimated_cost": (
            abs(summary_total_estimated_cost - estimated_cost_sum) < 1
        ),
        "summary_matches_rag_estimated_cost": (
            abs(summary_total_estimated_cost - rag_estimated_cost_sum) < 1
        ),

        "estimated_cost_avg": round(estimated_cost_avg, 2),
        "estimated_cost_median": round(statistics.median(estimated_costs), 2) if estimated_costs else 0,
        "estimated_cost_min": int(min(estimated_costs)) if estimated_costs else 0,
        "estimated_cost_max": int(max(estimated_costs)) if estimated_costs else 0,
        "estimated_cost_p90": int(percentile(estimated_costs, 0.9)),

        "rag_estimated_cost_avg": round(rag_estimated_cost_avg, 2),
        "rag_estimated_cost_median": round(statistics.median(rag_estimated_costs), 2) if rag_estimated_costs else 0,
        "rag_estimated_cost_min": int(min(rag_estimated_costs)) if rag_estimated_costs else 0,
        "rag_estimated_cost_max": int(max(rag_estimated_costs)) if rag_estimated_costs else 0,
        "rag_estimated_cost_p90": int(percentile(rag_estimated_costs, 0.9)),

        "avg_estimated_vs_rag_gap": round(
            estimated_cost_avg - rag_estimated_cost_avg,
            2
        ),
        "estimated_to_rag_ratio": round(
            estimated_cost_avg / rag_estimated_cost_avg,
            4
        ) if rag_estimated_cost_avg > 0 else 0,

        "over_meal_budget_count": over_meal_budget_count,
        "over_meal_budget_rate": round(
            over_meal_budget_count / selected_menu_count,
            4
        ) if selected_menu_count else 0,

        "budget_usage_rate_by_estimated": round(
            estimated_cost_sum / monthly_budget,
            4
        ) if monthly_budget > 0 else 0,
        "budget_usage_rate_by_rag": round(
            rag_estimated_cost_sum / monthly_budget,
            4
        ) if monthly_budget > 0 else 0,
    }


def extract_top_cost_menus(result: dict, top_n: int) -> list[dict]:
    if not result.get("success"):
        return []

    response = result.get("response", {})
    selected_menus = extract_selected_menus(response)

    rows = []

    for item in selected_menus:
        menu = item["menu"]
        estimated_cost = safe_number(menu.get("estimated_cost"))
        rag_estimated_cost = safe_number(menu.get("rag_estimated_cost"))

        rows.append({
            "scenario_id": result.get("scenario_id"),
            "day": item.get("day"),
            "meal_order": item.get("meal_order"),
            "menu_id": menu.get("menu_id"),
            "name": menu.get("name"),
            "category": menu.get("category"),
            "estimated_cost": int(estimated_cost),
            "rag_estimated_cost": int(rag_estimated_cost),
            "cost_gap": int(estimated_cost - rag_estimated_cost),
            "estimated_to_rag_ratio": round(
                estimated_cost / rag_estimated_cost,
                4
            ) if rag_estimated_cost > 0 else 0,
            "pricing_status": menu.get("pricing_status"),
            "final_score": menu.get("final_score"),
            "budget_score": menu.get("scores", {}).get("budget"),
            "nutrition_score": menu.get("scores", {}).get("nutrition"),
            "preference_score": menu.get("scores", {}).get("preference"),
        })

    rows.sort(key=lambda row: row["estimated_cost"], reverse=True)

    return rows[:top_n]


def write_csv(path: str, rows: list[dict]) -> None:
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
        description="월간 식단 결과의 estimated_cost / rag_estimated_cost 분포를 분석한다."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--summary-output", required=True)
    parser.add_argument("--top-cost-output", required=True)
    parser.add_argument("--top-n", type=int, default=20)

    args = parser.parse_args()

    data = load_json(args.input)
    results = data.get("results", [])

    summary_rows = [
        build_cost_summary_row(result)
        for result in results
    ]

    top_cost_rows = []
    for result in results:
        top_cost_rows.extend(
            extract_top_cost_menus(result=result, top_n=args.top_n)
        )

    top_cost_rows.sort(
        key=lambda row: row["estimated_cost"],
        reverse=True
    )

    write_csv(args.summary_output, summary_rows)
    write_csv(args.top_cost_output, top_cost_rows)

    print("[INFO] cost distribution analysis finished.")
    print(f"[INFO] summary_output: {args.summary_output}")
    print(f"[INFO] top_cost_output: {args.top_cost_output}")

    success_rows = [row for row in summary_rows if row.get("success")]

    if success_rows:
        avg_estimated_usage = statistics.mean(
            row["budget_usage_rate_by_estimated"]
            for row in success_rows
        )
        avg_rag_usage = statistics.mean(
            row["budget_usage_rate_by_rag"]
            for row in success_rows
        )
        avg_ratio = statistics.mean(
            row["estimated_to_rag_ratio"]
            for row in success_rows
        )

        print("[INFO] overall:")
        print({
            "success_count": len(success_rows),
            "avg_budget_usage_rate_by_estimated": round(avg_estimated_usage, 4),
            "avg_budget_usage_rate_by_rag": round(avg_rag_usage, 4),
            "avg_estimated_to_rag_ratio": round(avg_ratio, 4),
        })


if __name__ == "__main__":
    main()
