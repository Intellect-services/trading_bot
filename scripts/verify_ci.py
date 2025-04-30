#!/usr/bin/env python3
"""Script to verify CI workflow locally."""

import os
import subprocess
import sys
from typing import List, Tuple


def run_command(command: List[str]) -> Tuple[int, str]:
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        return result.returncode, result.stdout + result.stderr
    except Exception as e:
        return 1, str(e)


def main():
    """Main function to verify CI workflow."""
    # Step 1: Install dependencies
    print("Installing dependencies...")
    return_code, output = run_command(["pip", "install", "-r", "requirements.txt"])
    if return_code != 0:
        print(f"Error installing dependencies: {output}")
        sys.exit(1)

    # Step 2: Run code style checks
    print("\nRunning code style checks...")
    return_code, output = run_command(["black", "--check", "src", "tests"])
    if return_code != 0:
        print(f"Black found issues: {output}")
        sys.exit(1)

    # Step 3: Run linting
    print("\nRunning linting...")
    return_code, output = run_command(["flake8", "src", "tests"])
    if return_code != 0:
        print(f"Flake8 found issues: {output}")
        sys.exit(1)

    # Step 4: Run type checking
    print("\nRunning type checking...")
    return_code, output = run_command(["mypy", "src", "tests"])
    if return_code != 0:
        print(f"Mypy found issues: {output}")
        sys.exit(1)

    # Step 5: Run security checks
    print("\nRunning security checks...")
    return_code, output = run_command(["safety", "check"])
    if return_code != 0:
        print(f"Safety found issues: {output}")
        sys.exit(1)

    return_code, output = run_command(["bandit", "-r", "src", "tests"])
    if return_code != 0:
        print(f"Bandit found issues: {output}")
        sys.exit(1)

    # Step 6: Run tests
    print("\nRunning tests...")
    return_code, output = run_command(["pytest", "tests", "--cov=src"])
    if return_code != 0:
        print(f"Tests failed: {output}")
        sys.exit(1)

    print("\nAll checks passed successfully!")


if __name__ == "__main__":
    main()
