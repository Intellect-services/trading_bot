---
title: Account Management
---

# Account Management

## Profile

- Update display name and avatar (UI avatars) from the profile drawer (coming soon).
- Email addresses are immutable; use the admin console to change them if needed.

## Credentials

Each user has an encrypted `UserCredentials` record:

- Keys are encrypted with the Fernet key supplied via `ENCRYPTION_KEY`.
- Verification toggles the `is_active` field so the bot only uses validated API keys.
- `last_verified_at` helps detect stale keys.

## Roles & Permissions

- `trader` – default.
- `admin` – future management features (viewing user accounts, overriding bots).
- `owner` – reserved for the application owner; bootstrapped via `init_db`.

## Sessions & Security

- Flask-Session stores sessions server-side; cookies are HTTP-only.
- CSRF is handled at the API level through JSON requests (no classic form submissions).
- Rotate the `SECRET_KEY` and `SESSION_KEY_PREFIX` for production deployments.
