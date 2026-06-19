import argparse
import json
from pathlib import Path


KEYS = [
    "success_rate",
    "solver_success_rate",
    "validation_fail_count",
    "validation_warning_count",
    "duplicate_warning_count",
    "unique_menu_ratio",
    "duplicate_rate",
    "meal_coverage_rate",
    "avg_runtime_ms",
    "p95_runtime_ms",
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def get_summary(data: dict) -> dict:
    return data.get("summary") or {}


def diff_value(base, target):
    if isinstance(base, (int, float)) and isinstance(target, (int, float)):
        return round(target - base, 6)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare two final validation summary JSON files."
    )
    parser.add_argument("--base", required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()

    base_path = Path(args.base)
    target_path = Path(args.target)

    base = get_summary(read_json(base_path))
    target = get_summary(read_json(target_path))

    print("=" * 100)
    print("[VALIDATION SUMMARY COMPARISON]")
    print("=" * 100)
    print("base:", base_path)
    print("target:", target_path)
    print()

    for key in KEYS:
        base_value = base.get(key)
        target_value = target.get(key)
        delta = diff_value(base_value, target_value)

        print(f"{key}:")
        print(f"  base   = {base_value}")
        print(f"  target = {target_value}")
        print(f"  delta  = {delta}")
        print()

    print("[STATUS COUNT]")
    print("base validation_status_count:", base.get("validation_status_count"))
    print("target validation_status_count:", target.get("validation_status_count"))
    print()
    print("base solver_status_count:", base.get("solver_status_count"))
    print("target solver_status_count:", target.get("solver_status_count"))


if __name__ == "__main__":
    main()
