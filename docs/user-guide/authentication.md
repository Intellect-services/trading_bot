---
title: Authentication & Accounts
---

# Authentication & Accounts

## Registration

- Users register via the React frontend.
- Upon submission, the backend issues a verification token and sends a Resend email.
- The UI redirects to `/verify-email` so the user can resend the link or go back to login.

## Email Verification Flow

1. User clicks the verification link.
2. Backend validates the token, marks the account as verified, and redirects back to `/login?verified=true`.
3. The login page shows a “Email verified” toast.

## OAuth (Optional)

The plan supports future OAuth providers (Google, GitHub, LinkedIn). These endpoints are scaffolded; populate client IDs/secrets through environment variables to enable them.

## Session Handling

- Flask-Session stores server-side sessions (filesystem in dev, Redis in production).
- `@login_required` protects API routes; React uses Axios with `withCredentials` to keep cookies in sync.
- The `/api/auth/status` endpoint powers the frontend auth context.

## Password Reset

1. User clicks “Forgot Password?”.
2. Backend sends a reset link via Resend.
3. `/reset-password?token=...` lets the user set a new password and redirects to login with `reset=true`.

## Roles & RBAC

Roles live on the `User` model (`trader`, `admin`, `owner`).

- **Trader** – default; can manage their own Alpaca credentials and run the bot.
- **Admin/Owner** – reserved for future management features (multi-user dashboards, team controls).
