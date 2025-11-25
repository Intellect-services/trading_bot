---
title: Trading Setup
---

# Trading Setup

## Alpaca Credentials

Each user stores their own Alpaca API key/secret:

1. Navigate to **Account → Alpaca**.
2. Paste key/secret from the Alpaca paper dashboard.
3. Click **Test Connection** – this encrypts the credentials, verifies them, and flips the “active” flag.
4. Once verified, the dashboard/bot gain access to Alpaca REST + WebSocket endpoints.

## Strategy Selection

Strategies are stored per user in the DB. When no active strategies exist the platform auto-creates:

- RSI Mean Reversion (per-symbol thresholds)
- MACD Trend (fast/slow EMA crossovers)
- Bollinger Bands Reversion

You can manage these entries via the Strategy API (or forthcoming UI) to adjust symbols, thresholds, and timeframes.

## Risk Configuration

Key parameters live in `RiskManager` and can be surfaced through settings:

- `risk_per_trade` – percent of equity risked per trade (default 1%).
- `max_drawdown` – stops the bot when equity drops more than the threshold.
- `max_daily_loss` – halts trades for the day if losses exceed the limit.
- Kelly & ATR sizing automatically use these limits when calculating quantities.

## Data Streaming & Caching

- Alpaca free WebSocket (IEX) streams bars; `MarketDataStreamer` saves each bar to SQLite.
- When Alpaca’s data API lacks access, the `DataProvider` falls back to cached bars, Yahoo Finance, or Alpha Vantage.
- The frontend chart pulls from `/api/dashboard/data`, which now uses Alpaca’s official portfolio history API, so performance charts match real account equity.
