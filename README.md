# Webloom Sales Engine

The sales engine for Webloom + Innovations. It finds and researches businesses, drafts
personalised outreach, gets a human's approval before anything sends, records replies,
qualifies the interested ones, and hands them to a person. Notification delivery runs
through FikaTu, our existing notification platform.

Websites are the offer we start with, not the limit of what this can sell.

## Status

Pre-MVP. **Epic 1 — First Lego Block is closed.** One thin vertical slice runs end to end:
sample leads in PostgreSQL, served by FastAPI, shown in a React Lead List and Lead Detail
with activity history.

- [`frontend/`](frontend/) — Vite + React 19 + TypeScript + Tailwind v4 + shadcn/ui.
- [`backend/`](backend/README.md) — FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL 17, with a
  reversible migration, an idempotent seed, and two read endpoints.
- [`docker-compose.yml`](docker-compose.yml) — one command starts all three.

There is no auth, no sending, and no CSV importer yet. What the block was and how it went is
in the [Epic 1 closure record](docs/homework/epic-1/status.md); what comes next, and who owns
it, is the [epic plan](docs/delivery/epic-plan.md).

## Run it

From a clean clone, one command starts everything:

```bash
docker compose up --build
```

The first run is slow and that is normal: it builds both images and initialises PostgreSQL.
On this machine that took about eight minutes the first time and under a minute after that.
The database is unhealthy for roughly the first minute and a half while `initdb` runs, and
`up` waits for it — so a long silence at the start is not a hang.

On first boot it creates both databases (`webloom_sales_engine` and
`webloom_sales_engine_test`), runs the migration, loads the eight sample leads, and builds the
UI. Then open:

| What | URL |
|---|---|
| The app | <http://localhost:5174> |
| The API directly | <http://localhost:8001> — deliberately not 8000, which is taken on at least one machine |

Click **Leads**, open one, and you should see real rows from PostgreSQL with their activity
history. The **Live data** badge confirms the UI is talking to the API rather than to its
bundled sample leads.

To write UI code with hot reload, run the backend in containers and the dev server by hand
instead — `docker compose up -d db api` then `cd frontend && npm run dev`. Run the backend
tests inside the container with:

```bash
docker compose run --rm api-test
```

The traps we hit, and the decisions to agree before the next block, are in the
[Docker note](docker/README.md).

## If you are one of the four of us

Epic 1 is closed. The next block is **Epic 2 — the Lead Desk is real**, owned by Sharon.
Start with the [epic plan](docs/delivery/epic-plan.md) to see what we are building and who
owns what; the Epic 1 cards live on in
[`docs/homework/epic-1/`](docs/homework/epic-1/README.md) as the record of how the first block
went.

## How we work

We build the product like Lego: one small working piece, everyone's pieces brought together,
tested, demoed, then the next piece. `main` is the latest integrated working state, and a
piece is not done until someone else can pull it and run it.

The rule that governs everything else: **the human team agrees on the contract; AI helps
implement it; a human reviews the result.** The short version is in
[how we work](docs/team/how-we-work.md).

## Team

- Mark Mwenesi — team lead, architecture and backend
- Herman Gathege — product, backlog, frontend
- Anne — sales workflow, copy, pilot campaign
- Sharon Kendi — backend

## Documentation

| Read this | For |
|---|---|
| [Scope spec](docs/superpowers/specs/2026-10-08-webloom-sales-engine-scope.md) | What we are building, what is out of scope, and the design |
| [Epic plan](docs/delivery/epic-plan.md) | What we build next, who owns it, and in what order |
| [Product roadmap](docs/delivery/product-roadmap.md) | The full long-term destination. Not a commitment |
| [Lead API contract](docs/delivery/epic-1-lead-contract.md) | The exact Lead and Activity shapes the API and UI agree on |
| [Epic 1 closure](docs/homework/epic-1/status.md) | What the first block shipped, and what we learned |
| [How we work](docs/team/how-we-work.md) | Branching, PRs, review, what "done" means |
| [FikaTu integration notes](docs/research/2026-10-08-fikatu-integration-notes.md) | Endpoints, events, and the gaps we must work around |
| [Lead list audit](docs/research/2026-10-08-lead-list-audit.md) | What the first lead list contains and what it changes |
| [AGENTS.md](AGENTS.md) | Conventions, guardrails, and the boundary rule |

## Intended stack

FastAPI, PostgreSQL, Redis, Celery, Alembic on the backend; React, Vite, TypeScript,
Tailwind, shadcn/ui on the frontend; Docker Compose and Nginx for infrastructure. This
matches FikaTu so the two systems share one set of conventions.

## Not built yet

Auth, the CSV importer, campaigns, drafts, approval, sending, replies, and reporting —
Epics 2 to 9 in the [epic plan](docs/delivery/epic-plan.md). There is no CI yet either;
Epic 2 adds it, because today a red test is only visible to whoever ran it.
