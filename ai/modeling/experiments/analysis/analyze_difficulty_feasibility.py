import argparse
import csv
import json
from pathlib import Path
from statistics import mean


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None

    sorted_values = sorted(values)
    k = (len(sorted_values) - 1) * p
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)

    if f == c:
        return sorted_values[f]

    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def safe_round(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def avg(values: list[float]) -> float | None:
    if not values:
        return None
    return round(mean(values), 2)


def get_candidate_scores(candidates: list[dict]) -> list[float]:
    return [
        float(menu.get("difficulty_score", 0) or 0)
        for menu in candidates
    ]


def get_raw_difficulties(candidates: list[dict]) -> list[float]:
    raw_values = []

    for menu in candidates:
        raw_menu = menu.get("raw_menu") or {}
        raw_difficulty = raw_menu.get("difficulty")

        if raw_difficulty is not None:
            raw_values.append(float(raw_difficulty))

    return raw_values


def build_row(result: dict) -> dict:
    scenario_id = result.get("scenario_id")

    response = result.get("response") or {}
    selected_style = response.get("selected_style") or {}

    monthly_plan = response.get("monthly_plan") or {}
    summary = monthly_plan.get("summary") or {}
    style_validation = monthly_plan.get("style_validation") or {}

    optimizer = monthly_plan.get("optimizer") or {}
    snapshot = optimizer.get("input_snapshot") or {}
    snapshot_profile = snapshot.get("profile") or {}
    candidates = snapshot.get("menus") or []

    candidate_scores = get_candidate_scores(candidates)
    raw_difficulties = get_raw_difficulties(candidates)

    candidate_p75 = percentile(candidate_scores, 0.75)
    candidate_p90 = percentile(candidate_scores, 0.90)

    required_meal_count = monthly_plan.get("required_meal_count")

    candidate_ge75 = sum(1 for score in candidate_scores if score >= 75)
    candidate_ge65 = sum(1 for score in candidate_scores if score >= 65)
    candidate_ge40 = sum(1 for score in candidate_scores if score >= 40)
    candidate_eq0 = sum(1 for score in candidate_scores if score == 0)

    feasibility_status = "unknown"

    if candidate_scores:
        if candidate_ge75 == 0:
            feasibility_status = "absolute_pass_unreachable"
        elif candidate_p90 is not None and candidate_p90 < 75:
            feasibility_status = "pass_threshold_very_sparse"
        else:
            feasibility_status = "candidate_pool_has_pass_options"

    return {
        "scenario_id": scenario_id,
        "validation_status": style_validation.get("status"),
        "style_id": selected_style.get("style_id"),
        "style_name": selected_style.get("style_name"),
        "focus_key": selected_style.get("focus_key"),
        "goals": snapshot_profile.get("goals"),
        "max_difficulty": snapshot_profile.get("max_difficulty"),
        "cooking_skill": snapshot_profile.get("cooking_skill"),
        "required_meal_count": required_meal_count,
        "candidate_count": len(candidate_scores),
        "summary_avg_difficulty": summary.get("average_difficulty_score"),
        "candidate_avg_difficulty": avg(candidate_scores),
        "candidate_p75_difficulty": safe_round(candidate_p75),
        "candidate_p90_difficulty": safe_round(candidate_p90),
        "candidate_max_difficulty": max(candidate_scores) if candidate_scores else None,
        "candidate_ge75_count": candidate_ge75,
        "candidate_ge65_count": candidate_ge65,
        "candidate_ge40_count": candidate_ge40,
        "candidate_eq0_count": candidate_eq0,
        "raw_difficulty_avg": avg(raw_difficulties),
        "raw_difficulty_p50": safe_round(percentile(raw_difficulties, 0.50)),
        "raw_difficulty_p90": safe_round(percentile(raw_difficulties, 0.90)),
        "feasibility_status": feasibility_status,
    }


def analyze(input_path: Path) -> dict:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    rows = [
        build_row(result)
        for result in data.get("results", [])
    ]

    status_count = {}
    feasibility_count = {}

    for row in rows:
        validation_status = row.get("validation_status")
        feasibility_status = row.get("feasibility_status")

        status_count[validation_status] = status_count.get(validation_status, 0) + 1
        feasibility_count[feasibility_status] = feasibility_count.get(feasibility_status, 0) + 1

    return {
        "summary": {
            "scenario_count": len(rows),
            "validation_status_count": status_count,
            "difficulty_feasibility_status_count": feasibility_count,
        },
        "rows": rows,
    }


def write_csv(output_csv: Path, rows: list[dict]) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        output_csv.write_text("", encoding="utf-8")
        return

    with output_csv.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze difficulty feasibility from final validation result JSON."
    )
    parser.add_argument("--input", required=True, help="Final validation result JSON path.")
    parser.add_argument("--output-json", required=True, help="Output summary JSON path.")
    parser.add_argument("--output-csv", required=True, help="Output CSV path.")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_json = Path(args.output_json)
    output_csv = Path(args.output_csv)

    result = analyze(input_path)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    write_csv(output_csv, result["rows"])

    print("[INFO] difficulty feasibility analysis finished.")
    print(f"[INFO] input: {input_path}")
    print(f"[INFO] output json: {output_json}")
    print(f"[INFO] output csv: {output_csv}")
    print(f"[INFO] summary: {result['summary']}")


if __name__ == "__main__":
    main()
