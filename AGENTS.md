# Webloom Sales Engine — Agent Instructions

## What this is

The sales engine for Webloom + Innovations, a software studio in Nairobi. It turns a
researched market into qualified, human-ready conversations and learns from every one of
them: find businesses, research and segment them, draft personalised outreach, get human
approval, send, record replies, qualify, and hand the interested ones to a person.

Websites are the entry offer, not the ceiling. Automation creates the opportunity; a human
converts it. FikaTu, our existing notification platform, handles delivery underneath.

## How we work — read this first

We build the product like Lego: build one small working piece, bring everyone's pieces
together, test it, learn how we worked, then build the next piece. The full working
agreement is [`docs/team/how-we-work.md`](docs/team/how-we-work.md). The short version:

- **Small vertical slices, not silos.** Nobody disappears for a week to reappear with a layer.
- **Short-lived branches, small PRs, frequent integration.** `main` is the latest integrated
  working state.
- **The first version of everything is small.** Extra abstraction is a cost we pay now for a
  guess about later; we do not pay it.
- **Human team agrees on the contract/decision. AI helps implement it. Human reviews the
  result.** That order is not optional.

## Use subagents on every prompt

This project is built by four people and their AI assistants in parallel. **Use subagents on
every prompt** — split the work so no single agent (or person) carries the whole load, and so
the four of us move as one. Skip delegation only when a prompt genuinely has nothing to
split: a single file, or a single decision on its own.

Rules for doing it safely:

- **One writer per file.** Before delegating, name the files each agent owns. Two agents
  never edit the same file at the same time.
- **Give every subagent the shared contract:** the slice it is building, the exact paths it
  owns, the conventions in `docs/team/how-we-work.md`, and the instruction *do not commit —
  leave the working tree for the coordinator*.
- **The coordinator integrates.** Review each subagent's output, reconcile cross-references,
  run the checks, and make the commit.
- **Verify, do not trust.** A subagent that reports success has not proven it. The
  coordinator runs the link check, the tests, or the demo before calling anything done.
- **Flag ambiguity, do not invent it.** If a subagent would have to guess a requirement, it
  stops and reports the question instead of filling the gap.

## Where the truth lives

Read the pointed-to document before acting in that area. Each is the single source of truth
for its subject — edit the document, not a copy of it.

| Subject | Document |
|---|---|
| What we are building, and what is out of scope | `docs/superpowers/specs/2026-10-08-webloom-sales-engine-scope.md` |
| What we build now, and the next few Lego blocks | `docs/delivery/2026-10-09-delivery-plan.md` |
| The exact Lead and Activity shapes the frontend and backend agree on | `docs/delivery/epic-1-lead-contract.md` |
| The full long-term product roadmap (roadmap areas R1–R13) | `docs/delivery/product-roadmap.md` |
| The current block, split into four homework cards | `docs/homework/epic-1/` |
| Branching, PRs, review, definition of done, disagreements | `docs/team/how-we-work.md` |
| How to talk to FikaTu (endpoints, events, token flow, gaps) | `docs/research/2026-10-08-fikatu-integration-notes.md` |
| What the current lead list actually contains | `docs/research/2026-10-08-lead-list-audit.md` |
| Decisions that are expensive to reverse | `docs/decisions/` (ADRs) |
| Everything above, indexed | `docs/README.md` |

When a document and the code disagree, the code is the current state and the document is the
intent. Say which you found, then fix the document or fix the code — never leave the two
apart.

## Current state

Epic 1 — the first Lego block, half built.

- **Built:** `frontend/` — Vite + React 19 + TypeScript + Tailwind v4 + shadcn/ui, routed
  Lead List → Lead Detail with activity history, and a client that falls back to bundled
  sample data until the API answers. It runs from a clean clone; see `frontend/README.md`.
- **Built:** `backend/` — the Lead and Activity model, the Alembic migration, an idempotent
  synthetic seed, `GET /api/v1/leads` and `GET /api/v1/leads/{id}`, and a pytest suite.
  Commands are in `backend/README.md`.
- **Not built:** the rails around it — Docker Compose, the API and worker containers, and
  Nginx. That is Mark's piece.
- The shapes the two halves must agree on are frozen in
  `docs/delivery/epic-1-lead-contract.md`. Change that document and
  `frontend/src/api/types.ts` in the same PR, or neither.
- FikaTu integration is **not** in Epic 1 — the seam is a small fake adapter. There is no
  auth, no sending, and none of the other eleven screens yet. The intended layout below is
  the target; the backend half does not exist.

## The boundary rule

The Sales Engine owns leads, campaigns, replies, tasks, deals, and everything a seller sees.
FikaTu owns events, templates, channels, providers, retries, and delivery. All FikaTu
communication lives in `backend/app/integrations/fikatu/`; call it through a narrow internal
interface so the seam can be faked in tests. The Sales Engine never implements a provider
integration, and FikaTu never learns anything about sales.

## Non-negotiables

These protect the company's reputation and other people's data. Break one and the work is
wrong regardless of how well it is written.

1. **A human approves every send.** Enforced in the outreach state machine, not only in the
   UI: the send path is reachable only from `approved`.
2. **Opt-out is terminal.** An opted-out lead is excluded from every future send, checked at
   send time.
3. **Targeted outreach with a clear opt-out path.** Each channel has a sanctioned, templated
   path; pacing keeps a campaign from bursting.
4. **Real lead data stays out of git.** Contact details live in the gitignored `data/`
   directory. Committed fixtures and examples use synthetic values only.
5. **Every lead records its source and the basis on which we hold it.** Provenance is a
   field, not an assumption.
6. **Contact details are role-gated.** Only `owner` and `sales` see them; exports are logged.
7. **Research respects terms of service.** Data comes from sources we are permitted to use.

## Team and decision rights

| Person | Ask them about | Reviews |
|---|---|---|
| Mark Mwenesi (team lead) | Architecture, backend, infrastructure, anything hard | Auth, the send path, database schema, the FikaTu integration |
| Herman Gathege (product) | Scope, backlog, acceptance criteria, priorities | Frontend, product decisions |
| Anne (sales) | The sales workflow, message copy, qualification criteria, pilot campaign | Copy, templates, funnel definitions |
| Sharon Kendi (backend) | Backend features, migrations, tests | Backend features she did not write |

The backlog is the delivery plan. If a request is not in it, raise it with Herman before
building.

## Intended layout

```
backend/app/
├── api/v1/          # route handlers: parse, authorise, delegate
├── schemas/         # Pydantic request/response models
├── services/        # business logic — where the rules live
├── repositories/    # data access; the only layer that writes SQL
├── models/          # SQLAlchemy ORM models
├── workers/         # Celery tasks: cadence scheduling, sending, status sync
├── middleware/      # auth, request id, logging
├── config/          # settings
├── database/        # session, base
└── integrations/    # fikatu/ — the only code that knows FikaTu's API exists
frontend/            # React SPA
docs/                # scope, delivery plan, roadmap, homework, research, ADRs
docker/              # nginx, postgres, redis, worker configuration
```

Follow the FikaTu repository (`Herman-Gathege/notifications_pipeline_system`) for layering
and conventions; both systems share a stack and a reviewer.

## Stack

Backend: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, Celery 5.5.
Data: PostgreSQL 17, Redis 7. Frontend: React 19, Vite, TypeScript, Tailwind CSS v4,
shadcn/ui, React Router v7, TanStack Table, Axios. Infrastructure: Docker, Docker Compose,
Nginx. Observability: structlog, prometheus-client.

Auth is JWT (python-jose) with bcrypt password hashing and four roles: `owner`, `sales`,
`engineer`, `viewer`.

## Working agreements

Branching, PRs, review, the definition of done, and how we handle disagreements all live in
`docs/team/how-we-work.md` — that file is the source of truth, so do not restate it here.
Two extras that belong to this repo specifically: commits are conventional (`feat:`, `fix:`,
`docs:`, `refactor:`, `test:`, `chore:`), and decisions that are expensive to reverse get an
ADR in `docs/decisions/`.

## Commands

The frontend exists; the backend does not. Keep this section honest — correct it in the same
PR that changes a command.

```bash
cd frontend && npm install && npm run dev      # the SPA on sample data, http://localhost:5173
cd frontend && npm run lint && npm run build && npm test

cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
cd backend && .venv/bin/alembic upgrade head   # create the leads and activities tables
cd backend && .venv/bin/python -m app.seed     # load the synthetic sample leads (repeatable)
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000   # the API the SPA proxies to
cd backend && .venv/bin/python -m pytest -v    # needs TEST_DATABASE_URL; see backend/README.md

docker compose up --build                      # api, worker, postgres, redis, frontend — not built yet
docker compose exec api pytest tests/ -v       # not built yet
```

**Node 22.12 or newer is required**, pinned in `.nvmrc`. Vite 8 will not run on Node 21: it
fails to load its rolldown native binding (`Cannot find module
'../rolldown-binding.linux-x64-gnu.node'`), which reads like a broken install but is only an
unsupported version. `frontend/package.json` declares the same range in `engines`.

## Before you write code

1. Read the scope spec section that covers this work, and the delivery plan block that owns it.
2. Check whether FikaTu already does it — the integration research note says what it offers.
3. Put the rule in a service, the query in a repository, and the wiring in the API layer.
4. Write the test for the failure path as well as the happy path, especially for anything
   that sends, imports, or changes state.
5. Confirm no secret, real contact detail, or export lands in the diff.

## Keep out of this repository

Real lead data, credentials, exports, and generated build output. The state machine carries
the send guardrails; do not add a path around it for convenience. Non-website offers belong
in the offers table, not in a new code path.
