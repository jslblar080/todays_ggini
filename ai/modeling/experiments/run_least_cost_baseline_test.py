import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.modeling_service import (
    calculate_monthly_candidate_count,
    calculate_monthly_rag_candidate_multiplier,
    request_monthly_candidate_menus_with_fallback,
)

from services.optimizer.baselines.least_cost_baseline import (
    build_least_cost_monthly_plan,
)

from services.profile.profile_service import build_user_profile_response
from services.recommendation.recommendation_service import recommend_menus
from services.style.meal_style_service import GOAL_STYLE_META
from services.style.style_selection_service import (
    apply_selected_style_to_profile,
    build_selected_style_summary,
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


def build_selected_style(profile: dict) -> dict:
    """
    월간 식단 생성에는 selected_style이 필요하다.

    실제 서비스에서는 사용자가 3일 샘플 스타일 중 하나를 선택하지만,
    baseline 실험에서는 사용자 goals의 첫 번째 목표를 기준으로
    테스트용 selected_style을 자동 생성한다.
    """

    goals = profile.get("goals", [])

    if not goals:
        raise ValueError("profile.goals가 비어 있어 selected_style을 만들 수 없습니다.")

    source_goal = goals[0]
    style_meta = GOAL_STYLE_META.get(source_goal)

    if style_meta is None:
        raise ValueError(f"지원하지 않는 goal입니다: {source_goal}")

    return {
        **style_meta,
        "source_goal": source_goal,
        "is_support_style": False,
        "display_scores": {},
        "display_labels": {},
    }


def build_monthly_request(scenario: dict) -> dict:
    """
    scenario profile을 모델링 월간 식단 생성 흐름에서 사용할 request_data로 변환한다.
    """

    profile = scenario["profile"]
    selected_style = build_selected_style(profile)

    request_data = {
        "user_id": scenario["scenario_id"],
        "request_type": "monthly_plan",
        "profile": profile,
        "selected_style": selected_style,
        "use_ortools": False,
        "optimizer_config": scenario.get("optimizer_config", {}),
    }

    if "rag_candidate_multiplier" in scenario:
        request_data["rag_candidate_multiplier"] = scenario["rag_candidate_multiplier"]

    return request_data


def build_least_cost_response(
    request_data: dict,
    monthly_plan: dict,
    base_profile: dict,
    monthly_profile: dict,
    selected_style_summary: dict,
    fallback_info: dict,
    profiling: dict,
) -> dict:
    """
    Least-cost baseline 실험 결과를 기존 월간 응답과 비슷한 형태로 정리한다.
    """

    monthly_plan["fallback"] = fallback_info
    monthly_plan["profiling"] = profiling

    return {
        "user_id": request_data.get("user_id"),
        "request_type": "monthly_plan",
        "planner": "least_cost_diet_baseline",
        "failure_reason": monthly_plan.get("baseline", {}).get("failure_reason"),
        "selected_style": selected_style_summary,
        "modeling_profile": base_profile,
        "monthly_profile": monthly_profile,
        "meta": {
            "period_days": monthly_plan.get("period_days"),
            "meal_count_per_day": monthly_plan.get("meal_count_per_day"),
            "required_meal_count": monthly_plan.get("required_meal_count"),
            "available_recommendation_count": monthly_plan.get(
                "available_recommendation_count"
            ),
            "warnings": fallback_info.get("warnings", []),
            "fallback": fallback_info,
        },
        "monthly_plan": monthly_plan,
    }


def run_one_scenario(scenario: dict) -> dict:
    """
    단일 시나리오에 대해 Least-cost Diet baseline을 실행한다.
    """

    scenario_id = scenario["scenario_id"]
    started_at = time.perf_counter()
    profiling: dict[str, Any] = {}

    try:
        request_data = build_monthly_request(scenario)

        profile_started_at = time.perf_counter()

        profile_response = build_user_profile_response(
            request_data=request_data,
        )

        base_profile = profile_response["profile"]

        selected_style_summary = build_selected_style_summary(
            selected_style=request_data["selected_style"],
        )

        monthly_profile = apply_selected_style_to_profile(
            profile=base_profile,
            selected_style=selected_style_summary,
        )

        rag_candidate_multiplier = request_data.get("rag_candidate_multiplier")

        if rag_candidate_multiplier is not None:
            monthly_profile["rag_candidate_multiplier"] = rag_candidate_multiplier

        period_days = monthly_profile.get("period_days", 30)
        meal_count_per_day = monthly_profile.get("meal_count_per_day", 1)
        required_meal_count = period_days * meal_count_per_day

        profiling["profile_time_ms"] = round(
            (time.perf_counter() - profile_started_at) * 1000,
            2,
        )

        candidate_count = calculate_monthly_candidate_count(
            profile=monthly_profile,
        )

        profiling["rag_candidate_multiplier"] = calculate_monthly_rag_candidate_multiplier(
            monthly_profile
        )
        profiling["rag_candidate_request_count"] = candidate_count

        rag_started_at = time.perf_counter()

        candidate_menus, fallback_info = request_monthly_candidate_menus_with_fallback(
            request_data=request_data,
            profile=monthly_profile,
            candidate_count=candidate_count,
        )

        profiling["rag_request_total_time_ms"] = round(
            (time.perf_counter() - rag_started_at) * 1000,
            2,
        )

        recommendation_started_at = time.perf_counter()

        recommendations = recommend_menus(
            menus=candidate_menus,
            profile=monthly_profile,
            top_n=len(candidate_menus),
        )

        profiling["recommendation_time_ms"] = round(
            (time.perf_counter() - recommendation_started_at) * 1000,
            2,
        )

        baseline_started_at = time.perf_counter()

        monthly_plan = build_least_cost_monthly_plan(
            recommendations=recommendations,
            profile=monthly_profile,
            period_days=period_days,
            meal_count_per_day=meal_count_per_day,
        )

        profiling["least_cost_build_time_ms"] = round(
            (time.perf_counter() - baseline_started_at) * 1000,
            2,
        )

        profiling["total_modeling_time_ms"] = round(
            (time.perf_counter() - started_at) * 1000,
            2,
        )

        response = build_least_cost_response(
            request_data=request_data,
            monthly_plan=monthly_plan,
            base_profile=base_profile,
            monthly_profile=monthly_profile,
            selected_style_summary=selected_style_summary,
            fallback_info=fallback_info,
            profiling=profiling,
        )

        runtime_ms = round((time.perf_counter() - started_at) * 1000, 2)

        return {
            "scenario_id": scenario_id,
            "description": scenario.get("description"),
            "purpose": scenario.get("purpose"),
            "planner": "least_cost_diet_baseline",
            "success": True,
            "baseline_success": monthly_plan.get("baseline", {}).get("success"),
            "runtime_ms": runtime_ms,
            "error": None,
            "profile": scenario.get("profile"),
            "selected_style": request_data.get("selected_style"),
            "response": response,
        }

    except Exception as error:
        runtime_ms = round((time.perf_counter() - started_at) * 1000, 2)

        return {
            "scenario_id": scenario_id,
            "description": scenario.get("description"),
            "purpose": scenario.get("purpose"),
            "planner": "least_cost_diet_baseline",
            "success": False,
            "baseline_success": False,
            "runtime_ms": runtime_ms,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
            },
            "profile": scenario.get("profile"),
            "selected_style": None,
            "response": None,
        }


def summarize_results(results: list[dict]) -> dict:
    """실험 결과의 간단한 요약을 만든다."""

    total_count = len(results)
    runner_success_count = sum(1 for result in results if result["success"])
    runner_fail_count = total_count - runner_success_count

    baseline_success_count = sum(
        1 for result in results
        if result.get("baseline_success") is True
    )
    baseline_fail_count = total_count - baseline_success_count

    runtime_values = [
        result["runtime_ms"]
        for result in results
        if result.get("runtime_ms") is not None
    ]

    avg_runtime_ms = (
        round(sum(runtime_values) / len(runtime_values), 2)
        if runtime_values
        else 0
    )

    return {
        "total_count": total_count,
        "runner_success_count": runner_success_count,
        "runner_fail_count": runner_fail_count,
        "baseline_success_count": baseline_success_count,
        "baseline_fail_count": baseline_fail_count,
        "baseline_success_rate": (
            round(baseline_success_count / total_count, 4)
            if total_count
            else 0
        ),
        "avg_runtime_ms": avg_runtime_ms,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Least-cost Diet baseline 월간 식단 실험을 실행한다."
    )
    parser.add_argument(
        "--scenario-file",
        required=True,
        help="사용자 시나리오 JSON 파일 경로",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Least-cost baseline 실행 결과 JSON 저장 경로",
    )

    args = parser.parse_args()

    scenario_data = load_json(args.scenario_file)
    scenarios = scenario_data.get("scenarios", [])

    if not scenarios:
        raise ValueError("실행할 scenarios가 없습니다.")

    results: list[dict[str, Any]] = []

    print(f"[INFO] least-cost baseline experiment start. scenario_count={len(scenarios)}")

    for index, scenario in enumerate(scenarios, start=1):
        scenario_id = scenario.get("scenario_id")
        description = scenario.get("description")

        print(f"[{index}/{len(scenarios)}] run {scenario_id} - {description}")

        result = run_one_scenario(scenario)
        results.append(result)

        if result["success"]:
            print(
                "  success "
                f"baseline_success={result.get('baseline_success')} "
                f"runtime_ms={result['runtime_ms']}"
            )
        else:
            print(
                "  failed "
                f"runtime_ms={result['runtime_ms']} "
                f"error={result['error']}"
            )

    output_data = {
        "experiment_name": scenario_data.get(
            "experiment_name",
            "least_cost_baseline_experiment",
        ),
        "planner": "least_cost_diet_baseline",
        "description": "estimated_cost 기준 최저가 메뉴 선택 baseline 실험",
        "scenario_file": args.scenario_file,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "summary": summarize_results(results),
        "results": results,
    }

    save_json(args.output, output_data)

    print("[INFO] least-cost baseline experiment finished.")
    print(f"[INFO] output saved: {args.output}")
    print(f"[INFO] summary: {output_data['summary']}")


if __name__ == "__main__":
    main()
