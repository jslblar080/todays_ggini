import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]
MODELING_ROOT = PROJECT_ROOT / "ai" / "modeling"

REQUEST_VALIDATION_SCRIPT = (
    PROJECT_ROOT
    / "ai"
    / "modeling"
    / "experiments"
    / "contract"
    / "validate_backend_contract_requests.py"
)

RESPONSE_VALIDATION_SCRIPT = (
    PROJECT_ROOT
    / "ai"
    / "modeling"
    / "experiments"
    / "contract"
    / "validate_backend_contract_responses.py"
)


def build_env() -> dict[str, str]:
    env = os.environ.copy()

    existing_pythonpath = env.get("PYTHONPATH")

    if existing_pythonpath:
        env["PYTHONPATH"] = f"{MODELING_ROOT}:{existing_pythonpath}"
    else:
        env["PYTHONPATH"] = str(MODELING_ROOT)

    return env


def run_script(script_path: Path, env: dict[str, str]) -> None:
    print(f"[RUN] {script_path.relative_to(PROJECT_ROOT)}")

    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
    )


def main() -> None:
    env = build_env()

    run_script(REQUEST_VALIDATION_SCRIPT, env)
    run_script(RESPONSE_VALIDATION_SCRIPT, env)

    print("[OK] backend contract validation completed.")


if __name__ == "__main__":
    main()
