import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.modeling_service import create_monthly_plan
from services.style.meal_style_service import GOAL_STYLE_META


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
    scenario profile을 create_monthly_plan()이 받을 수 있는 request_data로 변환한다.

    build_user_profile_response() 내부의 UserProfileRequest는 profile 필드를 요구한다.
    따라서 사용자 입력값은 request_data 최상위가 아니라 request_data["profile"]에 담아 전달한다.
    """
    profile = scenario["profile"]
    selected_style = build_selected_style(profile)

    request_data = {
        "user_id": scenario["scenario_id"],
        "request_type": "monthly_plan",
        "profile": profile,
        "selected_style": selected_style,
    }

    return request_data


def run_one_scenario(scenario: dict) -> dict:
    """
    단일 시나리오에 대해 기존 MMR + Re-ranking 월간 식단 생성 로직을 실행한다.
    """
    scenario_id = scenario["scenario_id"]
    started_at = time.perf_counter()

    try:
        request_data = build_monthly_request(scenario)
        response = create_monthly_plan(request_data)

        runtime_ms = round((time.perf_counter() - started_at) * 1000, 2)

        return {
            "scenario_id": scenario_id,
            "description": scenario.get("description"),
            "purpose": scenario.get("purpose"),
            "planner": "baseline_mmr_reranking",
            "success": True,
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
            "planner": "baseline_mmr_reranking",
            "success": False,
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
    """실험 결과의 간단한 성공/실패 요약을 만든다."""
    total_count = len(results)
    success_count = sum(1 for result in results if result["success"])
    fail_count = total_count - success_count

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
        "success_count": success_count,
        "fail_count": fail_count,
        "success_rate": round(success_count / total_count, 4) if total_count else 0,
        "avg_runtime_ms": avg_runtime_ms,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="기존 MMR + Re-ranking 월간 식단 생성 baseline 실험을 실행한다."
    )
    parser.add_argument(
        "--scenario-file",
        required=True,
        help="사용자 시나리오 JSON 파일 경로",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="baseline 실행 결과 JSON 저장 경로",
    )

    args = parser.parse_args()

    scenario_data = load_json(args.scenario_file)
    scenarios = scenario_data.get("scenarios", [])

    if not scenarios:
        raise ValueError("실행할 scenarios가 없습니다.")

    results: list[dict[str, Any]] = []

    print(f"[INFO] baseline experiment start. scenario_count={len(scenarios)}")

    for index, scenario in enumerate(scenarios, start=1):
        scenario_id = scenario.get("scenario_id")
        description = scenario.get("description")

        print(f"[{index}/{len(scenarios)}] run {scenario_id} - {description}")

        result = run_one_scenario(scenario)
        results.append(result)

        if result["success"]:
            print(f"  success runtime_ms={result['runtime_ms']}")
        else:
            print(
                "  failed "
                f"runtime_ms={result['runtime_ms']} "
                f"error={result['error']}"
            )

    output_data = {
        "experiment_name": scenario_data.get(
            "experiment_name",
            "baseline_mmr_experiment",
        ),
        "planner": "baseline_mmr_reranking",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "summary": summarize_results(results),
        "results": results,
    }

    save_json(args.output, output_data)

    print("[INFO] baseline experiment finished.")
    print(f"[INFO] output saved: {args.output}")
    print(f"[INFO] summary: {output_data['summary']}")


if __name__ == "__main__":
    main()
