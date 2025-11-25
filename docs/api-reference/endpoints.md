---
title: REST Endpoints
---

# REST Endpoints

## Auth

### `POST /register`

```json
{
  "email": "user@example.com",
  "password": "StrongPass1!",
  "name": "Jane Doe"
}
```

Returns `{ "status": "success" }` on success.

### `POST /login`

JSON body: `{ "email": "...", "password": "..." }`
Sets a secure session cookie.

### `POST /logout`

Clears the session.

## Account

### `GET /api/auth/status`

Returns the current user, role, and feature flags (e.g., strategies enabled, bot state).

### `POST /api/account/credentials`

Stores encrypted Alpaca API keys:

```json
{
  "alpaca_api_key": "PK...",
  "alpaca_secret_key": "SK...",
  "trading_mode": "paper"
}
```

### `POST /api/account/credentials/test`

Hits Alpaca `/account` to ensure the keys work; sets `is_active=true` when successful.

## Bot

### `POST /api/bot/start`

Starts (or resumes) the user's trading bot. The bot:

- Streams market data via WebSocket
- Executes strategies
- Emits status updates to the frontend

### `POST /api/bot/stop`

Stops the running bot and detaches background workers.

## Dashboard

### `GET /api/dashboard/data`

Returns:

- `account` – computed floats (equity, buying power, cash).
- `performance` – win rate, total/daily PnL, Alpaca portfolio history points, Sharpe/Sortino.
- `positions` – active Alpaca positions.
- `status` – bot state + message.
