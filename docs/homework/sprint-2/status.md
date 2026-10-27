# Sprint 2 — exit review

**Decision: closed with accepted deviations.** Reviewed 2026-10-27 against `main` at
`53c77ad` (PR #24). `sprint/2-lead-desk` is identical to `main` at that commit.

This is the evidence behind the decision, not a summary written from memory. Where the
implementation differs from the written criteria, it says so below.

## What shipped

| Piece | State |
|---|---|
| CSV importer with per-row refusal reasons | Shipped. Refusals name the physical line and keep good rows. |
| Provenance, import batches, independent channel review, terminal suppression | Shipped in the Sprint 2 compliance foundation (`0002` migration). |
| Compliance audit entries | Shipped. Actor, state, channel, scope and reason; no raw contacts. |
| Lead list filters and search | Shipped in the browser. |
| Pagination | Shipped: 25 per page, page in the URL. |
| Import screen | Shipped: upload, progress, refused-rows table and download. |
| CI workflow | Shipped: backend lint/tests/migration check, frontend lint/build/tests. |
| Wadi identity | Shipped: palette, scout, crew, responsive navigation. |

## Evidence

- **Backend:** `136 passed` at the Sprint 2 exit commit; `ruff` clean. (150 after the
  Sprint 3 auth tests were added.)
- **Frontend:** `28 passed` at exit; lint clean; production build succeeds. (34 after
  Sprint 3.)
- **Migrations:** `0001 → 0002 → 0003` apply cleanly; `alembic check` reports no drift.
- **Live database after the exit review:** 62 leads, 186 channel-review rows (62 × 3),
  **all `needs_review`**, 0 eligible, 0 suppressions.
- **CI workflow:** `.github/workflows/ci.yml` exists and runs both applications.

## Acceptance against the written criteria

| Criterion | Result |
|---|---|
| Lead desk works | Met — list, detail, timeline and compliance panel served from PostgreSQL |
| Import works, rejects explained | Met — covered by importer tests and the live import review |
| Tests and frontend checks pass | Met |
| CI runs on every PR | Met (workflow). Requiring the checks in branch protection is an admin action and is **not** done. |
| Filters, search and pagination | Partly met — filters/search are client-side over up to 200 leads; the API paginates but does not filter. |
| Contact details hidden by role | Deferred by decision to Sprint 3 — **implemented there** (see the Sprint 3 record). |
| 13-screen inventory signed off | Not done; still an open question in the sprint detail. |
| Compliance decisions preserved | Met, with the provenance gap below. |

## Known limitations and deviations

1. **The 62 existing leads have no provenance or import-batch rows.** They were imported
   before the compliance migration. The backfill created three `needs_review` channel rows
   for each lead, so none is eligible for contact, but their `source_url`, collection date
   and contact type are genuinely unknown. Nothing was invented to fill the gap. Leads
   imported from now on do record provenance and a batch — that path is covered by tests.
2. **Filtering is client-side.** The list fetches up to 200 leads and filters in the
   browser. Correct for the current 62, and a scaling limit rather than a bug.
3. **Role-gated contact visibility was deferred to Sprint 3**, which now implements
   `admin`/`sales` and backend enforcement.
4. **No branch protection.** The CI workflow is not yet a required check in GitHub.
5. **No screen inventory sign-off.** The 13-surface list remains an open team question.

## Why this is safe to close

Every lead is `needs_review` on every channel, and suppression is terminal. Nothing in this
sprint can send, and nothing was sent. The importer refuses suppressed contacts and never
marks a channel eligible. FikaTu remains the delivery layer and is untouched.

## Where to go next

Sprint 3 — authentication and roles. See
[the Sprint 3 scope](../../delivery/sprint-3-auth.md) and
[the review homework](../sprint-3/README.md).
