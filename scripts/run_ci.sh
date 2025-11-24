#!/bin/bash

# Exit on error
set -e

echo "Running CI checks..."

# Check code formatting with black
echo "Running black..."
black . --check --line-length 100

# Sort imports with isort
echo "Running isort..."
isort . --check-only --profile black

# Lint with flake8
echo "Running flake8..."
flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 src/ --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics

# Type checking with mypy
echo "Running mypy..."
mypy src/ --ignore-missing-imports --disallow-untyped-defs --strict

# Run tests with pytest
echo "Running pytest..."
pytest --cov=src --cov-report=term-missing

# Run security checks
echo "Running security checks..."
bandit -r src/ -c pyproject.toml
safety check --full-report

# Check for outdated packages
echo "Checking for outdated packages..."
pip list --outdated

echo "All CI checks passed successfully!"
