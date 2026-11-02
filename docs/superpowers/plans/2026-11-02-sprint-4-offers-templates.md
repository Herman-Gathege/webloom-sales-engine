# Sprint 4 Offers and Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an authenticated, multi-currency offer catalogue and reusable email/SMS template system that Admins manage and Sales can read.

**Architecture:** New catalogue models own offers and Sales Engine message templates. A repository/service/API boundary enforces currency, price, variable and opt-out rules. A separate idempotent catalogue seed installs the four initial offers, with Starter Website priced at KES 40,000. The React Catalog exposes responsive offer and template screens to both roles, with mutations gated to Admins.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 17, Pydantic v2, React 19, TypeScript, Tailwind v4, shadcn/ui, Vitest.

**Spec:** `docs/delivery/sprint-4-offers-templates.md`

## Global Constraints

- Starter Website is `KES 40000.00`; Business Website and Custom Website have blank price guidance until the team supplies it.
- Currency accepts uppercase three-letter codes; the editor offers KES, USD, EUR, GBP, ZAR, UGX and TZS.
- Admins create/edit/deactivate; Sales read active records only.
- Every template is `email` or `sms`, and every active template contains `{{opt_out}}`.
- Template variables are the exact allowlist in the Sprint 4 contract.
- No campaign, draft, sending or FikaTu work is included.
- Lists use cards on mobile and must not overflow horizontally.

---

### Task 1: Catalogue data and migration

**Files:**
- Create: `backend/app/models/catalog.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/alembic/versions/20261102-0005-create-offers-templates.py`
- Modify: `backend/tests/test_migration.py`
- Create: `backend/tests/test_catalog_model.py`

**Interfaces:**
- Produces: `Offer`, `MessageTemplate`, `TemplateChannel`
- `Offer` exposes `id`, `name`, `slug`, `description`, `price_min`, `price_max`, `currency`, `pitch_angle`, `is_active`, timestamps.
- `MessageTemplate` exposes `id`, `offer_id`, `offer`, `channel`, `name`, `variant`, `body`, `variables`, `is_active`, timestamps.

- [ ] Write failing model tests for unique slugs, nonblank names, valid price ranges, uppercase currency, supported channels, unique offer/channel/variant and nonblank template bodies.
- [ ] Run `pytest tests/test_catalog_model.py -q`; confirm failures are missing model imports.
- [ ] Add the SQLAlchemy models and export them.
- [ ] Run the model tests; expect pass.
- [ ] Add reversible migration `0005`; add `offers` and `message_templates` to the migration round-trip expectation.
- [ ] Run migration/model tests and `alembic check`.
- [ ] Commit the task.

### Task 2: Catalogue service, API and seed

**Files:**
- Create: `backend/app/schemas/catalog.py`
- Create: `backend/app/repositories/catalog_repository.py`
- Create: `backend/app/services/catalog_service.py`
- Create: `backend/app/api/v1/catalog.py`
- Modify: `backend/app/schemas/__init__.py`
- Modify: `backend/app/repositories/__init__.py`
- Modify: `backend/app/services/__init__.py`
- Modify: `backend/app/api/v1/router.py`
- Create: `backend/app/catalog_seed/__init__.py`
- Create: `backend/app/catalog_seed/__main__.py`
- Create: `backend/tests/test_catalog_api.py`
- Create: `backend/tests/test_catalog_seed.py`

**Interfaces:**
- Consumes: Task 1 models.
- Produces REST routes: `GET/POST /api/v1/offers`, `PATCH /api/v1/offers/{id}`, `GET/POST /api/v1/templates`, `PATCH /api/v1/templates/{id}`.
- Produces seed command: `python -m app.catalog_seed`.

- [ ] Write failing API tests for Admin writes, Sales read/write rules, active filtering, duplicate conflicts, price validation, currency validation, template channels, variable rejection, required `{{opt_out}}` and no hard delete.
- [ ] Run the focused tests; confirm expected 404/missing-route failures.
- [ ] Implement repository/service/schemas/routes with Admin-only writes and active-only Sales reads.
- [ ] Run focused tests until green.
- [ ] Write failing seed tests for four offers, KES 40000 Starter price, idempotence and preserving edited records.
- [ ] Implement the idempotent catalogue seed.
- [ ] Run focused API/seed tests and commit the task.

### Task 3: Catalog frontend and navigation

**Files:**
- Create: `frontend/src/api/catalog.ts`
- Create: `frontend/src/api/catalog.test.ts`
- Create: `frontend/src/routes/OfferCatalog.tsx`
- Create: `frontend/src/routes/TemplateCatalog.tsx`
- Create: `frontend/src/routes/OfferCatalog.test.tsx`
- Create: `frontend/src/routes/TemplateCatalog.test.tsx`
- Modify: `frontend/src/components/layout/AppLayout.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes Task 2 API routes.
- Produces `/catalog/offers` and `/catalog/templates`.

- [ ] Write failing API client tests for list/create/update payloads.
- [ ] Implement typed catalog API clients.
- [ ] Write failing route tests for Admin controls, Sales read-only state, duplicate/validation errors and responsive card content.
- [ ] Implement Offers and Templates pages using cards on mobile, compact tables on desktop, responsive forms and variable guidance.
- [ ] Add Catalog navigation visible to both roles; hide mutation controls for Sales.
- [ ] Run frontend tests, lint and build; commit the task.

### Task 4: Sprint 4 deliverables and manual test guide

**Files:**
- Create: `docs/homework/sprint-4/README.md`
- Create: `docs/homework/sprint-4/herman/homework.md`
- Create: `docs/homework/sprint-4/mark/homework.md`
- Create: `docs/homework/sprint-4/sharon/homework.md`
- Create: `docs/homework/sprint-4/anne/homework.md`
- Modify: `docs/homework/README.md`
- Modify: `docs/delivery/README.md`
- Modify: `docs/README.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `docs/delivery/sprint-4-offers-templates.md`

**Interfaces:**
- Consumes implemented backend/frontend.
- Produces the manual demo and release checklist requested by the user.

- [ ] Update the spec with resolved currency and Starter pricing decisions.
- [ ] Add one-screen homework cards and a manual acceptance guide covering Admin and Sales.
- [ ] Reconcile current-state docs and test counts.
- [ ] Run backend, frontend, migration, link, responsive and browser checks.
- [ ] Commit the task.

## Verification Commands

```bash
docker compose build api
docker compose run --rm api-test
cd frontend && npm run lint && npm test && npm run build
docker compose exec api alembic check
```

Manual browser acceptance follows `docs/homework/sprint-4/README.md`.
