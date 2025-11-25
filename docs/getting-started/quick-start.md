---
title: Quick Start
---

# Quick Start

This guide walks you through spinning up the IntellectScout trading bot with Alpaca’s free tier.

## 1. Clone & Install

```bash
git clone https://github.com/betintellect-com/trading_bot.git
cd trading_bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Configure Environment

Copy `.env.template` to `.env` and fill in at least:

```env
FLASK_ENV=development
SECRET_KEY=replace-me
ENCRYPTION_KEY=generated-fernet-key
RESEND_API_KEY=your-resend-key
EMAIL_FROM=noreply@intellectscout.com
```

Leave Alpaca keys blank initially; users enter their own credentials through the UI.

## 3. Start Services

```bash
./scripts/isbot.sh start
```

This launches:

- Flask backend on port 5002
- Vite frontend on whichever port is free (5173/5174)
- Socket.IO for real-time bot status

## 4. Register & Verify

1. Navigate to the frontend port.
2. Register a new account.
3. Confirm the verification email (Resend).
4. Sign in and open **Account → Alpaca** to add your API key/secret (free paper account).

## 5. Kick Off the Bot

- Configure preferred strategy symbols in **Settings**.
- Visit the dashboard; if credentials are verified, start the bot.
- The bot streams data via Alpaca’s free WebSocket, auto-saves bars, and generates signals.

## 6. Next Steps

- Review the [User Guide](../user-guide/authentication.md) for in-depth flows.
- Explore the [Deployment docs](../deployment/staging.md) to push to Railway.
- Run the full QA suite: `pytest`, `ruff check .`, `mypy src/`.
