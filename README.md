# Webloom Sales Engine

The sales engine for Webloom + Innovations. It finds and researches businesses, drafts
personalised outreach, gets a human's approval before anything sends, records replies,
qualifies the interested ones, and hands them to a person. Notification delivery runs
through FikaTu, our existing notification platform.

Websites are the offer we start with, not the limit of what this can sell.

## Status

Pre-MVP. **Epic 1 — First Lego Block is half built.** The frontend shell exists in
[`frontend/`](frontend/): a Lead List, a Lead Detail with activity history, navigation, and
a client that shows bundled sample data until the API answers. It runs from a clean clone
with `npm run dev`.

The Lead backend now exists in [`backend/`](backend/README.md): the Lead and Activity
tables, the Alembic migration, a repeatable synthetic seed, `GET /api/v1/leads` and
`GET /api/v1/leads/{id}`, and a pytest suite. Start it and the frontend's **"Sample data"**
banner becomes **"Live data"** with no frontend change.

Still to come in this block: the backend rails and Docker Compose (Mark), the frontend
and backend demoed together, and the first demo. See the
[delivery plan](docs/delivery/2026-10-09-delivery-plan.md) for the pieces, and the
[lead API contract](docs/delivery/epic-1-lead-contract.md) for the shape they must agree on.

## If you are one of the four of us

Open your homework card and start. It is one screen long and fits in a normal workday:
[Herman](docs/homework/epic-1/herman/homework.md) ·
[Mark](docs/homework/epic-1/mark/homework.md) ·
[Sharon](docs/homework/epic-1/sharon/homework.md) ·
[Anne](docs/homework/epic-1/anne/homework.md)

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
| [Delivery plan](docs/delivery/2026-10-09-delivery-plan.md) | What we are building now, and the next few blocks |
| [Product roadmap](docs/delivery/product-roadmap.md) | The full long-term destination. Not a commitment |
| [Lead API contract](docs/delivery/epic-1-lead-contract.md) | The exact Lead and Activity shapes the API and UI agree on |
| [Homework — Epic 1](docs/homework/epic-1/README.md) | The current block, split into four pieces |
| [How we work](docs/team/how-we-work.md) | Branching, PRs, review, what "done" means |
| [FikaTu integration notes](docs/research/2026-10-08-fikatu-integration-notes.md) | Endpoints, events, and the gaps we must work around |
| [Lead list audit](docs/research/2026-10-08-lead-list-audit.md) | What the first lead list contains and what it changes |
| [AGENTS.md](AGENTS.md) | Conventions, guardrails, and the boundary rule |

## Intended stack

FastAPI, PostgreSQL, Redis, Celery, Alembic on the backend; React, Vite, TypeScript,
Tailwind, shadcn/ui on the frontend; Docker Compose and Nginx for infrastructure. This
matches FikaTu so the two systems share one set of conventions.

## Not built yet

Epic 1 is one thin slice: two screens, backed by leads and their activity. Docker Compose,
the API and worker containers, and Nginx are still to come, so the API is started by hand
for now. CI, deployment, auth, the CSV importer, campaigns, sending, and FikaTu delivery
all come in later blocks.
