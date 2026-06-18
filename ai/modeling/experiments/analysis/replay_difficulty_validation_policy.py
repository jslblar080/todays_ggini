import argparse
import csv
import json
from pathlib import Path


POLICIES = {
    "current_absolute_75_65": {
        "pass_threshold": 75,
        "warning_threshold": 65,
        "use_candidate_feasibility": False,
    },
    "relaxed_absolute_65_50": {
        "pass_threshold": 65,
        "warning_threshold": 50,
        "use_candidate_feasibility": False,
    },
    "feasibility_aware_75_65": {
        "pass_threshold": 75,
        "warning_threshold": 65,
        "use_candidate_feasibility": True,
    },
    "feasibility_aware_65_50": {
        "pass_threshold": 65,
        "warning_threshold": 50,
        "use_candidate_feasibility": True,
    },
}


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None

    values = sorted(values)
    k = (len(values) - 1) * p
    f = int(k)
    c = min(f + 1, len(values) - 1)

    if f == c:
        return values[f]

    return values[f] + (values[c] - values[f]) * (k - f)


def get_candidate_scores(monthly_plan: dict) -> list[float]:
    snapshot = (
        monthly_plan
        .get("optimizer", {})
        .get("input_snapshot", {})
    )
    menus = snapshot.get("menus") or []

    return [
        float(menu.get("difficulty_score", 0) or 0)
        for menu in menus
    ]


def classify_policy(
    selected_avg: float,
    candidate_scores: list[float],
    pass_threshold: float,
    warning_threshold: float,
    use_candidate_feasibility: bool,
) -> tuple[str, str]:
    candidate_ge_pass = sum(1 for score in candidate_scores if score >= pass_threshold)
    candidate_p90 = percentile(candidate_scores, 0.90)

    if use_candidate_feasibility:
        if candidate_scores and candidate_ge_pass == 0:
            return "warning", "candidate_difficulty_shortage"

        if candidate_p90 is not None and candidate_p90 < warning_threshold:
            return "warning", "candidate_difficulty_sparse"

    if selected_avg >= pass_threshold:
        return "pass", "selected_meets_pass_threshold"

    if selected_avg >= warning_threshold:
        return "warning", "selected_meets_warning_threshold"

    return "fail", "selected_below_warning_threshold"


def build_rows(data: dict) -> list[dict]:
    rows = []

    for result in data.get("results", []):
        scenario_id = result.get("scenario_id")
        response = result.get("response") or {}
        selected_style = response.get("selected_style") or {}
        monthly_plan = response.get("monthly_plan") or {}
        summary = monthly_plan.get("summary") or {}
        style_validation = monthly_plan.get("style_validation") or {}

        selected_avg = float(summary.get("average_difficulty_score", 0) or 0)
        candidate_scores = get_candidate_scores(monthly_plan)

        candidate_p90 = percentile(candidate_scores, 0.90)
        candidate_max = max(candidate_scores) if candidate_scores else None

        for policy_name, policy in POLICIES.items():
            replay_status, replay_reason = classify_policy(
                selected_avg=selected_avg,
                candidate_scores=candidate_scores,
                pass_threshold=policy["pass_threshold"],
                warning_threshold=policy["warning_threshold"],
                use_candidate_feasibility=policy["use_candidate_feasibility"],
            )

            rows.append({
                "scenario_id": scenario_id,
                "policy_name": policy_name,
                "original_validation_status": style_validation.get("status"),
                "replay_status": replay_status,
                "replay_reason": replay_reason,
                "style_id": selected_style.get("style_id"),
                "focus_key": selected_style.get("focus_key"),
                "goals": (
                    monthly_plan
                    .get("optimizer", {})
                    .get("input_snapshot", {})
                    .get("profile", {})
                    .get("goals")
                ),
                "max_difficulty": (
                    monthly_plan
                    .get("optimizer", {})
                    .get("input_snapshot", {})
                    .get("profile", {})
                    .get("max_difficulty")
                ),
                "summary_avg_difficulty": selected_avg,
                "candidate_count": len(candidate_scores),
                "candidate_p90": round(candidate_p90, 2) if candidate_p90 is not None else None,
                "candidate_max": candidate_max,
                "candidate_ge_pass_threshold": sum(
                    1 for score in candidate_scores
                    if score >= policy["pass_threshold"]
                ),
                "candidate_ge_warning_threshold": sum(
                    1 for score in candidate_scores
                    if score >= policy["warning_threshold"]
                ),
                "pass_threshold": policy["pass_threshold"],
                "warning_threshold": policy["warning_threshold"],
                "use_candidate_feasibility": policy["use_candidate_feasibility"],
            })

    return rows


def init_policy_summary() -> dict:
    return {
        "pass": 0,
        "warning": 0,
        "fail": 0,
        "reason_count": {},
    }


def update_policy_summary(summary_by_policy: dict, row: dict) -> None:
    policy_name = row["policy_name"]

    if policy_name not in summary_by_policy:
        summary_by_policy[policy_name] = init_policy_summary()

    replay_status = row["replay_status"]
    replay_reason = row["replay_reason"]

    summary_by_policy[policy_name][replay_status] += 1

    reason_count = summary_by_policy[policy_name]["reason_count"]
    reason_count[replay_reason] = reason_count.get(replay_reason, 0) + 1


def summarize_group(rows: list[dict]) -> dict:
    summary_by_policy = {}

    for row in rows:
        update_policy_summary(summary_by_policy, row)

    return summary_by_policy


def summarize(rows: list[dict]) -> dict:
    focus_difficulty_rows = [
        row for row in rows
        if row.get("focus_key") == "difficulty"
    ]

    easy_cooking_goal_rows = [
        row for row in rows
        if "간편식" in (row.get("goals") or [])
    ]

    low_skill_rows = [
        row for row in rows
        if row.get("max_difficulty") == 1
    ]

    return {
        "policy_count": len(POLICIES),
        "scenario_count": len({row["scenario_id"] for row in rows}),
        "group_counts": {
            "all": len({row["scenario_id"] for row in rows}),
            "focus_difficulty": len({row["scenario_id"] for row in focus_difficulty_rows}),
            "easy_cooking_goal": len({row["scenario_id"] for row in easy_cooking_goal_rows}),
            "low_skill": len({row["scenario_id"] for row in low_skill_rows}),
        },
        "summary_by_policy_all": summarize_group(rows),
        "summary_by_policy_focus_difficulty": summarize_group(focus_difficulty_rows),
        "summary_by_policy_easy_cooking_goal": summarize_group(easy_cooking_goal_rows),
        "summary_by_policy_low_skill": summarize_group(low_skill_rows),
    }


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
        description="Replay difficulty validation policy candidates."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)

    args = parser.parse_args()

    input_path = Path(args.input)
    output_json = Path(args.output_json)
    output_csv = Path(args.output_csv)

    data = json.loads(input_path.read_text(encoding="utf-8"))
    rows = build_rows(data)

    result = {
        "summary": summarize(rows),
        "rows": rows,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    write_csv(output_csv, rows)

    print("[INFO] difficulty validation policy replay finished.")
    print(f"[INFO] input: {input_path}")
    print(f"[INFO] output json: {output_json}")
    print(f"[INFO] output csv: {output_csv}")
    print(f"[INFO] summary: {result['summary']}")


if __name__ == "__main__":
    main()
