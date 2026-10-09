# Epic 1 — where we are

One page: what is finished, what is verified, and what is left before we can demo.

## Done and merged

| Piece | Who | Where |
|---|---|---|
| Product shell — Lead List, Lead Detail with activity, sample-data fallback | Herman | [`frontend/`](../../../frontend/README.md) |
| Lead backend — both tables, the migration, the idempotent seed, the two read endpoints, the tests | Sharon | [`backend/`](../../../backend/README.md) |
| The agreed Lead + Activity shape | Herman + Sharon | [`epic-1-lead-contract.md`](../../delivery/epic-1-lead-contract.md) |
| One defect in the migration test | fixed on `docs/epic-1-standings` | [`backend/tests/test_migration.py`](../../../backend/tests/test_migration.py) |

The contract held. Sharon's API returned exactly the agreed fields, so the frontend needed no
change at all to switch from sample data to real rows.

## What is verified, not just claimed

Against a throwaway PostgreSQL 17 and Python 3.12:

- **34 of 34 tests pass** and `ruff` is clean. The suite builds its schema with
  `alembic upgrade head`, so the migration is under test, and a separate test proves it
  reverses.
- **The seed is idempotent** — 8 leads created, then `0 created, 8 already present`.
- **The API matches the contract** — the list is newest-first and paginated with a
  pre-pagination `total`; the detail returns activity oldest-first and `[]` rather than
  `null`; an unknown *or malformed* id is a `404`, not a `500`.
- **The two halves connect.** With the API running, `GET /api/v1/leads` answers through
  Vite's dev proxy, which is the request that flips the banner from **Sample data** to
  **Live data**.

## Left in Epic 1

Nothing here is a new feature. It is joining the pieces and looking at the result.

- **Mark — one command.** Docker Compose for the database and the API, both databases
  created on first boot, migration and seed run automatically, on a free port. See
  [his card](mark/homework.md).
- **Anne — the seller's eyes.** Nobody who would actually use this has looked at it yet.
  Journey, what each screen must show, 3–5 recommendations, and her example lead in the
  seed. See [her card](anne/homework.md).
- **Everyone — the demo and the retro.** Run it from a clean clone, demo it, then write down
  one thing to keep and one to change before Epic 2.

## One trap to avoid on demo day

`http://localhost:8000` is already taken on Herman's machine by another project's backend,
and that backend answers `/health` with `200 OK` while `GET /api/v1/leads` is a `404`. On a
bad port, the system looks healthy and the UI quietly falls back to sample data. The demo
must name the port it is really using.

## Epic 1 is done when

- Everyone has contributed, and their work is integrated into `main`.
- Someone who wrote none of it can follow one command and see
  Lead List → a lead → its activity, from the database rather than the sample banner.
- Anne has used it as a seller and we have acted on her feedback.
- We know what to change before Epic 2.

The full plan and the checklist live in the
[delivery plan](../../delivery/2026-10-09-delivery-plan.md); how we work is in
[how-we-work.md](../../team/how-we-work.md).
