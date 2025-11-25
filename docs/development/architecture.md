---
title: Architecture Overview
---

# Architecture Overview

## High-Level Components

| Layer                       | Description                                                                                              |
| --------------------------- | -------------------------------------------------------------------------------------------------------- |
| **Frontend (Vite + React)** | Auth pages, dashboard, bot monitor, account settings. Uses Axios with `withCredentials`.                 |
| **Backend (Flask)**         | REST APIs, Socket.IO, strategy/bot orchestration, encryption.                                            |
| **Trading Core**            | Strategies, risk manager, Alpaca service, market data streamer, backtesting engine.                      |
| **Storage**                 | SQLite (dev) / PostgreSQL (Railway). SQLAlchemy ORM for models (User, Strategy, Credential, EmailToken). |

## Data Flow

1. Frontend sends login/register requests → backend issues sessions.
2. Authenticated calls fetch dashboard data (`/api/dashboard/data`).
3. When the bot starts, it loads strategies, obtains user-specific Alpaca credentials, streams data, and records trades/logs.
4. Alpaca REST handles account/positions/orders; Data API/WS fetches bars for strategies.
5. `MarketDataStreamer` writes bars to SQLite; `DataProvider` falls back to cached/Yahoo/AlphaVantage data.
6. Backtesting engine and documentation share the same strategy/risk modules for consistency.

## Scripts & Tooling

- `scripts/isbot.sh` – orchestrates start/stop/restart/status/logs/db reset.
- `scripts/reset_db.py` – resets SQLite & recreates tables.
- GitHub Actions – CI, dependencies, security scans, docs deployment, Railway deployments.

## Extensibility Points

- **Strategies** – add new classes in `src/strategies/` and register them in `StrategyManager`.
- **Risk** – extend `RiskManager` for new sizing/drawdown rules.
- **Backtesting** – extend `BacktestEngine` metrics/reporting for ML or scenario analysis.
- **API** – modular blueprints under `src/api/` for future admin/strategy endpoints.
