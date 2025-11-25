---
title: Data Models
---

# Data Models

## User

| Field                      | Type     | Notes                      |
| -------------------------- | -------- | -------------------------- |
| `id`                       | int      | Primary key                |
| `email`                    | string   | Unique, immutable          |
| `name`                     | string   | Display name               |
| `role`                     | string   | `trader`, `admin`, `owner` |
| `email_verified`           | bool     | Set after verification     |
| `created_at`, `updated_at` | datetime | Audit fields               |

## UserCredentials

| Field                         | Type     | Notes                     |
| ----------------------------- | -------- | ------------------------- |
| `alpaca_api_key_encrypted`    | string   | Encrypted with Fernet     |
| `alpaca_secret_key_encrypted` | string   | Encrypted                 |
| `trading_mode`                | string   | `paper` or `live`         |
| `is_active`                   | bool     | Set after successful test |
| `last_verified_at`            | datetime | Null until test succeeds  |

Use `UserCredentials.get_by_user_id(user_id)` helpers in backend services.

## EmailToken

Stores both verification and password-reset tokens:

| Field        | Type      | Notes                     |
| ------------ | --------- | ------------------------- |
| `token`      | string    | Random UUID               |
| `token_type` | string    | `verification` or `reset` |
| `expires_at` | datetime  | 24h expiry                |
| `used_at`    | datetime? | Null until consumed       |

## Strategy

| Field        | Type   | Notes                                        |
| ------------ | ------ | -------------------------------------------- |
| `type`       | string | `rsi`, `macd`, `bollinger`, `moving_average` |
| `parameters` | JSON   | Strategy-specific config                     |
| `is_active`  | bool   | Active flag                                  |

Default strategies are auto-provisioned if none exist for a user.

## Alpaca Account (external)

`GET /account` responses are normalized to floats (`portfolio_value`, `buying_power`, `cash`, `equity`, `last_equity`). Use this sanitized payload in the dashboard and bot to avoid Decimal issues.
