# Herman — Sprint 5 Implementation

## Your mission

Build the complete Sprint 5 campaign and draft slice alone, in small reviewable checkpoints, and
stop before approval or sending.

Read [the Sprint 5 contract](../../../delivery/sprint-5-campaigns-drafts.md) before starting.

## What to build

### Checkpoint 1 — campaign selection and preview

- Add the campaign and campaign-lead data model with a reversible migration.
- Support explicit selection of up to 200 leads.
- Require an active offer, active template and supported channel.
- Preview eligible leads plus one explainable skip reason per excluded lead.
- Include SMS and email in the contract, but keep the live demo SMS-first.
- Add Campaign List, Campaign Create/Preview and Campaign Detail screens.
- Enforce current approved-policy or current human eligibility during preview.

### Checkpoint 2 — generate historical drafts

- Generate at most one draft per eligible lead.
- Snapshot the rendered body, offer/template content, policy/decision basis and relevant
  versions.
- Skip missing variables, blank price guidance used by the template, suppression, opt-out,
  technical unavailability and stale/review-only eligibility.
- Return the existing drafts on rerun; never duplicate or replace them in Sprint 5.
- Show draft and skip sections in Campaign Detail.
- Do not add approval, queue, send or FikaTu code.

### Checkpoint 3 — saved segments

- Save named campaign filters and preview their live count.
- Use a saved segment as campaign selection input.
- Handle deleted or no-longer-matching leads through the same preview/skip rules.

## Done means

- [ ] Migration upgrades and downgrades cleanly.
- [ ] Admin and Sales can create/use campaigns; catalogue writes remain Admin-only.
- [ ] Inactive offers/templates and active templates under inactive offers are rejected.
- [ ] Preview is policy-aware and explainable.
- [ ] Draft generation is idempotent and snapshots content.
- [ ] No send or approval path exists in this sprint.
- [ ] Backend tests, Ruff, frontend tests, lint, build and Alembic checks pass.
- [ ] The app survives desktop and mobile layout checks.
- [ ] Mark, Sharon and Anne have review evidence for their lenses.

## Bring back

- The PR link and checkpoint summary.
- Test evidence and migration result.
- A short demo script.
- Any accepted scope cut or unresolved risk; do not silently absorb it.
