import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


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


def get_raw_menu(menu: dict) -> dict:
    return menu.get("raw_menu") or {}


def get_difficulty_detail(menu: dict) -> dict:
    raw_menu = get_raw_menu(menu)
    return raw_menu.get("difficulty_detail") or {}


def extract_menu_row(result: dict, menu: dict) -> dict:
    monthly_plan = (
        result
        .get("response", {})
        .get("monthly_plan", {})
    )
    profile = get_profile(monthly_plan)
    raw_menu = get_raw_menu(menu)
    detail = get_difficulty_detail(menu)

    scores = raw_menu.get("scores") or {}

    return {
        "scenario_id": result.get("scenario_id"),
        "description": result.get("description"),
        "max_difficulty": profile.get("max_difficulty"),
        "cooking_skill": profile.get("cooking_skill"),
        "goals": "|".join(profile.get("goals") or []),
        "preferred_categories": "|".join(profile.get("preferred_categories") or []),

        "menu_id": menu.get("menu_id"),
        "name": menu.get("name"),
        "final_score": menu.get("final_score"),
        "difficulty_score": menu.get("difficulty_score"),
        "raw_difficulty": raw_menu.get("difficulty"),
        "score_difficulty": scores.get("difficulty"),

        "ingredient_count": detail.get("ingredient_count"),
        "step_count": detail.get("step_count"),
        "cooking_time": detail.get("cooking_time"),
        "estimated_usage_ratio": detail.get("estimated_usage_ratio"),

        "ingredient_points": detail.get("ingredient_points"),
        "step_points": detail.get("step_points"),
        "cooking_time_points": detail.get("cooking_time_points"),
        "action_points": detail.get("action_points"),
        "estimated_usage_points": detail.get("estimated_usage_points"),
        "difficulty_points": detail.get("difficulty_points"),
    }


def build_rows(data: dict) -> list[dict]:
    rows = []

    for result in data.get("results", []):
        monthly_plan = (
            result
            .get("response", {})
            .get("monthly_plan", {})
        )
        menus = get_snapshot_menus(monthly_plan)

        for menu in menus:
            rows.append(extract_menu_row(result, menu))

    return rows


def numeric_values(rows: list[dict], key: str) -> list[float]:
    values = []

    for row in rows:
        value = row.get(key)
        if isinstance(value, (int, float)):
            values.append(float(value))

    return values


def count_by(rows: list[dict], key: str) -> dict:
    counter = Counter()

    for row in rows:
        value = row.get(key)
        if value is not None:
            counter[str(value)] += 1

    return dict(counter)


def summarize_rows(rows: list[dict]) -> dict:
    fields = [
        "difficulty_score",
        "raw_difficulty",
        "difficulty_points",
        "ingredient_points",
        "step_points",
        "cooking_time_points",
        "action_points",
        "estimated_usage_points",
        "ingredient_count",
        "step_count",
        "cooking_time",
        "estimated_usage_ratio",
    ]

    summary = {
        "menu_count": len(rows),
    }

    for field in fields:
        values = numeric_values(rows, field)

        summary[f"{field}_avg"] = average(values)
        summary[f"{field}_p50"] = percentile(values, 0.50)
        summary[f"{field}_p75"] = percentile(values, 0.75)
        summary[f"{field}_p90"] = percentile(values, 0.90)
        summary[f"{field}_max"] = max(values) if values else None

    summary["difficulty_score_bucket_count"] = {
        "ge75": sum(1 for row in rows if (row.get("difficulty_score") or 0) >= 75),
        "ge65": sum(1 for row in rows if (row.get("difficulty_score") or 0) >= 65),
        "ge40": sum(1 for row in rows if (row.get("difficulty_score") or 0) >= 40),
        "eq0": sum(1 for row in rows if (row.get("difficulty_score") or 0) == 0),
    }

    summary["raw_difficulty_count"] = count_by(rows, "raw_difficulty")
    summary["difficulty_points_count"] = count_by(rows, "difficulty_points")
    summary["cooking_time_points_count"] = count_by(rows, "cooking_time_points")
    summary["action_points_count"] = count_by(rows, "action_points")
    summary["estimated_usage_points_count"] = count_by(rows, "estimated_usage_points")

    return summary


def group_rows(rows: list[dict]) -> dict[str, list[dict]]:
    groups = {
        "all": rows,
        "low_skill": [
            row for row in rows
            if row.get("max_difficulty") == 1
        ],
        "easy_cooking_goal": [
            row for row in rows
            if "간편식" in (row.get("goals") or "")
        ],
        "low_skill_easy_cooking_goal": [
            row for row in rows
            if row.get("max_difficulty") == 1
            and "간편식" in (row.get("goals") or "")
        ],
        "US05_easy_cooking_low_skill": [
            row for row in rows
            if row.get("scenario_id") == "US05_easy_cooking_low_skill"
        ],
    }

    return groups


def build_scenario_summary(rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)

    for row in rows:
        grouped[row["scenario_id"]].append(row)

    scenario_rows = []

    for scenario_id, scenario_menus in grouped.items():
        summary = summarize_rows(scenario_menus)
        first = scenario_menus[0]

        scenario_rows.append({
            "scenario_id": scenario_id,
            "max_difficulty": first.get("max_difficulty"),
            "cooking_skill": first.get("cooking_skill"),
            "goals": first.get("goals"),
            "menu_count": summary["menu_count"],
            "difficulty_score_avg": summary["difficulty_score_avg"],
            "difficulty_score_p90": summary["difficulty_score_p90"],
            "difficulty_score_max": summary["difficulty_score_max"],
            "difficulty_score_ge75": summary["difficulty_score_bucket_count"]["ge75"],
            "difficulty_score_ge65": summary["difficulty_score_bucket_count"]["ge65"],
            "difficulty_score_ge40": summary["difficulty_score_bucket_count"]["ge40"],
            "difficulty_score_eq0": summary["difficulty_score_bucket_count"]["eq0"],
            "raw_difficulty_avg": summary["raw_difficulty_avg"],
            "raw_difficulty_p90": summary["raw_difficulty_p90"],
            "difficulty_points_avg": summary["difficulty_points_avg"],
            "ingredient_points_avg": summary["ingredient_points_avg"],
            "step_points_avg": summary["step_points_avg"],
            "cooking_time_points_avg": summary["cooking_time_points_avg"],
            "action_points_avg": summary["action_points_avg"],
            "estimated_usage_points_avg": summary["estimated_usage_points_avg"],
        })

    return sorted(scenario_rows, key=lambda row: row["scenario_id"])


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
        description="Analyze RAG difficulty mapping components from validation result."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--menu-csv", required=True)
    parser.add_argument("--scenario-csv", required=True)

    args = parser.parse_args()

    input_path = Path(args.input)
    output_json = Path(args.output_json)
    menu_csv_path = Path(args.menu_csv)
    scenario_csv_path = Path(args.scenario_csv)

    data = json.loads(input_path.read_text(encoding="utf-8"))
    rows = build_rows(data)

    grouped = group_rows(rows)
    group_summary = {
        group_name: summarize_rows(group_rows)
        for group_name, group_rows in grouped.items()
    }

    scenario_summary_rows = build_scenario_summary(rows)

    result = {
        "summary": {
            "group_summary": group_summary,
            "scenario_count": len(scenario_summary_rows),
            "menu_count": len(rows),
        },
        "scenario_rows": scenario_summary_rows,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    write_csv(menu_csv_path, rows)
    write_csv(scenario_csv_path, scenario_summary_rows)

    print("[INFO] RAG difficulty mapping analysis finished.")
    print(f"[INFO] input: {input_path}")
    print(f"[INFO] output json: {output_json}")
    print(f"[INFO] menu csv: {menu_csv_path}")
    print(f"[INFO] scenario csv: {scenario_csv_path}")
    print(f"[INFO] menu_count: {len(rows)}")
    print(f"[INFO] scenario_count: {len(scenario_summary_rows)}")


if __name__ == "__main__":
    main()
