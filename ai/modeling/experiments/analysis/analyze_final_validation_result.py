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


def collect_rag_mapping_info(result: dict) -> dict:
    """
    실험 result artifact에 저장된 RAG mapping diagnostics를 수집한다.
    """

    diagnostics = result.get("diagnostics") or {}
    rag_mapping = diagnostics.get("rag_mapping") or {}
    quality_issue_type_count = rag_mapping.get("quality_issue_type_count") or {}
    ingredient_group_mapping_status_count = (
        rag_mapping.get("ingredient_group_mapping_status_count") or {}
    )

    return {
        "rag_mapping_event_count": rag_mapping.get("event_count", 0),
        "rag_raw_menus": rag_mapping.get("raw_menus", 0),
        "rag_mapped_menus": rag_mapping.get("mapped_menus", 0),
        "rag_excluded_menus": rag_mapping.get("excluded_menus", 0),
        "rag_quality_issue_menus": rag_mapping.get("quality_issue_menus", 0),
        "rag_quality_issue_type_count": quality_issue_type_count,
        "rag_ingredient_group_mapping_status_count": (
            ingredient_group_mapping_status_count
        ),
        "rag_mapping_success_rate": rag_mapping.get("mapping_success_rate", 0),
        "rag_quality_issue_rate": rag_mapping.get("quality_issue_rate", 0),
    }


def collect_optimizer_info(monthly_plan: dict) -> dict:
    optimizer = monthly_plan.get("optimizer") or {}
    config = optimizer.get("config") or {}

    return {
        "optimizer_enabled": bool(optimizer.get("enabled")),
        "solver": optimizer.get("solver"),
        "solver_status": optimizer.get("solver_status"),
        "objective_value": optimizer.get("objective_value"),
        "solver_time_limit_seconds": config.get("solver_time_limit_seconds"),
        "used_optimizer_candidate_count": config.get(
            "used_optimizer_candidate_count"
        ),
        "optimizer_candidate_multiplier": config.get(
            "optimizer_candidate_multiplier"
        ),
        "max_repeat_per_menu": config.get("max_repeat_per_menu"),
    }


def collect_fallback_info(monthly_plan: dict, response: dict) -> dict:
    """
    월간 식단 fallback 및 후보 풀 진단 정보를 수집한다.

    같은 fallback 정보가 response.meta와 monthly_plan 양쪽에 들어갈 수 있으므로,
    monthly_plan.fallback을 우선 사용하고 없으면 response.meta.fallback을 사용한다.
    """

    meta = response.get("meta") or {}
    fallback = monthly_plan.get("fallback") or meta.get("fallback") or {}

    fallback_steps = fallback.get("fallback_steps") or []
    candidate_diagnostics = fallback.get("candidate_diagnostics") or {}

    fallback_reasons = [
        step.get("reason")
        for step in fallback_steps
        if step.get("reason")
    ]

    shortage_reasons = candidate_diagnostics.get("shortage_reasons") or []

    candidate_count = candidate_diagnostics.get("candidate_count")
    required_meal_count = candidate_diagnostics.get("required_meal_count")

    return {
        "fallback_used": bool(fallback.get("fallback_used")),
        "fallback_step_count": len(fallback_steps),
        "fallback_reasons": "|".join(fallback_reasons),
        "final_candidate_count": fallback.get("final_candidate_count"),
        "candidate_pool_is_enough": candidate_diagnostics.get("is_enough"),
        "candidate_pool_shortage_reasons": "|".join(shortage_reasons),
        "candidate_pool_shortage_reason_count": len(shortage_reasons),
        "candidate_pool_candidate_count": candidate_count,
        "candidate_pool_unique_menu_count": candidate_diagnostics.get(
            "unique_menu_count"
        ),
        "candidate_pool_required_meal_count": required_meal_count,
        "candidate_pool_to_required_ratio": safe_rate(
            candidate_count or 0,
            required_meal_count or 0,
        ),
        "optimizer_candidate_limit": candidate_diagnostics.get(
            "optimizer_candidate_limit"
        ),
        "candidate_pool_max_repeat_per_menu": candidate_diagnostics.get(
            "max_repeat_per_menu"
        ),
        "max_fillable_meal_count": candidate_diagnostics.get(
            "max_fillable_meal_count"
        ),
        "minimum_unique_menu_count": candidate_diagnostics.get(
            "minimum_unique_menu_count"
        ),
        "recommended_next_step": candidate_diagnostics.get(
            "recommended_next_step"
        ),
        "additional_candidate_count": candidate_diagnostics.get(
            "additional_candidate_count"
        ),
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
    difficulty_feasibility_status_counter = Counter()
    difficulty_feasibility_reason_counter = Counter()
    fallback_reason_counter = Counter()
    candidate_shortage_reason_counter = Counter()
    recommended_next_step_counter = Counter()
    rag_quality_issue_type_counter = Counter()
    rag_ingredient_group_mapping_status_counter = Counter()

    fallback_count = 0
    candidate_pool_enough_count = 0
    candidate_pool_shortage_count = 0
    solver_success_count = 0
    optimal_count = 0
    feasible_count = 0
    non_success_solver_count = 0
    validation_warning_count = 0
    validation_fail_count = 0
    duplicate_warning_count = 0

    total_selected_menu_count = 0
    total_required_meal_count = 0
    total_unique_menu_count = 0
    total_duplicate_menu_count = 0
    total_available_recommendation_count = 0

    total_rag_mapping_event_count = 0
    total_rag_raw_menus = 0
    total_rag_mapped_menus = 0
    total_rag_excluded_menus = 0
    total_rag_quality_issue_menus = 0

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

        difficulty_feasibility = (
            style_validation
            .get("diagnostics", {})
            .get("difficulty_feasibility", {})
        )
        difficulty_feasibility_status = difficulty_feasibility.get("status")
        difficulty_feasibility_reason = difficulty_feasibility.get("reason")

        response_shape = collect_response_shape(response)
        optimizer_info = collect_optimizer_info(monthly_plan)
        fallback_info = collect_fallback_info(
            monthly_plan=monthly_plan,
            response=response,
        )
        rag_mapping_info = collect_rag_mapping_info(result)

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

        if difficulty_feasibility_status:
            difficulty_feasibility_status_counter[
                difficulty_feasibility_status
            ] += 1

        if difficulty_feasibility_reason:
            difficulty_feasibility_reason_counter[
                difficulty_feasibility_reason
            ] += 1

        solver_status = optimizer_info.get("solver_status")
        if solver_status:
            solver_status_counter[solver_status] += 1

        if solver_status in ["OPTIMAL", "FEASIBLE"]:
            solver_success_count += 1
        elif solver_status:
            non_success_solver_count += 1

        if solver_status == "OPTIMAL":
            optimal_count += 1

        if solver_status == "FEASIBLE":
            feasible_count += 1

        if validation_status == "warning":
            validation_warning_count += 1

        if validation_status == "fail":
            validation_fail_count += 1

        if duplicate_warning.get("level") == "warning":
            duplicate_warning_count += 1

        if fallback_info.get("fallback_used"):
            fallback_count += 1

        if fallback_info.get("candidate_pool_is_enough") is True:
            candidate_pool_enough_count += 1
        elif fallback_info.get("candidate_pool_is_enough") is False:
            candidate_pool_shortage_count += 1

        fallback_reason_counter.update(
            [
                reason
                for reason in fallback_info.get("fallback_reasons", "").split("|")
                if reason
            ]
        )

        candidate_shortage_reason_counter.update(
            [
                reason
                for reason in fallback_info.get(
                    "candidate_pool_shortage_reasons", ""
                ).split("|")
                if reason
            ]
        )

        recommended_next_step = fallback_info.get("recommended_next_step")
        if recommended_next_step:
            recommended_next_step_counter[recommended_next_step] += 1

        total_selected_menu_count += selected_menu_count
        total_required_meal_count += required_meal_count
        total_unique_menu_count += unique_menu_count
        total_duplicate_menu_count += duplicate_menu_count
        total_available_recommendation_count += available_recommendation_count

        total_rag_mapping_event_count += (
            rag_mapping_info.get("rag_mapping_event_count", 0) or 0
        )
        total_rag_raw_menus += rag_mapping_info.get("rag_raw_menus", 0) or 0
        total_rag_mapped_menus += rag_mapping_info.get("rag_mapped_menus", 0) or 0
        total_rag_excluded_menus += (
            rag_mapping_info.get("rag_excluded_menus", 0) or 0
        )
        total_rag_quality_issue_menus += (
            rag_mapping_info.get("rag_quality_issue_menus", 0) or 0
        )

        rag_quality_issue_type_counter.update(
            rag_mapping_info.get("rag_quality_issue_type_count") or {}
        )

        rag_ingredient_group_mapping_status_counter.update(
            rag_mapping_info.get("rag_ingredient_group_mapping_status_count") or {}
        )

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

            "difficulty_feasibility_status": difficulty_feasibility_status,
            "difficulty_feasibility_reason": difficulty_feasibility_reason,
            "difficulty_candidate_count": difficulty_feasibility.get(
                "candidate_count"
            ),
            "difficulty_candidate_avg_difficulty": difficulty_feasibility.get(
                "candidate_avg_difficulty"
            ),
            "difficulty_candidate_p75_difficulty": difficulty_feasibility.get(
                "candidate_p75_difficulty"
            ),
            "difficulty_candidate_p90_difficulty": difficulty_feasibility.get(
                "candidate_p90_difficulty"
            ),
            "difficulty_candidate_max_difficulty": difficulty_feasibility.get(
                "candidate_max_difficulty"
            ),
            "difficulty_candidate_ge75_count": difficulty_feasibility.get(
                "candidate_ge75_count"
            ),
            "difficulty_candidate_ge65_count": difficulty_feasibility.get(
                "candidate_ge65_count"
            ),
            "difficulty_candidate_ge40_count": difficulty_feasibility.get(
                "candidate_ge40_count"
            ),
            "difficulty_candidate_eq0_count": difficulty_feasibility.get(
                "candidate_eq0_count"
            ),

            "duplicate_menu_warning_level": duplicate_warning.get("level"),
            "duplicate_menu_warning_rate": duplicate_warning.get("rate"),
            "duplicate_menu_recommended_maximum_rate": duplicate_warning.get(
                "recommended_maximum_rate"
            ),

            **optimizer_info,
            **fallback_info,
            **{
                key: value
                for key, value in rag_mapping_info.items()
                if key != "rag_quality_issue_type_count"
            },
            "rag_quality_issue_type_count_json": json.dumps(
                rag_mapping_info.get("rag_quality_issue_type_count") or {},
                ensure_ascii=False,
            ),
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
        "difficulty_feasibility_status_count": dict(
            difficulty_feasibility_status_counter
        ),
        "difficulty_feasibility_reason_count": dict(
            difficulty_feasibility_reason_counter
        ),
        "difficulty_candidate_shortage_count": (
            difficulty_feasibility_reason_counter.get(
                "candidate_difficulty_shortage",
                0,
            )
        ),
        "difficulty_absolute_pass_unreachable_count": (
            difficulty_feasibility_status_counter.get(
                "absolute_pass_unreachable",
                0,
            )
        ),
        "difficulty_pass_threshold_sparse_count": (
            difficulty_feasibility_status_counter.get(
                "pass_threshold_very_sparse",
                0,
            )
        ),
        "difficulty_candidate_pool_has_pass_options_count": (
            difficulty_feasibility_status_counter.get(
                "candidate_pool_has_pass_options",
                0,
            )
        ),
        "solver_status_count": dict(solver_status_counter),
        "solver_success_count": solver_success_count,
        "solver_success_rate": safe_rate(solver_success_count, scenario_count),
        "optimal_count": optimal_count,
        "optimal_rate": safe_rate(optimal_count, scenario_count),
        "feasible_count": feasible_count,
        "feasible_rate": safe_rate(feasible_count, scenario_count),
        "non_success_solver_count": non_success_solver_count,
        "non_success_solver_rate": safe_rate(
            non_success_solver_count,
            scenario_count,
        ),

        "failure_reason_count": dict(failure_reason_counter),

        "fallback_count": fallback_count,
        "fallback_rate": safe_rate(fallback_count, scenario_count),
        "fallback_reason_count": dict(fallback_reason_counter),

        "candidate_pool_enough_count": candidate_pool_enough_count,
        "candidate_pool_enough_rate": safe_rate(
            candidate_pool_enough_count,
            scenario_count,
        ),
        "candidate_pool_shortage_count": candidate_pool_shortage_count,
        "candidate_pool_shortage_rate": safe_rate(
            candidate_pool_shortage_count,
            scenario_count,
        ),
        "candidate_shortage_reason_count": dict(
            candidate_shortage_reason_counter
        ),
        "recommended_next_step_count": dict(recommended_next_step_counter),

        "validation_warning_count": validation_warning_count,
        "validation_warning_rate": safe_rate(
            validation_warning_count,
            scenario_count,
        ),
        "validation_fail_count": validation_fail_count,
        "validation_fail_rate": safe_rate(
            validation_fail_count,
            scenario_count,
        ),
        "duplicate_warning_count": duplicate_warning_count,
        "duplicate_warning_rate": safe_rate(
            duplicate_warning_count,
            scenario_count,
        ),

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

        "rag_mapping_event_count": total_rag_mapping_event_count,
        "rag_raw_menus": total_rag_raw_menus,
        "rag_mapped_menus": total_rag_mapped_menus,
        "rag_excluded_menus": total_rag_excluded_menus,
        "rag_quality_issue_menus": total_rag_quality_issue_menus,
        "rag_quality_issue_type_count": dict(rag_quality_issue_type_counter),
        "rag_ingredient_group_mapping_status_count": dict(
            rag_ingredient_group_mapping_status_counter
        ),
        "rag_mapping_success_rate": safe_rate(
            total_rag_mapped_menus,
            total_rag_raw_menus,
        ),
        "rag_quality_issue_rate": safe_rate(
            total_rag_quality_issue_menus,
            total_rag_mapped_menus,
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
