# Webloom Sales Engine

The sales engine for Webloom + Innovations. It finds and researches businesses, drafts
personalised outreach, gets a human's approval before anything sends, records replies,
qualifies the interested ones, and hands them to a person. Notification delivery runs
through FikaTu, our existing notification platform.

Websites are the offer we start with, not the limit of what this can sell.

## Status

Pre-MVP, docs-first. No application code yet. The first code arrives in **Epic 1 — First
Lego Block**: an app shell, a Lead model, a Lead API, a Lead List, a Lead Detail screen, and
basic activity/history. Deliberately small. See the [delivery plan](docs/delivery/2026-10-09-delivery-plan.md).

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

Everything below `docs/` is documentation. Epic 1 creates the first working slice — seed
fixture → Lead → PostgreSQL → FastAPI → React → Lead List → Lead Detail → activity/history.
CI, deployment, auth, the CSV importer, and FikaTu delivery come in later blocks.
