# Sharon — Epic 1

> **Status: done and merged** (PR #7). The API is in
> [`backend/`](../../../../backend/README.md): the two tables, the migration, an idempotent
> seed, the two read endpoints, and a suite that runs against a real PostgreSQL. Two gaps
> she deliberately left are now Mark's and Anne's — see the note at the bottom.

## Your mission

Make a real Lead travel from the database to the API.

## What to do

- Create the smallest Lead model that fits the fields we agreed.
- Write the migration and make sure it runs on a clean database, and can be reversed.
- Build the basic Lead API: list leads, and get one lead by id.
- Add a small amount of seed data — a handful of realistic sample leads, no real contacts.
- Add a tiny activity/history per lead — a couple of entries the UI renders on the detail screen.
- Add focused tests for the endpoints.
- Keep the response simple and frontend-friendly.

The exact field names and shapes are already agreed — build against
`docs/delivery/epic-1-lead-contract.md`, don't invent a different shape.

Do not build campaigns, messaging, qualification, or the whole data model. Just the Lead.

## Done means

- [x] The migration runs — and reverses, tested from empty.
- [x] Lead exists, with `activities` behind it.
- [x] The API returns leads, and one lead by id, in exactly the agreed shape.
- [x] Each lead has its activity behind it, oldest first.
- [x] Tests pass — `ruff` clean, and 34 of 34 green once the one real defect was fixed. The
      red test was in her own test file, not in the migration: it built the throwaway
      database URL with `str(url)`, and SQLAlchemy's `URL.__str__` masks the password as
      `***`, so it could only pass where PostgreSQL does not ask for one. Fixed on
      `docs/epic-1-standings` with `render_as_string(hide_password=False)`; the migration
      itself was never wrong.
- [x] Herman has an example response to connect to — and the contract held, so he needed no
      frontend change at all.

Verified independently against a throwaway PostgreSQL 17 and Python 3.12: 34/34 tests pass
and the migration reverses; the seed is idempotent (8 leads, then `0 created, 8 already
present`); the pagination respects `limit`/`offset` and caps `limit` at 200; the detail
endpoint returns activity oldest-first and `[]` rather than `null`; an unknown or malformed
id is a 404 rather than a 500. Started through Vite, `GET /api/v1/leads` comes back through
the dev proxy, so the screen switches to **Live data** with no frontend change.

## Bring back

- Her pull request.
- The API endpoints.
- An example response.
- Anything Herman needs — the answer was "nothing".

Two things she left behind on purpose, and they now belong to other people:

- **Nothing creates the databases.** A fresh PostgreSQL has neither
  `webloom_sales_engine` nor `webloom_sales_engine_test`, so the suite cannot run until
  someone makes them. **Mark**, with the containers.
- **The seller's view is still untested.** The screens have never been looked at by the
  person who would use them. **Anne.**
