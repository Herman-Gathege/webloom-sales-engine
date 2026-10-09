# Backend — Webloom Sales Engine

The Epic 1 Lead backend: the Lead and Activity tables, the Alembic migration, a repeatable
synthetic seed, two read endpoints, and their tests. It is the piece that replaces the
frontend's **"Sample data"** banner with real leads.

Deliberately **not** in this block: authentication and roles, sending, campaigns, the CSV
importer, exports, background jobs, and FikaTu delivery. There is no Docker Compose here —
Mark owns the rails and the containers.

## Layout

Requests flow one way: `api` → `schemas` → `services` → `repositories` → `models`.

| Path | Responsibility |
|---|---|
| `app/api/v1/` | Route handlers: parse the request, delegate, shape the response |
| `app/schemas/` | Pydantic request/response models — the JSON the frontend sees |
| `app/services/` | Business rules; where "a malformed id is a 404" lives |
| `app/repositories/` | Data access; the only layer that writes queries |
| `app/models/` | SQLAlchemy ORM models (`leads`, `activities`) |
| `app/database/` | Engine, session factory, declarative base |
| `app/config/` | Settings, read from the environment |
| `app/seed/` | Synthetic sample leads, and the idempotent runner |
| `alembic/` | Migration environment and versions |
| `tests/` | pytest suite, against a real PostgreSQL test database |
| `app/integrations/` | Reserved for the FikaTu seam — not part of Epic 1 |

## Prerequisites

- **Python 3.12** (the version the stack is pinned to).
- **PostgreSQL.** The project targets PostgreSQL 17; any 13+ works locally. Docker Compose
  is Mark's piece and is not defined here, so until it lands you need a database you can
  reach with a connection string — a local Postgres, or
  `docker run --name webloom-pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:17`.

## Setup

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env          # then adjust DATABASE_URL if needed
```

Settings come from the environment, or from `backend/.env` if it exists:

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/webloom_sales_engine` | Where the app and Alembic connect. |
| `TEST_DATABASE_URL` | `...@localhost:5432/webloom_sales_engine_test` | The test suite's database. Its name must end in `_test`. |
| `ENVIRONMENT` | `development` | `production` makes the seed refuse to run. |
| `SQL_ECHO` | `false` | Log every SQL statement. |

## Commands

Run everything from `backend/`.

```bash
.venv/bin/alembic upgrade head      # create or update the schema (leads, activities)
.venv/bin/alembic downgrade base    # reverse the migration — it is not one-way
.venv/bin/alembic check             # fail if the models and the migration have drifted
.venv/bin/python -m app.seed        # load the synthetic sample leads (safe to re-run)
.venv/bin/uvicorn app.main:app --reload --port 8000   # the API the frontend proxies to
.venv/bin/python -m pytest -v       # the test suite (needs TEST_DATABASE_URL)
```

Interactive docs are at <http://localhost:8000/docs> once the server is running.

## The API

### `GET /api/v1/leads?limit=50&offset=0`

One page of leads, newest first (`created_at` descending, with the id as a tie-breaker so a
page boundary can never repeat or skip a lead).

- `limit` defaults to **50** and is capped at **200** — a larger request comes back with
  `limit: 200` and 200 rows, not an error
- `offset` defaults to **0**
- `total` is the count **before** pagination, so the UI can say "8 in the pipeline"
- `limit < 1` or `offset < 0` is a `422`

```json
{
  "items": [
    {
      "id": "00000000-0000-4000-8000-000000000008",
      "business_name": "Nairobi Bee Supplies",
      "sector": null,
      "area": "Kasarani",
      "phone": null,
      "whatsapp_capable": false,
      "website_status": "no phone number on the listing",
      "has_website": false,
      "source": "google_maps",
      "status": "new",
      "created_at": "2026-09-23T09:07:00Z",
      "updated_at": "2026-09-23T09:07:00Z"
    }
  ],
  "total": 8,
  "limit": 50,
  "offset": 0
}
```

### `GET /api/v1/leads/{id}`

Every Lead field, plus the lead's history. `activity` is **oldest first** so the timeline
reads top to bottom, and it is `[]` — never `null` — when nothing has happened yet.

```json
{
  "id": "00000000-0000-4000-8000-000000000006",
  "business_name": "Baraka Chemist",
  "sector": "Pharmacies and chemists",
  "area": "Ngong Road",
  "phone": "+254700000106",
  "whatsapp_capable": false,
  "website_status": "landline only - no website listed",
  "has_website": false,
  "source": "google_maps",
  "status": "new",
  "created_at": "2026-09-23T09:05:00Z",
  "updated_at": "2026-09-23T09:05:00Z",
  "activity": [
    {
      "id": "10000000-0000-4000-8000-000000000011",
      "lead_id": "00000000-0000-4000-8000-000000000006",
      "type": "lead.created",
      "actor": "system",
      "summary": "Imported from the Google Maps list",
      "created_at": "2026-09-23T09:05:00Z"
    },
    {
      "id": "10000000-0000-4000-8000-000000000012",
      "lead_id": "00000000-0000-4000-8000-000000000006",
      "type": "lead.researched",
      "actor": "system",
      "summary": "Website research recorded: landline only - no website listed",
      "created_at": "2026-09-23T09:05:30Z"
    }
  ]
}
```

### `GET /health`

`{"status": "ok"}`. A liveness check for a container or a person; it says nothing about the
database.

### Errors

| Case | Response |
|---|---|
| Unknown lead id | `404` `{"detail": "Lead not found"}` |
| Malformed id (not a uuid) | `404` `{"detail": "Lead not found"}` — a missing lead, not a server error |
| `limit < 1`, `offset < 0` | `422` with FastAPI's validation body |

The field names, nullability, and shapes are frozen in
[`docs/delivery/epic-1-lead-contract.md`](../docs/delivery/epic-1-lead-contract.md). That
document and `frontend/src/api/types.ts` move together; this backend follows them.

## Seed data

`python -m app.seed` inserts eight invented businesses with two activity entries each. It is
safe to run repeatedly:

- every lead has a **fixed id**, and the runner also skips a lead whose **phone** already
  exists — phone is the contract's de-duplication key
- it never updates or deletes a row; a lead that is already there is left alone

```text
Seeded sample leads into localhost:5432/webloom_sales_engine
  8 leads created, 0 already present, 16 activity entries created
# second run
  0 leads created, 8 already present, 0 activity entries created
```

The seed refuses to run when `ENVIRONMENT=production`, and every value in
`app/seed/sample_data.py` is synthetic — invented names, and phone numbers in the reserved
`+2547000...` range. Real lead data lives in the gitignored `data/` directory and never
enters this repository.

## Tests

```bash
TEST_DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/webloom_sales_engine_test" \
  .venv/bin/python -m pytest -v
```

The suite runs against a **real PostgreSQL** database — no SQLite, no mocked session — and
refuses to run unless the database name ends in `_test`. It drops and recreates that schema
and builds it with `alembic upgrade head`, so the migration itself is under test. Each test
then runs inside a transaction that is rolled back, so tests cannot see each other's rows.
One test creates a separate `_migration_test` database to prove `upgrade` → `downgrade`
→ `upgrade` works from empty.

## Frontend integration

Nothing in the frontend needs to change. In development, Vite proxies `/api` to
`http://localhost:8000` (`frontend/vite.config.ts`), and the client's default base URL is
`/api/v1`, so the app calls `GET /api/v1/leads` and `GET /api/v1/leads/{id}` as soon as the
API is running on port 8000 — the banner switches from **"Sample data"** to **"Live data"**
by itself.

- `VITE_API_BASE_URL` overrides the base URL (default `/api/v1`)
- `VITE_USE_MOCK=1` skips the API entirely and always uses the bundled fixtures
- if the API is unreachable, the client waits 4 seconds and falls back to fixtures, saying
  so on screen; a reachable API that answers `404` is a real result and is not hidden

One inconsistency to be aware of, in Herman's files rather than here: `frontend/.env.example`
sets `VITE_API_BASE_URL=http://localhost:8000`, while the client appends `/leads` to that
base — so following that file literally would call `http://localhost:8000/leads` and miss
the `/api/v1` prefix. The default (`/api/v1`, through the proxy) is correct; whether to
change the example belongs to Herman.

## Known limitations

- **Nothing moves a lead off `new`.** Nothing sends yet, so status is always `new` in this
  block; the long-term rule that status is derived from evidence is not implemented.
- **No auth.** Every caller sees contact details. Epic 1 runs locally for the four of us;
  the role-gating rule starts applying in the login block.
- **`activities` is not `activity_events`.** This is the per-lead timeline the detail screen
  shows; the scope spec's `activity_events` is the wider audit feed for a later block.
- **Not the final schema.** The contract is a small subset of the scope spec's data model —
  no campaigns, outreaches, replies, or deals.
- **No Docker Compose.** Mark owns it; this README does not define the containers.
