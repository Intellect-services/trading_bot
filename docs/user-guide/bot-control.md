---
title: Bot Control
---

# Bot Control

## Starting the Bot

- Open the dashboard and ensure Alpaca credentials are verified.
- Click **Start Bot**; the server spins up a per-user `TradingBot`, subscribes to live data, and caches trades/logs.
- Status messages stream to the Bot Monitor via Socket.IO.

## Stopping & Restarting

- Use the UI controls or `./scripts/isbot.sh stop` to halt all services.
- The backend caches bot instances per user; stopping frees the streaming task but keeps persisted positions in the database.

## Monitoring

- **Dashboard Cards** – show equity, buying power, win rate, cumulative PnL.
- **Portfolio Performance Chart** – fed by Alpaca’s `/account/portfolio/history`.
- **Bot Monitor** – status feed with informational/warning/error messages emitted by the bot (market closed, API errors, data gaps, etc.).

## Logs & Alerts

- Structured logs output to console and `logs/` (if enabled).
- Status messages are capped to the latest 100 entries per user to keep the UI responsive.
- For staging/production, ship logs to a centralized sink (CloudWatch/Logtail) by setting `LOG_LEVEL` and handler configs.
