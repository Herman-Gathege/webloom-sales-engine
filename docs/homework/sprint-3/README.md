# Sprint 3 — team review homework

**What this is:** one review pass on the authentication sprint. Nobody implements a second
auth system. You are looking for what is wrong, missing, or risky in what is already here.

Read these first, in this order:

1. [Sprint 2 exit review](../sprint-2/status.md) — what closed, and what was left open.
2. [Sprint 3 scope](../../delivery/sprint-3-auth.md) — what this sprint promises.

## The design in one paragraph

Email and password sign-in returns an 8-hour JWT carrying the user id, role and token
version. The API is the authority: every lead route needs a session, `GET /users` needs an
`admin`, and a bootstrap account cannot read business data until it sets its own password.
Logout and password change bump `token_version`, which invalidates older tokens. Front doors:
`backend/app/auth.py`, `backend/app/api/v1/auth.py`, `frontend/src/auth/`.

## Everyone checks the same things

- Can any protected endpoint be reached without a token, with an expired one, or with a token
  issued before logout?
- Can a `sales` user reach `/api/v1/users` by calling it directly, not through the UI?
- Do the lead list, import and compliance review still behave exactly as they did in Sprint 2?
- Does anything expose a password hash, a token secret, or a temporary password?
- Is the login, forced password change, and access-denied experience understandable?

## Focus by person

**Mark — backend security.** Token signing and expiry, the `ver` claim, 401 vs 403
consistency, the timing path for unknown emails, and anything that could let a request claim
another reviewer. Check `backend/app/security.py` and `backend/app/auth.py`.

**Sharon — data integrity and regression.** The `0003` migration and its downgrade, bootstrap
idempotence, and that leads, provenance, eligibility and suppressions are untouched. Run the
backend suite and try importing a small file as a signed-in user.

**Anne — the seller's experience.** Sign in with a temporary password, set a new one, work the
lead desk, open a lead, and try an admin URL as a sales user. Report anything confusing in
plain language — especially whether the login and password screens make sense to someone who
does not care how tokens work.

**Herman — the whole picture.** Check that the documentation matches what the code does, that
the stated limitations are honest, and that review findings are triaged rather than collected.

## How to report a finding

One block per finding:

```
[severity: high/medium/low] file:line — what happens
  Reproduce: exact steps or request
  Expected: ...
  Actual: ...
```

High means a security bypass, data loss, or the lead desk unusable. Medium is a real bug with
a workaround. Low is polish. If you find nothing in your area, say "nothing to add" — that is
a result.

## Run it locally

```bash
# from the repo root
docker compose up --build

# create the four development admins (once; safe to repeat)
BOOTSTRAP_ADMIN_PASSWORD='set-your-own-temporary-password' \
  docker compose run --rm -e BOOTSTRAP_ADMIN_PASSWORD api python -m app.bootstrap

# and one sales account for the other half of the review
BOOTSTRAP_ADMIN_PASSWORD='set-your-own-temporary-password' \
  docker compose run --rm -e BOOTSTRAP_ADMIN_PASSWORD api python -m app.bootstrap --sales reviewer@example.test

# backend
docker compose build api && docker compose run --rm api-test
# frontend
cd frontend && npm run lint && npm test && npm run build
```

The app is at <http://localhost:5174>; the API docs at <http://localhost:8001/docs>.

## Rules

- Do not refactor unrelated code.
- Do not add features while reviewing; file them.
- Do not change a password for a teammate's account while testing; use your own.
- Bring findings to the review, not a rewritten auth layer.
