# Webloom Sales Engine

The sales engine for Webloom + Innovations. It finds and researches businesses, drafts
personalised outreach, gets a human's approval before anything sends, records replies,
qualifies the interested ones, and hands them to a person. Notification delivery runs
through FikaTu, our existing notification platform.

Websites are the offer we start with, not the limit of what this can sell.

## Status

Pre-MVP. **Sprints 1–4 are closed; Sprint 5 is active with Herman as the sole implementation
owner.**
Start with the [visual workflow](docs/workflow.html) and
[full Wadi guide](docs/full-wadi-documentation.md) for the current system, boundaries and
roadmap.

- [`frontend/`](frontend/) — Vite + React 19 + TypeScript + Tailwind v4 + shadcn/ui.
- [`backend/`](backend/README.md) — FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL 17, with
  reversible migrations, an idempotent seed, lead review endpoints, the CSV importer, and
  JWT authentication with `admin`/`sales` roles. A versioned central policy can approve
  channel eligibility automatically when documented conditions match. The approved
  `2026-11-09.1` policy currently enables SMS for generic business contacts from the
  Yellow Pages Kenya research source.
- [`docker-compose.yml`](docker-compose.yml) — one command starts all three.

There is no sending yet. Sprint 5 now owns campaigns and draft generation.

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
`webloom_sales_engine_test`), runs the migration, and builds the UI. The database starts empty
so the first import is the source of truth. For a disposable demo, add the synthetic leads
explicitly:

```bash
SEED_SAMPLE_DATA=true docker compose up --build
```

Then open:

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

The traps we hit, and the decisions to agree before the next sprint, are in the
[Docker note](docker/README.md).

## If you are one of the four of us

Read the [Sprint 5 contract](docs/delivery/sprint-5-campaigns-drafts.md) and the
[Sprint 5 homework](docs/homework/sprint-5/README.md). The whole plan remains the
[sprint plan](docs/delivery/sprint-plan.md).

There are four administrator accounts and no public sign-up. Create them locally once:

```bash
BOOTSTRAP_ADMIN_PASSWORD='choose-a-temporary-password' \
  docker compose run --rm -e BOOTSTRAP_ADMIN_PASSWORD api python -m app.bootstrap
```

Each account must set its own password at first login.

To try the sales role, add a sales account the same way:

```bash
BOOTSTRAP_ADMIN_PASSWORD='choose-a-temporary-password' \
  docker compose run --rm -e BOOTSTRAP_ADMIN_PASSWORD api python -m app.bootstrap --sales you@example.test
```

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
| [Workflow](docs/workflow.html) | A fast visual explanation of how Wadi works |
| [Workflow description](docs/workflow-description.md) | Exact stage rules, human decisions and stop conditions |
| [Full Wadi guide](docs/full-wadi-documentation.md) | Current state, architecture, gaps and roadmap |
| [Scope spec](docs/superpowers/specs/2026-10-08-webloom-sales-engine-scope.md) | What we are building, what is out of scope, and the design |
| [Sprint plan](docs/delivery/sprint-plan.md) | The nine sprints, what each delivers, and who leads it. Read this one |
| [Sprint 3 scope](docs/delivery/sprint-3-auth.md) | Login, roles, bootstrap, and what this sprint does not do |
| [Sprint 3 solidification](docs/delivery/sprint-3-solidification.md) | CSV import outcomes, automatic eligibility, Lead Desk filters, and the current outreach boundary |
| [Sprint 4 exit review](docs/homework/sprint-4/status.md) | Catalogue evidence, fixed closeout gaps and accepted carry-forward limitations |
| [Sprint 5 contract](docs/delivery/sprint-5-campaigns-drafts.md) | Active campaign/draft slice, locked decisions and ownership |
| [Sprint 5 homework](docs/homework/sprint-5/README.md) | Herman implementation card plus review-only cards for Mark, Sharon and Anne |
| [Sprint 3 exit review](docs/homework/sprint-3/status.md) | Tests, accepted deviations and the closeout decision |
| [Sprint 2 exit](docs/homework/sprint-2/status.md) · [Sprint 1 record](docs/homework/sprint-1/status.md) | How the first two sprints closed, with evidence |
| [Lead API contract](docs/delivery/sprint-1-lead-contract.md) | The exact Lead and Activity shapes the API and UI agree on |
| [Sprint detail](docs/delivery/sprint-detail.md) | Deep detail on every piece of work, sprint by sprint. Reference only |
| [How we work](docs/team/how-we-work.md) | Branching, PRs, review, what "done" means |
| [FikaTu integration notes](docs/research/2026-10-08-fikatu-integration-notes.md) | Endpoints, events, and the gaps we must work around |
| [Lead list audit](docs/research/2026-10-08-lead-list-audit.md) | What the first lead list contains and what it changes |
| [Compliance foundation](docs/compliance/README.md) | Legal boundaries, responsibilities, and the practical outreach safeguards |
| [AGENTS.md](AGENTS.md) | Conventions, guardrails, and the boundary rule |

## Intended stack

FastAPI, PostgreSQL, Redis, Celery, Alembic on the backend; React, Vite, TypeScript,
Tailwind, shadcn/ui on the frontend; Docker Compose and Nginx for infrastructure. This
matches FikaTu so the two systems share one set of conventions.

## Not built yet

Campaigns, drafts, approval, sending, replies, and reporting — Sprints 5 to 9 in the
[sprint plan](docs/delivery/sprint-plan.md). The CI workflow is present, and `main` requires
its Backend/Frontend checks.
