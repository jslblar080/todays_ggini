import argparse
import json
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def extract_optimizer_snapshot(result: dict) -> dict | None:
    response = result.get("response") or {}
    monthly_plan = response.get("monthly_plan") or {}
    optimizer = monthly_plan.get("optimizer") or {}
    input_snapshot = optimizer.get("input_snapshot")

    if not input_snapshot:
        return None

    return {
        "scenario_id": result.get("scenario_id"),
        "description": result.get("description"),
        "purpose": result.get("purpose"),
        "profile": result.get("profile"),
        "selected_style": result.get("selected_style"),
        "optimizer_input": input_snapshot,
        "plan_summary": monthly_plan.get("summary"),
        "style_validation": monthly_plan.get("style_validation"),
        "fallback": monthly_plan.get("fallback"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract OR-Tools optimizer input snapshots from validation result."
    )
    parser.add_argument("--input", required=True, help="validation result json path")
    parser.add_argument("--output", required=True, help="snapshot output json path")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    data = read_json(input_path)
    results = data.get("results", [])

    snapshots = []
    missing = []

    for result in results:
        snapshot = extract_optimizer_snapshot(result)

        if snapshot:
            snapshots.append(snapshot)
        else:
            missing.append({
                "scenario_id": result.get("scenario_id"),
                "success": result.get("success"),
                "failure_stage": result.get("failure_stage"),
                "failure_reason": result.get("failure_reason"),
            })

    output = {
        "source": str(input_path),
        "experiment_name": data.get("experiment_name"),
        "planner": data.get("planner"),
        "created_at": data.get("created_at"),
        "total_result_count": len(results),
        "snapshot_count": len(snapshots),
        "missing_snapshot_count": len(missing),
        "snapshots": snapshots,
        "missing_snapshots": missing,
    }

    write_json(output_path, output)

    print("[INFO] optimizer snapshot extraction finished.")
    print("input:", input_path)
    print("output:", output_path)
    print("total_result_count:", len(results))
    print("snapshot_count:", len(snapshots))
    print("missing_snapshot_count:", len(missing))

    if missing:
        print()
        print("[WARN] missing snapshot scenarios:")
        for item in missing[:20]:
            print(
                "-",
                item.get("scenario_id"),
                "success=",
                item.get("success"),
                "failure_reason=",
                item.get("failure_reason"),
            )


if __name__ == "__main__":
    main()
