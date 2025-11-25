---
title: Staging Deployment (Railway)
---

# Staging Deployment (Railway)

## 1. Provision Railway App

- Create a new project on [Railway](https://railway.app).
- Add a PostgreSQL plugin (or bring your own DB).
- Set environment variables under **Variables**:
  - `FLASK_ENV=production`
  - `SECRET_KEY`, `ENCRYPTION_KEY`
  - `RESEND_API_KEY`, `EMAIL_FROM`
  - `DATABASE_URL` (from Railway Postgres)
  - `SESSION_TYPE=redis` (if you attach Redis)

## 2. GitHub Action

`.github/workflows/deploy-staging.yml` handles:

- Installing dependencies
- Running linters/tests
- Deploying to Railway via `railway up`

Set the following secrets in GitHub:

| Secret           | Description       |
| ---------------- | ----------------- |
| `RAILWAY_TOKEN`  | Railway CLI token |
| `RESEND_API_KEY` | Email provider    |
| `ENCRYPTION_KEY` | Fernet key        |

## 3. Frontend

- Vite builds to `frontend/dist`.
- Flask serves the build automatically in production (`FRONTEND_DIST`).
- Ensure `VITE_API_URL` and `FRONTEND_URL` reflect the staging domain before building.

## 4. Domain

- Use Railway’s default staging domain or map `staging.intellectscout.com`.
- Update DNS to point the CNAME at Railway’s host.
- Set `site_url` in `mkdocs.yml` if you want the docs to link to staging endpoints.
