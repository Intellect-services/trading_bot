---
title: Production Deployment
---

# Production Deployment

## 1. Infrastructure

- Railway (or AWS/GCP) for the Flask API + Celery-equivalent workers.
- Managed PostgreSQL for persistence.
- Redis for server-side sessions and background jobs (optional).
- Resend for transactional email.
- CDN (Cloudflare) for static assets / docs.

## 2. Environment Variables

| Variable                       | Description                       |
| ------------------------------ | --------------------------------- |
| `FLASK_ENV=production`         | Enables production config.        |
| `SECRET_KEY`, `ENCRYPTION_KEY` | Must be long, random values.      |
| `DATABASE_URL`                 | Postgres connection string.       |
| `SESSION_TYPE=redis`           | Recommended for scale.            |
| `RESEND_API_KEY`, `EMAIL_FROM` | Email service.                    |
| `FRONTEND_URL`                 | `https://app.intellectscout.com`. |
| `ALPHA_VANTAGE_API_KEY`        | Optional fallback data source.    |

## 3. Build & Deploy

1. Push to `main`.
2. GitHub Actions runs:
   - `ci.yml` (lint, test, coverage)
   - `deploy-production.yml` (Railway deploy)
   - `docs.yml` (MkDocs → GitHub Pages)
3. Railway rebuilds the container and restarts the app.

## 4. Domain & TLS

- Point `intellectscout.com` (or subdomain) to Railway/GitHub Pages.
- Configure SSL via Railway or Cloudflare.
- Add `CNAME` to `docs/` deployment if you want docs on the root domain.

## 5. Observability

- Enable Railway logs + metrics.
- Consider shipping logs to a centralized sink (Logtail, Datadog).
- Health checks: `/health` (basic) and `/health/detailed` (DB/encryption/email).

## 6. Verification

Before promoting to production, run the checklist in `VERIFICATION_GUIDE.md` (auth flow, email, Alpaca integration, bot start/stop, dashboard rendering, docs availability).
