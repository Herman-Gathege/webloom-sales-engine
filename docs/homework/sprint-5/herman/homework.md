# Herman — Sprint 5 Implementation

## Your mission

Build the complete Sprint 5 campaign and draft slice alone, in small reviewable checkpoints, and
stop before approval or sending.

Read [the Sprint 5 contract](../../../delivery/sprint-5-campaigns-drafts.md) before starting.

## What to build

### Checkpoint 1 — domain, selection and preview

- Add the campaign and campaign-lead data model with a reversible migration.
- Support explicit selection of up to 200 leads.
- Require an active offer, active template and supported channel.
- Preview eligible leads plus one explainable skip reason per excluded lead.
- Keep the seller UI and acceptance path SMS-only. The backend renderer remains
  channel-generic and email is covered by tests.
- Add Campaign List, Campaign Create/Preview and Campaign Detail screens.
- Enforce current approved-policy or current human eligibility during preview.
- Use existing Lead Desk filters and explicit checkboxes. Do not build saved segments.

### Checkpoint 2 — generate historical drafts

- Generate at most one draft per eligible lead.
- Snapshot the rendered body, offer/template content, policy/decision basis and relevant
  versions.
- Skip missing variables, blank price guidance used by the template, suppression, opt-out,
  technical unavailability and stale/review-only eligibility.
- Return the existing drafts on rerun; never duplicate or replace them in Sprint 5.
- Show draft and skip sections in Campaign Detail.
- Store complete catalogue, eligibility, policy and SMS-metric snapshots.
- Keep drafts read-only and visibly labelled **Not sent**.
- Do not add approval, queue, send or FikaTu code.

### Checkpoint 3 — archive, UX and closeout

- Add reversible campaign archive and restore while retaining drafts, skips and events.
- Fix long Activity detail values with a seller allowlist and collapsed technical disclosure.
- Add the compact three-step Wadi Import tutorial and clickable provenance/search fallback.
- Apply the approved “From KES 40,000” catalogue guidance.
- No saved segment or send-path work is part of Sprint 5.

## Done means

- [x] Migration upgrades and downgrades cleanly.
- [x] Admin and Sales can create/use campaigns; catalogue writes remain Admin-only.
- [x] Inactive offers/templates and active templates under inactive offers are rejected.
- [x] Preview is policy-aware and explainable.
- [x] Draft generation is idempotent and snapshots content.
- [x] Campaign archive/restore preserves history.
- [x] Drafts are immutable, read-only and labelled **Not sent**.
- [x] No send or approval path exists in this sprint.
- [x] Backend tests, Ruff, frontend tests, lint, build and Alembic checks pass.
- [x] The app survives desktop and mobile layout checks.
- [ ] Mark, Sharon and Anne have review evidence for their lenses.

## Bring back

- The PR link and checkpoint summary.
- Test evidence and migration result.
- A short demo script.
- Any accepted scope cut or unresolved risk; do not silently absorb it.
