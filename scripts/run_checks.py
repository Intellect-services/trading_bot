#!/usr/bin/env python3
"""Unified quality gate for the project.

This script runs the same checks that we expect in CI:

- Ruff (lint)
- Mypy (types) for actively maintained slices
- Pytest with coverage
- Bandit (security) on supported slices
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str], *, name: str) -> int:
    """Run a command, streaming output, and return its exit code."""
    print("=" * 80)
    print(f"RUNNING: {name}")
    print("=" * 80)
    print(f"$ {' '.join(cmd)}")
    print()
    proc = subprocess.run(cmd, cwd=ROOT)
    print()
    print(f"{name} exited with code {proc.returncode}")
    print()
    return proc.returncode


def main() -> int:
    """Run all checks and fail fast on the first error."""
    checks: list[tuple[str, list[str]]] = [
        (
            "Ruff (lint)",
            ["ruff", "check", "."],
        ),
        (
            "Mypy (types, app/models/services/scripts)",
            [
                "mypy",
                "--config-file",
                "pyproject.toml",
                "src/app.py",
                "src/models",
                "src/services",
                "scripts/verify_implementation.py",
            ],
        ),
        (
            "Pytest (with coverage)",
            ["pytest"],
        ),
        (
            "Bandit (security, filtered via pyproject.toml)",
            ["bandit", "-c", "pyproject.toml", "-r", "src"],
        ),
    ]

    overall_rc = 0
    for name, cmd in checks:
        rc = run(cmd, name=name)
        if rc != 0:
            overall_rc = rc
            print(f"❌ {name} failed (exit code {rc})")
            break
        print(f"✅ {name} passed")

    if overall_rc == 0:
        print("=" * 80)
        print("✅ ALL CHECKS PASSED")
        print("=" * 80)
    else:
        print("=" * 80)
        print("⚠️  CHECKS FAILED")
        print("=" * 80)

    return overall_rc


if __name__ == "__main__":
    raise SystemExit(main())
