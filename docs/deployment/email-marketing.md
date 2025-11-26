## Email Marketing Deployment Guide

This guide describes how to operate the branded marketing email system in production.

### 1. Database preparation

```bash
alembic upgrade head
python scripts/seed_marketing_emails.py
```

The migration chain creates:

- `email_campaigns` – per-campaign cadence and audience rules
- `email_preferences` – per-user opt-ins and unsubscribe tokens
- `email_send_logs` – audit logs for every send attempt
- `email_events` – webhook events (deliveries, opens, bounces)

The seed script ensures that every `MarketingCampaignType` is present and that all existing users have default preferences.

### 2. Required environment variables

| Variable | Purpose |
| --- | --- |
| `RESEND_API_KEY` | Auth token for the Resend API |
| `EMAIL_FROM` | From header used for transactional + marketing emails |
| `RESEND_WEBHOOK_SECRET` | HMAC secret used to validate `/api/email/webhooks/resend` payloads |
| `MARKETING_SCHEDULER_INTERVAL_SECONDS` | Polling interval for `scripts/run_marketing_scheduler.py` (defaults to 300 seconds) |
| `MARKETING_EMAIL_*` / `BRAND_*` | Optional overrides for brand colors, logos, persona, etc. |


### 3. Scheduler process

Add a long-running worker that executes `python scripts/run_marketing_scheduler.py` with the same env vars as the main web process. Examples:

- **Procfile (Heroku/Railway):**
  ```
  web: gunicorn ...
  scheduler: python scripts/run_marketing_scheduler.py
  ```
- **Docker Compose:**
  ```yaml
  marketing_scheduler:
    build: .
    command: python scripts/run_marketing_scheduler.py
    depends_on:
      db:
        condition: service_healthy
  ```

### 4. Webhook wiring

1. In the Resend dashboard, create a webhook pointing to `https://<your-domain>/api/email/webhooks/resend`.
2. Copy the signing secret and set `RESEND_WEBHOOK_SECRET`.
3. Verify events by sending a test payload—`EmailEvent` rows should appear and `email_send_logs.last_event_type` should update.

### 5. Frontend release

Marketing controls live inside the React frontend. Build the assets prior to deployment:

```bash
cd src/frontend
npm install
npm run build
```

Ship the generated `dist` directory (already referenced by Flask) alongside the backend release.
