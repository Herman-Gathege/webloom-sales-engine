# Mark — Epic 1

> **Status: ready to pick up, and nothing is blocked on a design decision.** Both halves are
> merged: `frontend/` (Lead List → Lead Detail, sample-data fallback) and `backend/` (the
> Lead and Activity tables, the migration, the seed, `GET /api/v1/leads` and
> `GET /api/v1/leads/{id}`). What does not exist is the thing that starts them together —
> that is this card. Work on branch `chore/epic-1-docker`.

## Your mission

Make the whole Sales Engine start with one command, on a machine that has nothing set up.

## What to do

- Write a `docker-compose.yml` that starts PostgreSQL 17 and the API, and a `Dockerfile` for
  the API. One `docker compose up` should give a working system from a clean clone.
- **Create both databases on first boot:** `webloom_sales_engine` and
  `webloom_sales_engine_test`. A fresh PostgreSQL has neither, the app needs the first, and
  Sharon's suite refuses to run without the second.
- Run `alembic upgrade head` and `python -m app.seed` automatically, so a fresh `up` shows
  leads instead of an empty list.
- **Do not use port 8000.** Herman's machine already has another project's backend on it, and
  that backend answers `/health` with `200 OK` while `GET /api/v1/leads` is a `404` — so a
  bad port looks healthy and silently leaves the UI on sample data. Pick a free port and say
  which one in the README.
- Review the two halves against each other: `frontend/` structure, and whether the layering
  in `backend/app/` is the convention we want to copy. `backend/README.md` explains it.
- Write the short "watch-outs" note, and flag only the decisions that would be painful to
  reverse later.

Do not rewrite what is already there, and do not add abstraction we do not need yet.

You are the safety net, not the whole backend. Keep this to about a day.

## Done means

- [ ] `docker compose up` from a clean clone starts the database and the API together.
- [ ] The API answers on its own port, and `GET /api/v1/leads` returns the seeded leads.
- [ ] Started against that API, the UI shows **Live data**, not the sample banner.
- [ ] The test suite passes inside the container.
- [ ] The architecture is clear enough for the others to follow, and Herman's and Sharon's
      work has been reviewed with it.
- [ ] Obvious future traps are written down — the port above is the first one.
- [ ] No abstraction was added that we do not need yet.

## Bring back

- A small PR on `chore/epic-1-docker`.
- The one command that starts everything, written in the top-level `README.md`.
- A short architecture / watch-outs note.
- 2–3 decisions the team should agree on before we continue.
