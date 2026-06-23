import json
from pathlib import Path
from statistics import mean
from typing import Any


RESULT_FILES = [
    {
        "label": "rag_3_0",
        "path": "ai/modeling/experiments/results/ortools_rag_3_0_request_result.json",
    },
    {
        "label": "rag_2_9",
        "path": "ai/modeling/experiments/results/ortools_rag_2_9_request_result.json",
    },
    {
        "label": "rag_2_8",
        "path": "ai/modeling/experiments/results/ortools_rag_2_8_request_result.json",
    },
    {
        "label": "rag_2_7",
        "path": "ai/modeling/experiments/results/ortools_rag_2_7_request_result.json",
    },
    {
        "label": "rag_2_6",
        "path": "ai/modeling/experiments/results/ortools_rag_2_6_request_result.json",
    },
    {
        "label": "rag_2_5",
        "path": "ai/modeling/experiments/results/ortools_rag_2_5_request_result.json",
    },
    {
        "label": "rag_2_4",
        "path": "ai/modeling/experiments/results/ortools_rag_2_4_request_result.json",
    },
    {
        "label": "rag_2_3",
        "path": "ai/modeling/experiments/results/ortools_rag_2_3_request_result.json",
    },
    {
        "label": "rag_2_0",
        "path": "ai/modeling/experiments/results/ortools_rag_2_0_request_result.json",
    },
    {
        "label": "rag_1_5",
        "path": "ai/modeling/experiments/results/ortools_rag_1_5_request_result.json",
    },
    {
        "label": "rag_1_2",
        "path": "ai/modeling/experiments/results/ortools_rag_1_2_request_result.json",
    },
]


def load_json(path: str) -> dict:
    """JSON 파일을 읽어 dict로 반환한다."""
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def safe_get(data: dict, *keys: str, default: Any = None) -> Any:
    """중첩 dict에서 안전하게 값을 꺼낸다."""
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)

    return current if current is not None else default


def round_number(value: Any, digits: int = 2) -> Any:
    """숫자면 반올림하고, 아니면 그대로 반환한다."""
    if isinstance(value, (int, float)):
        return round(value, digits)
    return value


def is_modeling_success(response: dict) -> bool:
    """
    모델링 성공 여부를 판단한다.

    현재 성공 응답에는 success 키가 없고,
    실패 응답에는 success=false와 failure_reason이 포함된다.
    따라서 failure_reason이 없으면 성공으로 판단한다.
    """
    return response.get("failure_reason") is None


def extract_row(label: str, result: dict) -> dict:
    """단일 시나리오 결과에서 비교용 row를 추출한다."""
    response = result.get("response") or {}
    monthly_plan = response.get("monthly_plan") or {}
    meta = response.get("meta") or {}
    profiling = monthly_plan.get("profiling") or {}
    summary = monthly_plan.get("summary") or {}
    optimizer = monthly_plan.get("optimizer") or {}
    optimizer_config = optimizer.get("config") or {}
    style_validation = monthly_plan.get("style_validation") or {}

    modeling_success = is_modeling_success(response)

    return {
        "experiment": label,
        "scenario_id": result.get("scenario_id"),
        "runner_success": result.get("success"),
        "modeling_success": modeling_success,
        "failure_reason": response.get("failure_reason"),
        "runtime_ms": result.get("runtime_ms"),
        "runtime_sec": round_number((result.get("runtime_ms") or 0) / 1000),
        "required_meal_count": meta.get("required_meal_count") or monthly_plan.get("required_meal_count"),
        "available_recommendation_count": (
            meta.get("available_recommendation_count")
            or monthly_plan.get("available_recommendation_count")
        ),
        "rag_candidate_multiplier": profiling.get("rag_candidate_multiplier"),
        "rag_candidate_request_count": profiling.get("rag_candidate_request_count"),
        "rag_request_total_time_ms": profiling.get("rag_request_total_time_ms"),
        "ortools_solver_time_ms": profiling.get("ortools_solver_time_ms"),
        "total_modeling_time_ms": profiling.get("total_modeling_time_ms"),
        "solver_status": optimizer.get("solver_status"),
        "solver_time_limit_seconds": optimizer_config.get("solver_time_limit_seconds"),
        "used_optimizer_candidate_count": optimizer_config.get("used_optimizer_candidate_count"),
        "optimizer_candidate_multiplier": optimizer_config.get("optimizer_candidate_multiplier"),
        "selected_menu_count": summary.get("selected_menu_count"),
        "unique_menu_count": summary.get("unique_menu_count"),
        "duplicate_menu_count": summary.get("duplicate_menu_count"),
        "total_estimated_cost": summary.get("total_estimated_cost"),
        "average_daily_cost": summary.get("average_daily_cost"),
        "average_nutrition_score": summary.get("average_nutrition_score"),
        "average_budget_score": summary.get("average_budget_score"),
        "average_preference_score": summary.get("average_preference_score"),
        "average_difficulty_score": summary.get("average_difficulty_score"),
        "average_diversity_score": summary.get("average_diversity_score"),
        "style_validation_status": style_validation.get("status"),
    }


def print_table(rows: list[dict], columns: list[str]) -> None:
    """간단한 콘솔 테이블을 출력한다."""
    widths = {}

    for column in columns:
        widths[column] = max(
            len(column),
            max((len(str(row.get(column, ""))) for row in rows), default=0),
        )

    header = " | ".join(column.ljust(widths[column]) for column in columns)
    divider = "-+-".join("-" * widths[column] for column in columns)

    print(header)
    print(divider)

    for row in rows:
        print(" | ".join(str(row.get(column, "")).ljust(widths[column]) for column in columns))


def summarize_by_experiment(rows: list[dict]) -> list[dict]:
    """실험별 요약 지표를 계산한다."""
    summaries = []

    labels = []
    for row in rows:
        label = row["experiment"]
        if label not in labels:
            labels.append(label)

    for label in labels:
        group = [row for row in rows if row["experiment"] == label]
        success_group = [row for row in group if row["modeling_success"]]

        avg_runtime_ms = mean(row["runtime_ms"] for row in group if row["runtime_ms"] is not None)
        avg_runtime_sec = avg_runtime_ms / 1000

        summary = {
            "experiment": label,
            "total_count": len(group),
            "runner_success_count": sum(1 for row in group if row["runner_success"]),
            "modeling_success_count": len(success_group),
            "modeling_fail_count": len(group) - len(success_group),
            "modeling_success_rate": round(len(success_group) / len(group), 3) if group else 0,
            "avg_runtime_sec": round(avg_runtime_sec, 2),
            "avg_available_count": round(
                mean(row["available_recommendation_count"] for row in group if row["available_recommendation_count"] is not None),
                2,
            ),
        }

        if success_group:
            summary.update(
                {
                    "avg_rag_request_count": round(
                        mean(row["rag_candidate_request_count"] for row in success_group if row["rag_candidate_request_count"] is not None),
                        2,
                    ),
                    "avg_solver_time_sec": round(
                        mean(row["ortools_solver_time_ms"] for row in success_group if row["ortools_solver_time_ms"] is not None) / 1000,
                        2,
                    ),
                    "avg_duplicate_menu_count": round(
                        mean(row["duplicate_menu_count"] for row in success_group if row["duplicate_menu_count"] is not None),
                        2,
                    ),
                    "avg_unique_menu_count": round(
                        mean(row["unique_menu_count"] for row in success_group if row["unique_menu_count"] is not None),
                        2,
                    ),
                    "avg_preference_score": round(
                        mean(row["average_preference_score"] for row in success_group if row["average_preference_score"] is not None),
                        2,
                    ),
                    "avg_budget_score": round(
                        mean(row["average_budget_score"] for row in success_group if row["average_budget_score"] is not None),
                        2,
                    ),
                }
            )
        else:
            summary.update(
                {
                    "avg_rag_request_count": None,
                    "avg_solver_time_sec": None,
                    "avg_duplicate_menu_count": None,
                    "avg_unique_menu_count": None,
                    "avg_preference_score": None,
                    "avg_budget_score": None,
                }
            )

        summaries.append(summary)

    return summaries


def save_json(path: str, data: Any) -> None:
    """결과 데이터를 JSON 파일로 저장한다."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def main() -> None:
    rows = []

    for item in RESULT_FILES:
        data = load_json(item["path"])

        for result in data.get("results", []):
            rows.append(extract_row(item["label"], result))

    summaries = summarize_by_experiment(rows)

    print("\n=== RAG 요청 수 실험 요약 ===")
    print_table(
        summaries,
        [
            "experiment",
            "total_count",
            "runner_success_count",
            "modeling_success_count",
            "modeling_fail_count",
            "modeling_success_rate",
            "avg_runtime_sec",
            "avg_available_count",
            "avg_rag_request_count",
            "avg_solver_time_sec",
            "avg_duplicate_menu_count",
            "avg_unique_menu_count",
            "avg_preference_score",
            "avg_budget_score",
        ],
    )

    print("\n=== 시나리오별 상세 결과 ===")
    print_table(
        rows,
        [
            "experiment",
            "scenario_id",
            "modeling_success",
            "failure_reason",
            "runtime_sec",
            "available_recommendation_count",
            "rag_candidate_request_count",
            "solver_status",
            "selected_menu_count",
            "unique_menu_count",
            "duplicate_menu_count",
            "average_preference_score",
            "average_budget_score",
        ],
    )

    output = {
        "summary": summaries,
        "rows": rows,
    }

    output_path = "ai/modeling/experiments/results/compare_rag_request_results_summary.json"
    save_json(output_path, output)

    print(f"\n[INFO] 비교 결과 저장 완료: {output_path}")


if __name__ == "__main__":
    main()
