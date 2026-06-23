import json
from pathlib import Path
from statistics import mean


ORTOOLS_RESULT_PATH = Path(
    "modeling/experiments/results/ortools_default_policy_compare_result.json"
)

LEAST_COST_RESULT_PATH = Path(
    "modeling/experiments/results/least_cost_baseline_result.json"
)

OUTPUT_PATH = Path(
    "modeling/experiments/results/compare_least_cost_vs_ortools_summary.json"
)


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def get_monthly_plan(result: dict) -> dict:
    response = result.get("response") or {}
    return response.get("monthly_plan") or {}


def get_summary(result: dict) -> dict:
    return get_monthly_plan(result).get("summary") or {}


def get_optimizer(result: dict) -> dict:
    return get_monthly_plan(result).get("optimizer") or {}


def get_baseline(result: dict) -> dict:
    return get_monthly_plan(result).get("baseline") or {}


def get_profiling(result: dict) -> dict:
    return get_monthly_plan(result).get("profiling") or {}



def extract_selected_menus(result: dict) -> list[dict]:
    """
    월간 식단 결과에서 selected_menu 목록을 추출한다.
    OR-Tools 결과와 Least-cost 결과 모두 동일한 방식으로 처리한다.
    """

    monthly_plan = get_monthly_plan(result)
    selected_menus = []

    for day in monthly_plan.get("days", []):
        for meal in day.get("meals", []):
            selected_menu = meal.get("selected_menu")

            if selected_menu:
                selected_menus.append(selected_menu)

    return selected_menus


def average_menu_score(selected_menus: list[dict], score_key: str):
    """
    selected_menu 목록에서 scores[score_key] 평균을 계산한다.
    """

    values = []

    for menu in selected_menus:
        scores = menu.get("scores", {}) or {}
        value = scores.get(score_key)

        if value is None:
            continue

        number = safe_number(value)

        if number is not None:
            values.append(number)

    if not values:
        return None

    return round(mean(values), 2)


def average_menu_field(selected_menus: list[dict], field_key: str):
    """
    selected_menu 목록에서 특정 숫자 필드 평균을 계산한다.
    예: final_score, calories, protein
    """

    values = []

    for menu in selected_menus:
        value = menu.get(field_key)
        number = safe_number(value)

        if number is not None:
            values.append(number)

    if not values:
        return None

    return round(mean(values), 2)


def calculate_menu_quality_metrics(result: dict) -> dict:
    """
    monthly_plan.summary에 없는 품질 지표를 selected_menu 기준으로 직접 계산한다.
    """

    selected_menus = extract_selected_menus(result)

    return {
        "computed_selected_menu_count": len(selected_menus),
        "computed_average_final_score": average_menu_field(
            selected_menus,
            "final_score",
        ),
        "computed_average_preference_score": average_menu_score(
            selected_menus,
            "preference",
        ),
        "computed_average_budget_score": average_menu_score(
            selected_menus,
            "budget",
        ),
        "computed_average_nutrition_score": average_menu_score(
            selected_menus,
            "nutrition",
        ),
        "computed_average_calories": average_menu_field(
            selected_menus,
            "calories",
        ),
        "computed_average_protein": average_menu_field(
            selected_menus,
            "protein",
        ),
    }


def safe_number(value):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def diff_value(ortools_value, least_cost_value):
    ortools_number = safe_number(ortools_value)
    least_cost_number = safe_number(least_cost_value)

    if ortools_number is None or least_cost_number is None:
        return None

    return round(ortools_number - least_cost_number, 2)


def pct_diff(ortools_value, least_cost_value):
    ortools_number = safe_number(ortools_value)
    least_cost_number = safe_number(least_cost_value)

    if (
        ortools_number is None
        or least_cost_number is None
        or least_cost_number == 0
    ):
        return None

    return round((ortools_number - least_cost_number) / least_cost_number * 100, 2)



def divide_value(numerator, denominator):
    """
    0으로 나누는 상황을 피하면서 비율/단가 지표를 계산한다.
    """

    numerator_number = safe_number(numerator)
    denominator_number = safe_number(denominator)

    if numerator_number is None or denominator_number is None:
        return None

    if denominator_number == 0:
        return None

    return round(numerator_number / denominator_number, 2)


def rate_value(part, total):
    """
    비율 지표를 계산한다.
    예: unique_menu_count / selected_menu_count
    """

    return divide_value(part, total)


def build_row(ortools_result: dict, least_cost_result: dict) -> dict:
    scenario_id = ortools_result.get("scenario_id")

    ortools_summary = get_summary(ortools_result)
    least_cost_summary = get_summary(least_cost_result)

    optimizer = get_optimizer(ortools_result)
    baseline = get_baseline(least_cost_result)

    ortools_profiling = get_profiling(ortools_result)
    least_cost_profiling = get_profiling(least_cost_result)

    ortools_quality_metrics = calculate_menu_quality_metrics(ortools_result)
    least_cost_quality_metrics = calculate_menu_quality_metrics(least_cost_result)

    ortools_total_cost = ortools_summary.get("total_estimated_cost")
    least_cost_total_cost = least_cost_summary.get("total_estimated_cost")

    cost_diff = diff_value(
        ortools_total_cost,
        least_cost_total_cost,
    )

    ortools_selected_count = ortools_summary.get("selected_menu_count")
    least_cost_selected_count = least_cost_summary.get("selected_menu_count")

    ortools_unique_count = ortools_summary.get("unique_menu_count")
    least_cost_unique_count = least_cost_summary.get("unique_menu_count")

    ortools_duplicate_count = ortools_summary.get("duplicate_menu_count")
    least_cost_duplicate_count = least_cost_summary.get("duplicate_menu_count")

    additional_unique_menu_count = diff_value(
        ortools_unique_count,
        least_cost_unique_count,
    )

    reduced_duplicate_menu_count = diff_value(
        least_cost_duplicate_count,
        ortools_duplicate_count,
    )

    cost_per_additional_unique_menu = divide_value(
        cost_diff,
        additional_unique_menu_count,
    )

    return {
        "scenario_id": scenario_id,

        "ortools_success": (
            (ortools_result.get("response") or {}).get("failure_reason") is None
            and optimizer.get("solver_status") in ["OPTIMAL", "FEASIBLE"]
        ),
        "least_cost_success": baseline.get("success"),

        "ortools_solver_status": optimizer.get("solver_status"),
        "least_cost_failure_reason": baseline.get("failure_reason"),

        "ortools_runtime_ms": ortools_result.get("runtime_ms"),
        "least_cost_runtime_ms": least_cost_result.get("runtime_ms"),

        "ortools_total_cost": ortools_total_cost,
        "least_cost_total_cost": least_cost_total_cost,
        "cost_diff_ortools_minus_least_cost": cost_diff,
        "cost_diff_pct": pct_diff(
            ortools_total_cost,
            least_cost_total_cost,
        ),

        "ortools_average_daily_cost": ortools_summary.get("average_daily_cost"),
        "least_cost_average_daily_cost": least_cost_summary.get("average_daily_cost"),

        "ortools_selected_menu_count": ortools_selected_count,
        "least_cost_selected_menu_count": least_cost_selected_count,

        "ortools_unique_menu_count": ortools_unique_count,
        "least_cost_unique_menu_count": least_cost_unique_count,
        "unique_diff_ortools_minus_least_cost": additional_unique_menu_count,

        "ortools_duplicate_menu_count": ortools_duplicate_count,
        "least_cost_duplicate_menu_count": least_cost_duplicate_count,
        "duplicate_diff_ortools_minus_least_cost": diff_value(
            ortools_duplicate_count,
            least_cost_duplicate_count,
        ),

        "ortools_unique_rate": rate_value(
            ortools_unique_count,
            ortools_selected_count,
        ),
        "least_cost_unique_rate": rate_value(
            least_cost_unique_count,
            least_cost_selected_count,
        ),
        "unique_rate_diff_ortools_minus_least_cost": diff_value(
            rate_value(ortools_unique_count, ortools_selected_count),
            rate_value(least_cost_unique_count, least_cost_selected_count),
        ),

        "ortools_duplicate_rate": rate_value(
            ortools_duplicate_count,
            ortools_selected_count,
        ),
        "least_cost_duplicate_rate": rate_value(
            least_cost_duplicate_count,
            least_cost_selected_count,
        ),
        "duplicate_rate_diff_ortools_minus_least_cost": diff_value(
            rate_value(ortools_duplicate_count, ortools_selected_count),
            rate_value(least_cost_duplicate_count, least_cost_selected_count),
        ),

        "ortools_cost_per_unique_menu": divide_value(
            ortools_total_cost,
            ortools_unique_count,
        ),
        "least_cost_cost_per_unique_menu": divide_value(
            least_cost_total_cost,
            least_cost_unique_count,
        ),

        "additional_unique_menu_count": additional_unique_menu_count,
        "reduced_duplicate_menu_count": reduced_duplicate_menu_count,
        "additional_cost": cost_diff,
        "cost_per_additional_unique_menu": cost_per_additional_unique_menu,

        "least_cost_max_menu_repeat_count": least_cost_summary.get(
            "max_menu_repeat_count"
        ),

        "ortools_average_preference_score": ortools_summary.get(
            "average_preference_score"
        ),
        "least_cost_average_preference_score": least_cost_summary.get(
            "average_preference_score"
        ),
        "preference_diff_ortools_minus_least_cost": diff_value(
            ortools_summary.get("average_preference_score"),
            least_cost_summary.get("average_preference_score"),
        ),

        "ortools_average_budget_score": ortools_summary.get("average_budget_score"),
        "least_cost_average_budget_score": least_cost_summary.get(
            "average_budget_score"
        ),
        "budget_score_diff_ortools_minus_least_cost": diff_value(
            ortools_summary.get("average_budget_score"),
            least_cost_summary.get("average_budget_score"),
        ),

        "least_cost_average_nutrition_score": least_cost_summary.get(
            "average_nutrition_score"
        ),
        "least_cost_average_final_score": least_cost_summary.get(
            "average_final_score"
        ),

        "ortools_computed_average_final_score": ortools_quality_metrics.get(
            "computed_average_final_score"
        ),
        "least_cost_computed_average_final_score": least_cost_quality_metrics.get(
            "computed_average_final_score"
        ),
        "final_score_diff_ortools_minus_least_cost": diff_value(
            ortools_quality_metrics.get("computed_average_final_score"),
            least_cost_quality_metrics.get("computed_average_final_score"),
        ),

        "ortools_computed_average_preference_score": ortools_quality_metrics.get(
            "computed_average_preference_score"
        ),
        "least_cost_computed_average_preference_score": least_cost_quality_metrics.get(
            "computed_average_preference_score"
        ),
        "computed_preference_diff_ortools_minus_least_cost": diff_value(
            ortools_quality_metrics.get("computed_average_preference_score"),
            least_cost_quality_metrics.get("computed_average_preference_score"),
        ),

        "ortools_computed_average_budget_score": ortools_quality_metrics.get(
            "computed_average_budget_score"
        ),
        "least_cost_computed_average_budget_score": least_cost_quality_metrics.get(
            "computed_average_budget_score"
        ),
        "computed_budget_diff_ortools_minus_least_cost": diff_value(
            ortools_quality_metrics.get("computed_average_budget_score"),
            least_cost_quality_metrics.get("computed_average_budget_score"),
        ),

        "ortools_computed_average_nutrition_score": ortools_quality_metrics.get(
            "computed_average_nutrition_score"
        ),
        "least_cost_computed_average_nutrition_score": least_cost_quality_metrics.get(
            "computed_average_nutrition_score"
        ),
        "nutrition_score_diff_ortools_minus_least_cost": diff_value(
            ortools_quality_metrics.get("computed_average_nutrition_score"),
            least_cost_quality_metrics.get("computed_average_nutrition_score"),
        ),

        "ortools_computed_average_calories": ortools_quality_metrics.get(
            "computed_average_calories"
        ),
        "least_cost_computed_average_calories": least_cost_quality_metrics.get(
            "computed_average_calories"
        ),

        "ortools_computed_average_protein": ortools_quality_metrics.get(
            "computed_average_protein"
        ),
        "least_cost_computed_average_protein": least_cost_quality_metrics.get(
            "computed_average_protein"
        ),

        "ortools_rag_candidate_multiplier": ortools_profiling.get(
            "rag_candidate_multiplier"
        ),
        "least_cost_rag_candidate_multiplier": least_cost_profiling.get(
            "rag_candidate_multiplier"
        ),
        "ortools_rag_request_count": ortools_profiling.get(
            "rag_candidate_request_count"
        ),
        "least_cost_rag_request_count": least_cost_profiling.get(
            "rag_candidate_request_count"
        ),
    }


def average(rows: list[dict], key: str):
    values = [
        safe_number(row.get(key))
        for row in rows
        if safe_number(row.get(key)) is not None
    ]

    if not values:
        return None

    return round(mean(values), 2)


def summarize_metric_rows(rows: list[dict]) -> dict:
    """
    전달받은 rows 기준으로 비용, 다양성, 점수 지표 평균을 계산한다.

    전체 rows를 넣으면 전체 평균이 되고,
    paired success rows를 넣으면 둘 다 성공한 시나리오 기준 평균이 된다.
    """

    if not rows:
        return {
            "count": 0,
            "avg_ortools_runtime_sec": None,
            "avg_least_cost_runtime_sec": None,
            "avg_ortools_total_cost": None,
            "avg_least_cost_total_cost": None,
            "avg_cost_diff_ortools_minus_least_cost": None,
            "avg_cost_diff_pct": None,
            "avg_ortools_unique_menu_count": None,
            "avg_least_cost_unique_menu_count": None,
            "avg_unique_diff_ortools_minus_least_cost": None,
            "avg_ortools_duplicate_menu_count": None,
            "avg_least_cost_duplicate_menu_count": None,
            "avg_ortools_preference_score": None,
            "avg_least_cost_preference_score": None,
            "avg_preference_diff_ortools_minus_least_cost": None,
            "avg_ortools_budget_score": None,
            "avg_least_cost_budget_score": None,
            "avg_budget_score_diff_ortools_minus_least_cost": None,
            "avg_least_cost_nutrition_score": None,
            "avg_least_cost_final_score": None,
        }

    return {
        "count": len(rows),

        "avg_ortools_runtime_sec": round(
            average(rows, "ortools_runtime_ms") / 1000,
            2,
        ),
        "avg_least_cost_runtime_sec": round(
            average(rows, "least_cost_runtime_ms") / 1000,
            2,
        ),

        "avg_ortools_total_cost": average(rows, "ortools_total_cost"),
        "avg_least_cost_total_cost": average(rows, "least_cost_total_cost"),
        "avg_cost_diff_ortools_minus_least_cost": average(
            rows,
            "cost_diff_ortools_minus_least_cost",
        ),
        "avg_cost_diff_pct": average(rows, "cost_diff_pct"),

        "avg_ortools_unique_menu_count": average(rows, "ortools_unique_menu_count"),
        "avg_least_cost_unique_menu_count": average(
            rows,
            "least_cost_unique_menu_count",
        ),
        "avg_unique_diff_ortools_minus_least_cost": average(
            rows,
            "unique_diff_ortools_minus_least_cost",
        ),

        "avg_ortools_duplicate_menu_count": average(
            rows,
            "ortools_duplicate_menu_count",
        ),
        "avg_least_cost_duplicate_menu_count": average(
            rows,
            "least_cost_duplicate_menu_count",
        ),

        "avg_ortools_unique_rate": average(
            rows,
            "ortools_unique_rate",
        ),
        "avg_least_cost_unique_rate": average(
            rows,
            "least_cost_unique_rate",
        ),
        "avg_unique_rate_diff_ortools_minus_least_cost": average(
            rows,
            "unique_rate_diff_ortools_minus_least_cost",
        ),

        "avg_ortools_duplicate_rate": average(
            rows,
            "ortools_duplicate_rate",
        ),
        "avg_least_cost_duplicate_rate": average(
            rows,
            "least_cost_duplicate_rate",
        ),
        "avg_duplicate_rate_diff_ortools_minus_least_cost": average(
            rows,
            "duplicate_rate_diff_ortools_minus_least_cost",
        ),

        "avg_ortools_cost_per_unique_menu": average(
            rows,
            "ortools_cost_per_unique_menu",
        ),
        "avg_least_cost_cost_per_unique_menu": average(
            rows,
            "least_cost_cost_per_unique_menu",
        ),

        "avg_additional_unique_menu_count": average(
            rows,
            "additional_unique_menu_count",
        ),
        "avg_reduced_duplicate_menu_count": average(
            rows,
            "reduced_duplicate_menu_count",
        ),
        "avg_additional_cost": average(
            rows,
            "additional_cost",
        ),
        "avg_cost_per_additional_unique_menu": average(
            rows,
            "cost_per_additional_unique_menu",
        ),

        "avg_ortools_preference_score": average(
            rows,
            "ortools_average_preference_score",
        ),
        "avg_least_cost_preference_score": average(
            rows,
            "least_cost_average_preference_score",
        ),
        "avg_preference_diff_ortools_minus_least_cost": average(
            rows,
            "preference_diff_ortools_minus_least_cost",
        ),

        "avg_ortools_budget_score": average(rows, "ortools_average_budget_score"),
        "avg_least_cost_budget_score": average(
            rows,
            "least_cost_average_budget_score",
        ),
        "avg_budget_score_diff_ortools_minus_least_cost": average(
            rows,
            "budget_score_diff_ortools_minus_least_cost",
        ),

        "avg_least_cost_nutrition_score": average(
            rows,
            "least_cost_average_nutrition_score",
        ),
        "avg_least_cost_final_score": average(
            rows,
            "least_cost_average_final_score",
        ),

        "avg_ortools_computed_final_score": average(
            rows,
            "ortools_computed_average_final_score",
        ),
        "avg_least_cost_computed_final_score": average(
            rows,
            "least_cost_computed_average_final_score",
        ),
        "avg_final_score_diff_ortools_minus_least_cost": average(
            rows,
            "final_score_diff_ortools_minus_least_cost",
        ),

        "avg_ortools_computed_preference_score": average(
            rows,
            "ortools_computed_average_preference_score",
        ),
        "avg_least_cost_computed_preference_score": average(
            rows,
            "least_cost_computed_average_preference_score",
        ),
        "avg_computed_preference_diff_ortools_minus_least_cost": average(
            rows,
            "computed_preference_diff_ortools_minus_least_cost",
        ),

        "avg_ortools_computed_budget_score": average(
            rows,
            "ortools_computed_average_budget_score",
        ),
        "avg_least_cost_computed_budget_score": average(
            rows,
            "least_cost_computed_average_budget_score",
        ),
        "avg_computed_budget_diff_ortools_minus_least_cost": average(
            rows,
            "computed_budget_diff_ortools_minus_least_cost",
        ),

        "avg_ortools_computed_nutrition_score": average(
            rows,
            "ortools_computed_average_nutrition_score",
        ),
        "avg_least_cost_computed_nutrition_score": average(
            rows,
            "least_cost_computed_average_nutrition_score",
        ),
        "avg_nutrition_score_diff_ortools_minus_least_cost": average(
            rows,
            "nutrition_score_diff_ortools_minus_least_cost",
        ),

        "avg_ortools_computed_calories": average(
            rows,
            "ortools_computed_average_calories",
        ),
        "avg_least_cost_computed_calories": average(
            rows,
            "least_cost_computed_average_calories",
        ),

        "avg_ortools_computed_protein": average(
            rows,
            "ortools_computed_average_protein",
        ),
        "avg_least_cost_computed_protein": average(
            rows,
            "least_cost_computed_average_protein",
        ),
    }


def summarize(rows: list[dict]) -> dict:
    """
    전체 성공률 요약과 둘 다 성공한 시나리오 기준 품질 비교 요약을 함께 만든다.
    """

    total_count = len(rows)
    ortools_success_count = sum(1 for row in rows if row["ortools_success"])
    least_cost_success_count = sum(1 for row in rows if row["least_cost_success"])

    paired_success_rows = [
        row for row in rows
        if row["ortools_success"] and row["least_cost_success"]
    ]

    return {
        "summary_all": {
            "total_count": total_count,
            "ortools_success_count": ortools_success_count,
            "least_cost_success_count": least_cost_success_count,
            "ortools_success_rate": (
                round(ortools_success_count / total_count, 4)
                if total_count
                else 0
            ),
            "least_cost_success_rate": (
                round(least_cost_success_count / total_count, 4)
                if total_count
                else 0
            ),
            **summarize_metric_rows(rows),
        },
        "summary_paired_success": {
            "description": "OR-Tools와 Least-cost baseline이 모두 성공한 시나리오만 비교한 결과",
            **summarize_metric_rows(paired_success_rows),
        },
    }


def print_table(rows: list[dict], summary: dict) -> None:
    print("\n=== OR-Tools vs Least-cost 비교 요약 ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    print("\n=== 시나리오별 비교 ===")
    print(
        "scenario_id | "
        "ortools_success | least_success | "
        "ortools_cost | least_cost | cost_diff | cost_pct | "
        "ortools_unique | least_unique | "
        "ortools_dup | least_dup | "
        "ortools_pref | least_pref | "
        "ortools_budget | least_budget"
    )
    print("-" * 220)

    for row in rows:
        print(
            row["scenario_id"],
            "|",
            row["ortools_success"],
            "|",
            row["least_cost_success"],
            "|",
            row["ortools_total_cost"],
            "|",
            row["least_cost_total_cost"],
            "|",
            row["cost_diff_ortools_minus_least_cost"],
            "|",
            row["cost_diff_pct"],
            "|",
            row["ortools_unique_menu_count"],
            "|",
            row["least_cost_unique_menu_count"],
            "|",
            row["ortools_duplicate_menu_count"],
            "|",
            row["least_cost_duplicate_menu_count"],
            "|",
            row["ortools_average_preference_score"],
            "|",
            row["least_cost_average_preference_score"],
            "|",
            row["ortools_average_budget_score"],
            "|",
            row["least_cost_average_budget_score"],
        )


def main() -> None:
    ortools_data = load_json(ORTOOLS_RESULT_PATH)
    least_cost_data = load_json(LEAST_COST_RESULT_PATH)

    ortools_results = {
        result["scenario_id"]: result
        for result in ortools_data.get("results", [])
    }

    least_cost_results = {
        result["scenario_id"]: result
        for result in least_cost_data.get("results", [])
    }

    rows = []

    for scenario_id, ortools_result in ortools_results.items():
        least_cost_result = least_cost_results.get(scenario_id)

        if least_cost_result is None:
            continue

        rows.append(
            build_row(
                ortools_result=ortools_result,
                least_cost_result=least_cost_result,
            )
        )

    summary = summarize(rows)

    output_data = {
        "comparison_name": "least_cost_vs_ortools",
        "ortools_result_path": str(ORTOOLS_RESULT_PATH),
        "least_cost_result_path": str(LEAST_COST_RESULT_PATH),
        "summary": summary,
        "rows": rows,
    }

    save_json(OUTPUT_PATH, output_data)

    print_table(rows, summary)
    print(f"\n[INFO] 비교 결과 저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
