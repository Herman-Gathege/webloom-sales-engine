# Sprint 3 — exit review

**Decision:** ready to close on merge of
[PR #26](https://github.com/Herman-Gathege/webloom-sales-engine/pull/26).
**Reviewed:** 2026-11-02 · **Branch:** `feature/sprint-3-solidification`

This is the evidence behind the closeout decision. Sprint 3 combines the authentication
foundation with the CSV-to-outreach compliance boundary.

## What shipped

| Piece | State |
|---|---|
| Email/password login, logout and current-user session | Shipped |
| `admin` and `sales` roles enforced by the API | Shipped |
| Forced first-login password change | Shipped |
| Idempotent four-admin development bootstrap | Shipped |
| Reversible user migration `0003` | Shipped |
| Durable lead compliance evaluation and outreach readiness gate | Shipped |
| Independent human review and terminal suppression | Shipped |
| Reversible compliance migration `0004` | Shipped |
| Server-side compliance, provenance, quality and batch filters | Shipped |
| Responsive card lists and aligned filter grid | Shipped |
| Explicit opt-in demo seeding | Shipped |

## Evidence

- **Backend:** 181 tests pass against PostgreSQL 17 and Python 3.12; Ruff is clean.
- **Frontend:** 39 tests pass; lint is clean; the production build succeeds.
- **Migrations:** `0003` and `0004` are covered by the upgrade/downgrade/upgrade test.
- **Current dataset:** 52 imported leads, one import batch, 52 provenance rows, and 156
  channel-review rows. Every lead is `needs_review`; no channel is eligible and no
  suppression exists.
- **Responsive acceptance:** at 390px the Lead Desk renders 25 cards, no visible table
  container and no horizontal page overflow. Filter geometry has equal column widths and
  no overlaps at 640, 768, 1024, 1280, and 1440px.
- **CI:** PR #26 is mergeable with Backend and Frontend checks successful.

## Accepted deviations

1. **Development roles:** all four bootstrap accounts are administrators. Role editing is
   outside Sprint 3; production allocation remains a team decision.
2. **Token storage:** JWTs use `localStorage`. This is acceptable for the internal local
   prototype and documented for hardening before broader exposure.
3. **Authentication hardening:** login rate limiting, lockout, login-attempt audit,
   refresh tokens, password reset and MFA remain later work.
4. **Compliance policy:** lawful basis, DPIA/registration, retention, processor terms and
   final opt-out wording require human or professional decisions before real outreach.
5. **Sending boundary:** campaigns, approval, FikaTu delivery, retries and inbound replies
   remain Sprint 5–7 work. Sprint 3 ends at the outreach-readiness gate.
6. **Bulk approval:** not implemented. Any future bulk action must preserve an individual
   current decision for every lead.
7. **GitHub enforcement:** CI checks are green but branch protection remains an
   administrator action.

## Missing provenance

The current import has a real source name and collection method, so its data-quality label
is `complete`. It does not contain source URLs, provenance-level purposes or useful contact
types. Every lead correctly remains in human review; no missing evidence was invented.

## One keep, one change

- **Keep:** every imported row produces a durable, explainable compliance result before it
  can enter outreach.
- **Change:** demo data is opt-in, so restarting the application can never contaminate a
  real import.

## Carried into Sprint 4

- obtain lawful-basis and retention decisions before real outreach;
- sign off the screen, approval and handoff inventory;
- complete the FikaTu event/status/retry contract before Sprint 6;
- decide the final Admin/Sales allocation and user-management workflow;
- add broader security hardening before deployment.

## Closure checklist

- [x] Authentication and role checks implemented
- [x] Compliance review and outreach gate implemented
- [x] Import and responsive Lead Desk verified
- [x] Sample seeding made explicit
- [x] Backend, frontend and migration checks pass
- [x] Documentation reconciled
- [ ] PR #26 merged to `main`
- [ ] `main` pulled, started and smoke-tested
