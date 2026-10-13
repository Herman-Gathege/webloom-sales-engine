# Sprint 1 — the first working slice: done

**Closed:** 2026-10-13 · **Result:** shipped · **Scope:** one thin vertical slice, no auth,
no sending.

```text
seed data → Lead → PostgreSQL → FastAPI → React → Lead List → Lead Detail → activity/history
```

## What shipped

| Piece | Who | Where |
|---|---|---|
| Product shell — Lead List, Lead Detail with activity, sample-data fallback | Herman | [`frontend/`](../../../frontend/README.md) |
| Lead backend — both tables, the migration, the idempotent seed, the two read endpoints, the tests | Sharon | [`backend/`](../../../backend/README.md) |
| The agreed Lead + Activity shape | Herman + Sharon | [`sprint-1-lead-contract.md`](../../delivery/sprint-1-lead-contract.md) |
| One command — PostgreSQL, the API **and the UI** in Compose | Mark | [`docker/README.md`](../../../docker/README.md) |
| The seller's walkthrough | Anne | verbal sign-off, see below |

## What is verified, not just claimed

- **34 of 34 backend tests pass** and `ruff` is clean, against PostgreSQL 17 and Python 3.12.
  The suite builds its schema with `alembic upgrade head`, so the migration is under test, and
  a separate test proves it reverses.
- **The seed is idempotent** — 8 leads created, then `0 created, 8 already present`.
- **The API matches the contract** — the list is newest-first with a pre-pagination `total`;
  the detail returns activity oldest-first and `[]` rather than `null`; an unknown *or
  malformed* id is a `404`, not a `500`.
- **The frontend builds, lints, and passes its tests** on Node 22.
- **One command starts the whole slice from a clean clone**, verified from a deleted volume:
  `docker compose up --build` → database healthy → migration applied → 8 leads → UI on
  <http://localhost:5174>, API on 8001.
- **The contract held.** Sharon's API returned exactly the agreed fields, so the frontend
  needed no change at all to switch from sample data to real rows.

## What we learned — keep one, change one

**Keep: the contract-first split.** Agreeing the Lead shape before either side wrote code is
why the frontend needed zero changes to go live. Do that again for every seam.

**Change: the setup tax.** Sprint 1 cost more in environment friction than in product — a
Node 21/22 trap, a port another project already owned, and PostgreSQL needing both databases
created before anything would run. The containers fixed it, but it took three attempts. **From
Sprint 2, the first task of every sprint is "a new person can run it," not the last.**

## Traps worth remembering

- `http://localhost:8000` is already taken on at least one team machine by another project's
  backend, which answers `/health` with `200 OK` while `GET /api/v1/leads` is a `404`. On a bad
  port the system looks healthy and the UI quietly falls back to sample data.
- Vite 8 will not run on Node 21; it fails with a missing `rolldown` binding that reads like a
  broken install. Node 22 is pinned in `.nvmrc` and `engines`.

## Carried into Sprint 2, on purpose

Anne walked both screens as a seller and gave **verbal sign-off: the direction is right.** Her
written notes, her 3–5 recommendations, and her example "good lead" in the seed were not
delivered inside the sprint. Rather than retro-fit a closed sprint, they are the **first story of
Sprint 2** — they change the Lead Desk, which is what Sprint 2 is for.

That is the one honest gap in this closure: the seller's feedback exists, the artifact does
not yet.

## Sprint 1 is done when

- [x] Everyone contributed to the same working slice.
- [x] Everyone's work is integrated — Herman PR #5, Sharon PR #7, Mark PR #10.
- [x] Someone who wrote none of it can clone, run one command, and see Lead List → a lead →
      its activity, from the database rather than the sample banner.
- [x] Everyone understands how we want to work, and the keep/change note above is written
      down before Sprint 2.

The plan we act on now is the **[sprint plan](../../delivery/sprint-plan.md)**; how we work is in
[how-we-work.md](../../team/how-we-work.md).
