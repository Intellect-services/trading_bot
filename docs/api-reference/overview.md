---
title: API Overview
---

# API Overview

All endpoints are served by the Flask application (default `http://localhost:5002`).

- Authentication uses server-side sessions with secure cookies.
- Responses are JSON, errors follow `{ "status": "error", "message": "..." }`.

## Core Routes

| Method | Path                            | Description                                                      |
| ------ | ------------------------------- | ---------------------------------------------------------------- |
| GET    | `/api/auth/status`              | Returns the logged-in user + feature flags.                      |
| POST   | `/login`                        | Session-based login.                                             |
| POST   | `/register`                     | Creates a user and triggers verification email.                  |
| POST   | `/api/account/credentials`      | Stores encrypted Alpaca credentials.                             |
| POST   | `/api/account/credentials/test` | Validates credentials and marks them active.                     |
| GET    | `/api/dashboard/data`           | Aggregated dashboard payload (account, performance, bot status). |
| POST   | `/api/bot/start`                | Starts the user’s trading bot.                                   |
| POST   | `/api/bot/stop`                 | Stops the bot.                                                   |

Refer to the sections below for parameter details.
