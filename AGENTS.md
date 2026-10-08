# Webloom Sales Engine — Agent Instructions

## What this is

The sales engine for Webloom + Innovations, a software studio in Nairobi. It turns a
researched market into qualified, human-ready conversations and learns from every one of
them: find businesses, research and segment them, draft personalised outreach, get human
approval, send, record replies, qualify, and hand the interested ones to a person.

Websites are the entry offer, not the ceiling. Automation creates the opportunity; a human
converts it. FikaTu, our existing notification platform, handles delivery underneath.

## Where the truth lives

Read the pointed-to document before acting in that area. Each is the single source of truth
for its subject — edit the document, not a copy of it.

| Subject | Document |
|---|---|
| What we are building, and what is out of scope | `docs/superpowers/specs/2026-10-08-webloom-sales-engine-scope.md` |
| What to build in which order, who owns it | `docs/delivery/2026-10-08-agile-delivery-plan.md` |
| How to talk to FikaTu (endpoints, events, token flow, gaps) | `docs/research/2026-10-08-fikatu-integration-notes.md` |
| What the current lead list actually contains | `docs/research/2026-10-08-lead-list-audit.md` |
| Decisions that are expensive to reverse | `docs/decisions/` (ADRs) |

When a document and the code disagree, the code is the current state and the document is the
intent. Say which you found, then fix the document or fix the code — never leave the two
apart.

## Current state

Pre-MVP and docs-first. The repository contains documentation only; there is no application
scaffold, no schema, no CI, and no deployment yet. The intended layout below is a target,
not a description of what exists.

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
3. **Targeted outreach with a clear opt-out path.** Each channel has a sanctioned,
   templated path; pacing keeps a campaign from bursting.
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
docs/                # specs, delivery plan, research, ADRs
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

- Branches: `feat/<name>`, `fix/<name>`, `chore/<name>`. Nothing is pushed directly to `main`.
- Commits: conventional (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
- Every change lands through a PR with one approval; Mark approves anything touching auth,
  sending, schema, or the FikaTu integration.
- A story is done when its acceptance criteria are demonstrated, its tests pass, it runs in
  Docker locally, migrations are reversible, and docs are updated. The full definition is in
  the delivery plan.
- Decisions that are expensive to reverse get an ADR in `docs/decisions/`.

## Commands

The scaffold does not exist yet, so these are the intended commands. Correct this section
in the same PR that creates the scaffold.

```bash
docker compose up --build              # api, worker, postgres, redis, frontend
docker compose exec api pytest tests/ -v
cd frontend && npm run lint && npm run build
```

## Before you write code

1. Read the scope spec section that covers this work, and the delivery plan story that owns it.
2. Check whether FikaTu already does it — the integration research note says what it offers.
3. Put the rule in a service, the query in a repository, and the wiring in the API layer.
4. Write the test for the failure path as well as the happy path, especially for anything
   that sends, imports, or changes state.
5. Confirm no secret, real contact detail, or export lands in the diff.

## Keep out of this repository

Real lead data, credentials, exports, and generated build output. The state machine carries
the send guardrails; do not add a path around it for convenience. Non-website offers belong
in the offers table, not in a new code path.
