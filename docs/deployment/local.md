---
title: Local Deployment
---

# Local Deployment

## Prerequisites

- Python 3.10+
- Node 18+
- Resend API key (for email flows)

## Steps

1. Clone repo & install dependencies (`pip install -r requirements.txt`, `npm install --prefix frontend`).
2. Copy `.env.template` → `.env`. Use SQLite by default (no `DATABASE_URL`).
3. Start services:

```bash
./scripts/isbot.sh start
```

Frontend will launch on an available Vite port (5173/5174). Backend listens on `http://localhost:5002`.

## Useful Commands

```bash
./scripts/isbot.sh status       # show running processes and ports
./scripts/isbot.sh logs         # tail backend/frontend logs
./scripts/isbot.sh reset-db     # wipe SQLite (requires confirmation)
./scripts/isbot.sh stop         # stop everything
```

## Testing Emails

Set `RESEND_API_KEY` to a test key. Verification and password reset emails are sent via Resend’s sandbox.
