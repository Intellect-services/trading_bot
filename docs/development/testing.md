---
title: Testing & QA
---

# Testing & QA

## Python Tests

```bash
source venv/bin/activate
pytest
```

- Unit tests cover models, utilities, strategies, risk manager, and the Alpaca service.
- Integration tests (`tests/integration`) exercise the auth flow end-to-end (registration, verification, password reset).
- Coverage threshold is enforced via pytest’s `--cov` settings (fail under 70%).

## Frontend Checks

```bash
npm run lint --prefix frontend
npm run test --prefix frontend   # placeholder for React Testing Library suites
```

## Linters & Static Analysis

```bash
ruff check .
mypy src/ --ignore-missing-imports --disallow-untyped-defs
bandit -r src/
```

All of these run inside `.github/workflows/ci.yml` as part of the PR gate.

## Pre-commit

Install hooks locally:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Manual Verification

Use `VERIFICATION_GUIDE.md` for staging/production smoke tests (login, email, Alpaca integration, bot start/stop, dashboard rendering).
