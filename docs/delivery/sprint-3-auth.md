# Sprint 3 — lock the door

**Status:** implemented, awaiting team review · **Owner:** Mark · **Reviewer:** Herman

The first thing that has ever protected this application. One login, two roles, and the
backend as the authority.

## Goal

Only the team can reach the pipeline, and what a person may do is decided by the API rather
than by what the frontend happens to render.

## Roles

Deliberately two:

| Role | Can |
|---|---|
| `admin` | Everything a seller can do, plus list application users |
| `sales` | Sign in, work the lead desk, import leads, record compliance decisions |

Sprint 3 does **not** build a permission matrix, invitations, deactivation, or role editing.
Those are later work; the user list is read-only.

## In scope

- Email and password login; generic failure that never reveals whether an account exists.
- Logout that invalidates the current token.
- `GET /auth/me` for the signed-in identity and role.
- Password change, and a forced change for bootstrap accounts.
- Bearer-token protection on every lead endpoint.
- `GET /users` for administrators only.
- Reversible `0003` migration for the `users` table.
- Idempotent development bootstrap of four administrator accounts.
- A responsive login screen, forced password-change screen, account menu and access-denied
  page in the existing Wadi visual system.

## Out of scope

Registration, invitations, password reset by email, multi-factor authentication, refresh
tokens, role editing, user deactivation, SSO, audit of login attempts, and any change to the
lead or compliance business rules.

## Design

- **JWT bearer tokens**, signed HS256, 8-hour lifetime. The same libraries FikaTu uses:
  `python-jose` and `passlib`/bcrypt.
- **`token_version` on the user.** Every token carries the version it was issued with.
  Logout and password change increment it, which invalidates every older token without a
  second table.
- **Backend authority.** `require_password_current` guards all lead routes and
  `require_admin` guards `/users`. Hiding a nav item is presentation, not control.
- **Forced first password change** is enforced by the API (403 on lead routes) as well as
  the frontend.
- **Reviewer identity comes from the session.** `reviewer` and `recorded_by` are accepted
  for compatibility but ignored; the API records the signed-in user's email. Imports
  record `imported_by` the same way.
- **Token storage is `localStorage`.** Simple and appropriate for this internal tool, but
  it is readable by any script on the page. A cookie-based session with CSRF protection is
  the hardening step if this is ever exposed beyond the team.
- **Development secret.** `JWT_SECRET_KEY` falls back to a documented development value;
  startup refuses that value outside `development`.

## Bootstrap accounts

Four administrators, created only in development, from `BOOTSTRAP_ADMIN_PASSWORD`:

- `hermangathege@kbc.co.ke`
- `sharonkendi@kbc.co.ke`
- `annewaithaka68@gmail.com`
- `markmwenesi@kbc.co.ke`

Rerunning the command never duplicates a user and never resets an existing password. Every
bootstrapped account must set its own password at first login.

## Acceptance criteria

- [x] Correct credentials return a token; wrong password and unknown email are
      indistinguishable 401s.
- [x] Passwords are bcrypt hashes; no hash or plaintext appears in a response.
- [x] Missing, malformed, expired and post-logout tokens are rejected.
- [x] Lead endpoints require a session; `/users` requires an administrator.
- [x] Sales can use the lead desk and receives 403 on `/users`.
- [x] A temporary-password account is refused business data until it changes its password.
- [x] Existing lead and compliance behaviour still works.
- [x] Bootstrap is idempotent and duplicate-safe.

## Known limitations

- No rate limiting or lockout on repeated failed logins yet.
- `localStorage` token storage (see Design).
- The five file groups (see the handover) share one long-lived sprint branch; review is by
  PR, not by deployment.
