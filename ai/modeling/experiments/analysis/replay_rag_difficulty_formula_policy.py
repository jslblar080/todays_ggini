import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


POLICIES = {
    "baseline_current": {
        "exclude_estimated_usage_points": False,
        "relax_default_20min_time": False,
        "exclude_basic_action_points": False,
    },
    "exclude_estimated_usage": {
        "exclude_estimated_usage_points": True,
        "relax_default_20min_time": False,
        "exclude_basic_action_points": False,
    },
    "relax_default_20min_time": {
        "exclude_estimated_usage_points": False,
        "relax_default_20min_time": True,
        "exclude_basic_action_points": False,
    },
    "exclude_basic_action": {
        "exclude_estimated_usage_points": False,
        "relax_default_20min_time": False,
        "exclude_basic_action_points": True,
    },
    "combined_a_b_c": {
        "exclude_estimated_usage_points": True,
        "relax_default_20min_time": True,
        "exclude_basic_action_points": True,
    },
}


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None

    values = sorted(values)
    position = (len(values) - 1) * p
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(values) - 1)

    if lower_index == upper_index:
        return round(values[lower_index], 2)

    lower_value = values[lower_index]
    upper_value = values[upper_index]

    return round(
        lower_value + (upper_value - lower_value) * (position - lower_index),
        2,
    )


def average(values: list[float]) -> float | None:
    if not values:
        return None

    return round(sum(values) / len(values), 2)


def convert_points_to_difficulty(difficulty_points: int) -> int:
    if difficulty_points <= 1:
        return 1

    if difficulty_points <= 3:
        return 2

    if difficulty_points <= 5:
        return 3

    if difficulty_points <= 7:
        return 4

    return 5


def calculate_difficulty_score(raw_difficulty: int, cooking_skill: int) -> float:
    if raw_difficulty <= cooking_skill:
        return 100

    score = 100 - (raw_difficulty - cooking_skill) * 30
    return max(0, float(score))


def get_profile(monthly_plan: dict) -> dict:
    return (
        monthly_plan
        .get("optimizer", {})
        .get("input_snapshot", {})
        .get("profile", {})
    )


def get_snapshot_menus(monthly_plan: dict) -> list[dict]:
    return (
        monthly_plan
        .get("optimizer", {})
        .get("input_snapshot", {})
        .get("menus", [])
    )


def get_difficulty_detail(menu: dict) -> dict:
    raw_menu = menu.get("raw_menu") or {}
    return raw_menu.get("difficulty_detail") or {}


def replay_points(detail: dict, policy: dict) -> int:
    ingredient_points = int(detail.get("ingredient_points", 0) or 0)
    step_points = int(detail.get("step_points", 0) or 0)
    cooking_time_points = int(detail.get("cooking_time_points", 0) or 0)
    action_points = int(detail.get("action_points", 0) or 0)
    estimated_usage_points = int(detail.get("estimated_usage_points", 0) or 0)

    cooking_time = int(detail.get("cooking_time", 0) or 0)

    # 20분이 RAG mapping 기본값처럼 반복되는 경우를 가정한 실험 후보.
    if policy["relax_default_20min_time"] and cooking_time == 20:
        cooking_time_points = 0

    # 현재 detail에는 basic/heat/hard action별 점수가 분리되어 있지 않다.
    # 따라서 action_points가 1점인 경우 basic action으로 볼 가능성을 실험한다.
    # action_points가 2점인 경우 hard 또는 복합 동작 가능성이 있어 유지한다.
    if policy["exclude_basic_action_points"] and action_points == 1:
        action_points = 0

    if policy["exclude_estimated_usage_points"]:
        estimated_usage_points = 0

    return (
        ingredient_points
        + step_points
        + cooking_time_points
        + action_points
        + estimated_usage_points
    )


def build_rows(data: dict) -> list[dict]:
    rows = []

    for result in data.get("results", []):
        scenario_id = result.get("scenario_id")
        monthly_plan = (
            result
            .get("response", {})
            .get("monthly_plan", {})
        )
        profile = get_profile(monthly_plan)
        menus = get_snapshot_menus(monthly_plan)

        max_difficulty = profile.get("max_difficulty")
        cooking_skill = profile.get("cooking_skill") or max_difficulty or 3
        goals = "|".join(profile.get("goals") or [])

        for menu in menus:
            detail = get_difficulty_detail(menu)
            raw_menu = menu.get("raw_menu") or {}

            for policy_name, policy in POLICIES.items():
                replay_difficulty_points = replay_points(detail, policy)
                replay_raw_difficulty = convert_points_to_difficulty(
                    replay_difficulty_points
                )
                replay_difficulty_score = calculate_difficulty_score(
                    raw_difficulty=replay_raw_difficulty,
                    cooking_skill=int(cooking_skill or 3),
                )

                rows.append({
                    "scenario_id": scenario_id,
                    "policy_name": policy_name,
                    "max_difficulty": max_difficulty,
                    "cooking_skill": cooking_skill,
                    "goals": goals,
                    "menu_id": menu.get("menu_id"),
                    "name": menu.get("name"),

                    "baseline_difficulty_score": menu.get("difficulty_score"),
                    "baseline_raw_difficulty": raw_menu.get("difficulty"),
                    "baseline_difficulty_points": detail.get("difficulty_points"),

                    "replay_difficulty_score": replay_difficulty_score,
                    "replay_raw_difficulty": replay_raw_difficulty,
                    "replay_difficulty_points": replay_difficulty_points,

                    "ingredient_points": detail.get("ingredient_points"),
                    "step_points": detail.get("step_points"),
                    "cooking_time": detail.get("cooking_time"),
                    "cooking_time_points": detail.get("cooking_time_points"),
                    "action_points": detail.get("action_points"),
                    "estimated_usage_points": detail.get("estimated_usage_points"),
                })

    return rows


def summarize_rows(rows: list[dict]) -> dict:
    scores = [
        float(row["replay_difficulty_score"])
        for row in rows
    ]
    raw_difficulties = [
        float(row["replay_raw_difficulty"])
        for row in rows
    ]
    difficulty_points = [
        float(row["replay_difficulty_points"])
        for row in rows
    ]

    return {
        "menu_count": len(rows),
        "difficulty_score_avg": average(scores),
        "difficulty_score_p50": percentile(scores, 0.50),
        "difficulty_score_p75": percentile(scores, 0.75),
        "difficulty_score_p90": percentile(scores, 0.90),
        "difficulty_score_max": max(scores) if scores else None,
        "difficulty_score_bucket_count": {
            "ge75": sum(1 for score in scores if score >= 75),
            "ge65": sum(1 for score in scores if score >= 65),
            "ge40": sum(1 for score in scores if score >= 40),
            "eq0": sum(1 for score in scores if score == 0),
        },
        "raw_difficulty_avg": average(raw_difficulties),
        "raw_difficulty_p90": percentile(raw_difficulties, 0.90),
        "raw_difficulty_count": dict(Counter(str(int(v)) for v in raw_difficulties)),
        "difficulty_points_avg": average(difficulty_points),
        "difficulty_points_p90": percentile(difficulty_points, 0.90),
        "difficulty_points_count": dict(Counter(str(int(v)) for v in difficulty_points)),
    }


def build_group_summary(rows: list[dict]) -> dict:
    group_filters = {
        "all": lambda row: True,
        "low_skill": lambda row: row.get("max_difficulty") == 1,
        "easy_cooking_goal": lambda row: "간편식" in (row.get("goals") or ""),
        "low_skill_easy_cooking_goal": (
            lambda row: row.get("max_difficulty") == 1
            and "간편식" in (row.get("goals") or "")
        ),
        "US05_easy_cooking_low_skill": (
            lambda row: row.get("scenario_id") == "US05_easy_cooking_low_skill"
        ),
    }

    result = {}

    for group_name, group_filter in group_filters.items():
        result[group_name] = {}

        for policy_name in POLICIES:
            policy_rows = [
                row for row in rows
                if row["policy_name"] == policy_name
                and group_filter(row)
            ]
            result[group_name][policy_name] = summarize_rows(policy_rows)

    return result


def build_scenario_policy_rows(rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)

    for row in rows:
        grouped[(row["scenario_id"], row["policy_name"])].append(row)

    scenario_rows = []

    for (scenario_id, policy_name), scenario_policy_rows in grouped.items():
        summary = summarize_rows(scenario_policy_rows)
        first = scenario_policy_rows[0]

        bucket = summary["difficulty_score_bucket_count"]

        scenario_rows.append({
            "scenario_id": scenario_id,
            "policy_name": policy_name,
            "max_difficulty": first.get("max_difficulty"),
            "cooking_skill": first.get("cooking_skill"),
            "goals": first.get("goals"),
            "menu_count": summary["menu_count"],
            "difficulty_score_avg": summary["difficulty_score_avg"],
            "difficulty_score_p90": summary["difficulty_score_p90"],
            "difficulty_score_max": summary["difficulty_score_max"],
            "difficulty_score_ge75": bucket["ge75"],
            "difficulty_score_ge65": bucket["ge65"],
            "difficulty_score_ge40": bucket["ge40"],
            "difficulty_score_eq0": bucket["eq0"],
            "raw_difficulty_avg": summary["raw_difficulty_avg"],
            "raw_difficulty_p90": summary["raw_difficulty_p90"],
            "difficulty_points_avg": summary["difficulty_points_avg"],
            "difficulty_points_p90": summary["difficulty_points_p90"],
        })

    return sorted(
        scenario_rows,
        key=lambda row: (row["scenario_id"], row["policy_name"]),
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay RAG difficulty formula policy candidates."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--menu-csv", required=True)
    parser.add_argument("--scenario-csv", required=True)

    args = parser.parse_args()

    input_path = Path(args.input)
    output_json = Path(args.output_json)
    menu_csv = Path(args.menu_csv)
    scenario_csv = Path(args.scenario_csv)

    data = json.loads(input_path.read_text(encoding="utf-8"))
    rows = build_rows(data)

    result = {
        "summary": {
            "policy_names": list(POLICIES.keys()),
            "group_summary": build_group_summary(rows),
            "row_count": len(rows),
        },
        "scenario_rows": build_scenario_policy_rows(rows),
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    write_csv(menu_csv, rows)
    write_csv(scenario_csv, result["scenario_rows"])

    print("[INFO] RAG difficulty formula policy replay finished.")
    print(f"[INFO] input: {input_path}")
    print(f"[INFO] output json: {output_json}")
    print(f"[INFO] menu csv: {menu_csv}")
    print(f"[INFO] scenario csv: {scenario_csv}")
    print(f"[INFO] row_count: {len(rows)}")


if __name__ == "__main__":
    main()
