---
title: Development Setup
---

# Development Setup

## Requirements

- Python 3.10+
- Node 18+ (for Vite frontend)
- SQLite (bundled) or PostgreSQL (for Railway)

## Initial Steps

```bash
git clone https://github.com/betintellect-com/trading_bot.git
cd trading_bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
npm install --prefix frontend
```

## Environment

Copy `.env.template` to `.env` and update:

- `SECRET_KEY`, `ENCRYPTION_KEY`
- `RESEND_API_KEY`, `EMAIL_FROM`
- Optional OAuth client IDs
- `DATABASE_URL` for Postgres (Railway)

## Running Locally

```bash
./scripts/isbot.sh start
```

This script:

- Installs frontend deps (first run)
- Builds/serves Vite
- Launches Flask with auto-reload
- Starts Socket.IO and watches logs
