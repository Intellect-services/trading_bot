## Email Marketing System Overview

This document captures the new branded marketing email system built on top of the existing Resend integration.

### Brand & Personalization Principles

- Every campaign injects IntellectScout brand guidelines (logo, gradients, typography, CTA styling) plus a hidden preheader for inbox previews.
- Messages are authored by a real persona (`Andrew from IntellectScout` by default) with configurable role, signature, reply-to, and unsubscribe links.
- Content is always tailored with the recipient's first name and contextual data (e.g., watchlists, new features, curriculum focus).

### Supported World-Class Use Cases

- **Welcome Series:** Three-step onboarding playbook guiding verification, brokerage linking, and first strategy launch.
- **Product Update:** Release spotlight with feature bullets, workflow highlights, and links to changelog/live dashboard.
- **Market Briefing:** Weekly macro pulse, watchlist, and risk guardrails to mirror institutional research updates.
- **Education Series:** Cohort-based curriculum plus live coaching CTA, mirroring SAAS customer success best practices.
- **Re-engagement:** Win-back narrative that preserves user progress, highlights missed features, and nudges resume action.

Each use case maps to `MarketingCampaignType` values and injects its own palette, hero badge, sections, and CTAs to keep designs unique while still on-brand.

### Implementation Notes

- Configuration lives in `src/config/constants.py` with env overrides for colors, persona, logo, and compliance links.
- Core logic resides in `src/services/marketing_email_service.py` with structured templates, personas, render pipeline, and new tracking hooks that log every attempt to `email_send_logs`.
- `MarketingEmailService.send_campaign(...)` accepts context overrides for first name, feature lists, urls, personas, etc., ensuring dynamic storytelling without duplicating templates.
- Persistent campaign + preference data is stored via:
  - `email_campaigns` (`src/models/email_campaign.py`) – scheduling metadata, cadences, and default seeds for the five core campaigns.
  - `email_preferences` (`src/models/email_preference.py`) – per-user opt-ins, unsubscribe tokens, and last-send timestamps.
  - `email_send_logs` (`src/models/email_send_log.py`) – audit trail for queued/sent/suppressed/failed attempts plus `last_event_*` telemetry.
  - `email_events` (`src/models/email_event.py`) – webhook events (delivered/opened/clicked/bounced) keyed to each send log.
- `/api/email/preferences` (GET/PUT), `/api/email/unsubscribe?token=...`, and `/api/email/resubscribe` power both authenticated settings and the public `/unsubscribe` landing page.
- `src/services/marketing_email_scheduler.py` + `scripts/run_marketing_scheduler.py` provide a polling worker that seeds campaigns, applies `audience_rules` (account age, inactivity, role filters), throttles sends, and keeps flows running continuously. The scheduler now ships in the `Procfile` as `scheduler: python scripts/run_marketing_scheduler.py`.
- `/api/email/webhooks/resend` (behind `RESEND_WEBHOOK_SECRET`) ingests provider callbacks, records `email_events`, and keeps `email_send_logs` synchronized.
- Unit tests under `tests/unit/test_marketing_email_service.py`, `tests/unit/test_email_preferences.py`, and `tests/unit/test_email_webhook.py` cover personalization, opt-out handling, preference APIs, and webhook ingestion.
