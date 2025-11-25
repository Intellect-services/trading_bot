---
title: API Authentication
---

# API Authentication

## Session Cookies

- Standard username/password login persists a Flask session cookie.
- Axios on the frontend uses `withCredentials=true` so every API call carries the cookie.
- For non-browser clients, use the `/login` endpoint followed by subsequent requests in the same session.

## CSRF & Security

- All mutating endpoints accept JSON payloads.
- Cookies are HTTP-only; avoid storing tokens in localStorage.
- For production, serve over HTTPS (Railway + custom domain).
- Rotate the `SECRET_KEY` and keep `SESSION_COOKIE_SECURE=True` when behind TLS.

## API Tokens (Future)

The architecture supports adding PATs for programmatic access. Extend the `User` model and add a Bearer auth guard if needed.
