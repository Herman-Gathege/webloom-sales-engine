# Sprint 4 — offers and templates

**Testing branch:** `sprint/4-offers-templates`

**Status:** closed with accepted deviations. This page remains as the original manual acceptance
script; the decision, limitation register and evidence are in [status.md](status.md).

Before testing, spend five minutes with the shared orientation:

1. Open the [visual Wadi workflow](../../workflow.html).
2. Read the [stage-by-stage workflow](../../workflow-description.md).
3. Use the [full Wadi guide](../../full-wadi-documentation.md) when you need status,
   architecture, gaps or roadmap context.

The one-sentence orientation: Wadi takes leads from CSV through provenance, approved-policy
evaluation and exception review to an outreach gate, and now has offers/templates; campaigns,
approval and sending are still future work.

Read the [Sprint 4 contract](../../delivery/sprint-4-offers-templates.md), then use this page
as the manual acceptance script. Campaigns and sending are outside this test.

## Start and prepare

From the repository root:

```bash
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python -m app.catalog_seed
```

The application must load at <http://localhost:5174>.

If you need a Sales account for the role test:

```bash
BOOTSTRAP_ADMIN_PASSWORD='choose-a-temporary-password' \
  docker compose run --rm -e BOOTSTRAP_ADMIN_PASSWORD \
  api python -m app.bootstrap --sales reviewer@example.test
```

## Admin acceptance

1. Sign in as an Admin.
2. Open **Offers** from the navigation.
3. Confirm Starter Website, Business Website, Custom Website and FikaTu Notification Platform
   appear.
4. Confirm Starter Website shows **KES 40,000**.
5. Create a temporary offer in USD and confirm it appears.
6. Edit the offer, then deactivate it.
7. Open **Templates**.
8. Filter by offer and channel.
9. Create an SMS template using `{{business_name}}` and `{{opt_out}}`.
10. Confirm variables are detected before save.
11. Confirm an unknown variable is rejected.
12. Confirm removing `{{opt_out}}` from an active template is rejected.
13. Edit and deactivate the template.

## Sales acceptance

1. Sign in with a Sales account.
2. Open **Offers** and **Templates**.
3. Confirm active records are visible and write controls are absent.
4. Confirm inactive records are not listed.

## Checks

```bash
docker compose build api
docker compose run --rm api-test

cd frontend
npm run lint
npm test
npm run build

cd ..
docker compose exec api alembic check
```

## Done means

- [ ] Catalogue seed is idempotent.
- [ ] Multi-currency offer values can be saved.
- [ ] Starter Website remains KES 40,000.
- [ ] Admin can create, edit and deactivate offers/templates.
- [ ] Sales can read active records but cannot mutate them.
- [ ] Unknown variables and missing opt-out text are rejected.
- [ ] Mobile cards show without horizontal page scrolling.
- [ ] Existing leads, imports, compliance and authentication still work.

Report issues with the screen, exact steps, expected result and actual result.
