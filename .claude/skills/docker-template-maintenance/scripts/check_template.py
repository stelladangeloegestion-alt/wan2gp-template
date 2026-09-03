#!/usr/bin/env python3
"""Static validation for this repo: bash syntax on every boot script, and
py_compile on every Python helper script. No Docker/GPU required.

Usage: python3 check_template.py
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]

SHELL_SCRIPTS = [
    "start-wan2gp.sh",
    "restart-wan2gp.sh",
    "startup.sh",
]

PYTHON_SCRIPTS = [
    "scripts/bootstrap_assets.py",
]


def main() -> int:
    failures = []

    for rel in SHELL_SCRIPTS:
        path = REPO_ROOT / rel
        if not path.exists():
            failures.append(f"{rel}: file not found")
            continue
        result = subprocess.run(
            ["bash", "-n", str(path)], capture_output=True, text=True
        )
        if result.returncode != 0:
            failures.append(f"{rel}: {result.stderr.strip()}")
        else:
            print(f"OK  bash -n {rel}")

    for rel in PYTHON_SCRIPTS:
        path = REPO_ROOT / rel
        if not path.exists():
            failures.append(f"{rel}: file not found")
            continue
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            failures.append(f"{rel}: {result.stderr.strip()}")
        else:
            print(f"OK  py_compile {rel}")

    if failures:
        print(f"\nFAIL: {len(failures)} issue(s):")
        for f in failures:
            print(f"  {f}")
        return 1

    print("\nAll shell scripts and Python helpers parse cleanly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
