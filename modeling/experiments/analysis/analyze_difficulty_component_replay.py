import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


def points_to_raw_difficulty(points: int) -> int:
    if points <= 1:
        return 1
    if points <= 3:
        return 2
    if points <= 5:
        return 3
    if points <= 7:
        return 4
    return 5


def raw_to_low_skill_score(raw_difficulty: int) -> int:
    return {
        1: 100,
        2: 70,
        3: 40,
        4: 10,
        5: 0,
    }.get(raw_difficulty, 0)


def load_scenario(result_path: Path, scenario_id: str) -> dict:
    data = json.loads(result_path.read_text(encoding="utf-8"))

    for item in data.get("results", []):
        if item.get("scenario_id") == scenario_id:
            return item

    raise ValueError(f"scenario_id not found: {scenario_id}")


def get_optimizer_menus(scenario_result: dict) -> list[dict]:
    try:
        return scenario_result["response"]["monthly_plan"]["optimizer"]["input_snapshot"]["menus"]
    except KeyError as error:
        raise KeyError(
            "optimizer input_snapshot menus not found in result artifact"
        ) from error


def get_difficulty_detail(menu: dict) -> dict:
    raw_menu = menu.get("raw_menu") or {}
    return raw_menu.get("difficulty_detail") or {}


def summarize_components(menus: list[dict]) -> None:
    fields = [
        "ingredient_points",
        "step_points",
        "cooking_time_points",
        "action_points",
        "estimated_usage_points",
        "difficulty_points",
        "ingredient_count",
        "step_count",
        "cooking_time",
        "estimated_usage_ratio",
    ]

    values = defaultdict(list)
    difficulty_scores = []
    raw_difficulties = []

    for menu in menus:
        raw_menu = menu.get("raw_menu") or {}
        detail = get_difficulty_detail(menu)

        difficulty_scores.append(float(menu.get("difficulty_score", 0) or 0))
        raw_difficulties.append(raw_menu.get("difficulty"))

        for field in fields:
            values[field].append(detail.get(field))

    print("optimizer_candidate_count:", len(menus))
    print()

    print("difficulty_score_distribution:")
    print(dict(sorted(Counter(difficulty_scores).items())))
    print()

    print("raw_difficulty_distribution:")
    print(dict(sorted(Counter(raw_difficulties).items(), key=lambda item: str(item[0]))))
    print()

    for field in fields:
        nums = [value for value in values[field] if isinstance(value, (int, float))]
        print(f"=== {field} ===")
        print("count:", len(nums))
        if nums:
            print("avg:", round(mean(nums), 4))
            print("min:", min(nums))
            print("max:", max(nums))
            print("distribution:", dict(sorted(Counter(nums).items())))
        print()


def simulate_policy(menus: list[dict], policy_name: str, transform) -> dict:
    rows = []

    for menu in menus:
        detail = get_difficulty_detail(menu)

        ingredient = int(detail.get("ingredient_points", 0) or 0)
        step = int(detail.get("step_points", 0) or 0)
        time = int(detail.get("cooking_time_points", 0) or 0)
        action = int(detail.get("action_points", 0) or 0)
        usage = int(detail.get("estimated_usage_points", 0) or 0)

        ingredient, step, time, action, usage = transform(
            ingredient,
            step,
            time,
            action,
            usage,
        )

        points = ingredient + step + time + action + usage
        raw_difficulty = points_to_raw_difficulty(points)
        score = raw_to_low_skill_score(raw_difficulty)

        rows.append(
            {
                "name": menu.get("name"),
                "points": points,
                "raw_difficulty": raw_difficulty,
                "score": score,
                "components": {
                    "ingredient_points": ingredient,
                    "step_points": step,
                    "cooking_time_points": time,
                    "action_points": action,
                    "estimated_usage_points": usage,
                },
            }
        )

    scores = [row["score"] for row in rows]
    raw_difficulties = [row["raw_difficulty"] for row in rows]
    points = [row["points"] for row in rows]

    return {
        "policy": policy_name,
        "avg_score": round(mean(scores), 2),
        "score_distribution": dict(sorted(Counter(scores).items())),
        "raw_difficulty_distribution": dict(sorted(Counter(raw_difficulties).items())),
        "points_distribution": dict(sorted(Counter(points).items())),
        "ge75": sum(1 for score in scores if score >= 75),
        "ge65": sum(1 for score in scores if score >= 65),
        "ge40": sum(1 for score in scores if score >= 40),
        "eq0": sum(1 for score in scores if score == 0),
        "top_examples": sorted(rows, key=lambda row: row["score"], reverse=True)[:5],
    }


def run_policy_replay(menus: list[dict]) -> list[dict]:
    policies = [
        (
            "baseline_current",
            lambda ingredient, step, time, action, usage: (
                ingredient,
                step,
                time,
                action,
                usage,
            ),
        ),
        (
            "remove_estimated_usage_points",
            lambda ingredient, step, time, action, usage: (
                ingredient,
                step,
                time,
                action,
                0,
            ),
        ),
        (
            "cap_action_points_to_1",
            lambda ingredient, step, time, action, usage: (
                ingredient,
                step,
                time,
                min(action, 1),
                usage,
            ),
        ),
        (
            "remove_usage_and_cap_action_to_1",
            lambda ingredient, step, time, action, usage: (
                ingredient,
                step,
                time,
                min(action, 1),
                0,
            ),
        ),
        (
            "remove_usage_and_action_points",
            lambda ingredient, step, time, action, usage: (
                ingredient,
                step,
                time,
                0,
                0,
            ),
        ),
    ]

    return [
        simulate_policy(menus, policy_name, transform)
        for policy_name, transform in policies
    ]


def print_policy_results(results: list[dict]) -> None:
    for result in results:
        print(f"\n=== {result['policy']} ===")
        print("avg_score:", result["avg_score"])
        print("score_distribution:", result["score_distribution"])
        print("raw_difficulty_distribution:", result["raw_difficulty_distribution"])
        print("points_distribution:", result["points_distribution"])
        print("ge75:", result["ge75"])
        print("ge65:", result["ge65"])
        print("ge40:", result["ge40"])
        print("eq0:", result["eq0"])

        print("top examples:")
        for example in result["top_examples"]:
            print(
                "-",
                example["name"],
                "| score=",
                example["score"],
                "| raw=",
                example["raw_difficulty"],
                "| points=",
                example["points"],
                "| components=",
                example["components"],
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze difficulty component replay from final validation result artifact."
    )
    parser.add_argument("--result-path", required=True)
    parser.add_argument("--scenario-id", default="US05_easy_cooking_low_skill")
    parser.add_argument("--output-json")
    args = parser.parse_args()

    scenario_result = load_scenario(Path(args.result_path), args.scenario_id)
    menus = get_optimizer_menus(scenario_result)

    print(f"scenario_id: {args.scenario_id}")
    print()
    summarize_components(menus)

    policy_results = run_policy_replay(menus)
    print_policy_results(policy_results)

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(
                {
                    "scenario_id": args.scenario_id,
                    "optimizer_candidate_count": len(menus),
                    "policy_results": policy_results,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print()
        print(f"saved: {output_path}")


if __name__ == "__main__":
    main()
