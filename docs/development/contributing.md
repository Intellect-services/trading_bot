---
title: Contributing Guide
---

# Contributing Guide

## Branching

- `main` – production-ready code.
- Feature branches use the format `feat/<feature-name>` or `fix/<bug>`.

## Pull Requests

Every PR should:

1. Reference the ticket/plan item it implements.
2. Include testing evidence (`pytest`, `ruff`, `mypy`).
3. Update docs if user-visible behavior changes.
4. Pass GitHub Actions (CI, security, docs build).

## Code Style

- Ruff handles formatting, linting, and import sorting.
- Type hints are enforced (`--disallow-untyped-defs`).
- Prefer dependency injection/service objects to tightly coupled modules.

## Commit Messages

Use concise, descriptive commits:

```
feat(risk): add Kelly sizing utility
fix(docs): correct dashboard route
```

## Communication

- Add status updates to the verification guide when manual QA is required.
- Document complex flows in `docs/` so the MkDocs site stays authoritative.
