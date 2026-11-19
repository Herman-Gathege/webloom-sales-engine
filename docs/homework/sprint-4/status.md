# Sprint 4 Exit Review

**Decision:** closed with accepted deviations.

**Reviewed:** 2026-11-09

**Evidence:** [PR #29](https://github.com/Herman-Gathege/webloom-sales-engine/pull/29)
merged the catalogue in `68141f5`; [PR #30](https://github.com/Herman-Gathege/webloom-sales-engine/pull/30)
merged the completed sprint branch in `604be37`; closeout and approved-policy work merged in
[PR #31](https://github.com/Herman-Gathege/webloom-sales-engine/pull/31) as `32bc30c`.
Backend and Frontend checks passed for all release commits.

This review separates what shipped from what remains. It does not treat later campaign, draft,
approval, delivery or analytics work as Sprint 4 debt.

## What shipped

| Piece | State |
|---|---|
| Multi-currency offer model and reversible `0005` migration | Shipped |
| Admin offer create, edit and deactivate APIs | Shipped |
| Admin email/SMS template create, edit and deactivate APIs | Shipped |
| Sales read-only catalogue access with API-enforced write denial | Shipped |
| Variable allowlist and exact declared/detected variable matching | Shipped |
| Mandatory `{{opt_out}}` on active templates | Shipped |
| Raw phone/email rejection in template bodies | Fixed during closeout |
| Inactive offers excluded from Sales template results | Fixed during closeout |
| Responsive offer/template catalogue screens | Shipped |
| Idempotent catalogue seed | Shipped with four offers and two starter templates |
| Browser workflow tests for Admin create/deactivate and Sales controls | Expanded during closeout |
| Existing lead, import, compliance and authentication regression suites | Passing |

## Evidence

- **Backend:** 228/228 tests pass against PostgreSQL 17 and Python 3.12; Ruff is clean.
- **Frontend:** 50/50 tests pass; lint and production build pass.
- **Migrations:** the full `upgrade -> downgrade -> upgrade` test passes; model and migration
  constraints agree.
- **Seed:** the live catalogue contains four offers and two active starter templates. Rerunning
  the seed preserves edits and creates no duplicates.
- **Catalogue UI:** the running app successfully loads the Admin catalogue and its active
  templates. Component tests exercise Admin create/deactivate and Sales read-only controls.
- **Remote release:** PR #29 and PR #30 are merged; no Sprint 4 pull request remains open.

## Fixed during this closeout

1. Template bodies now reject raw phone numbers and email addresses on both the API and the
   editor.
2. Sales users no longer receive active templates whose parent offer is inactive.
3. Tests now cover template update/deactivation, Sales write denial on `PATCH`, inactive-parent
   filtering, raw-contact rejection and the main catalogue UI workflows.
4. The Sprint 4 API contract now names the implemented `include_inactive` query parameter.
5. The desktop-table expectation is marked as superseded by the accepted responsive card grid.

## Accepted deviations

1. **Copy pack is partial.** The seed contains one SMS variant and one email variant for Starter
   Website. A/B coverage, the social-only variant, approved price phrasing, final opt-out copy
   and channel-length rules still require Anne and the team. These must be resolved before a
   real Sprint 5 campaign is approved.
2. **Desktop uses cards, not tables.** The original contract proposed a desktop table, but the
   implemented responsive card grid avoids horizontal scrolling and is the accepted design.
3. **Price guidance is incomplete.** Business Website, Custom Website and FikaTu prices remain
   open. Templates must omit price claims when guidance is absent.
4. **Catalogue scale is small.** There is no catalogue search or pagination. This is acceptable
   for the current handful of offers and templates and becomes relevant only as the catalogue
   grows.
5. **No template history.** Editing a template leaves no version history. Sprint 5 must snapshot
   the rendered draft so later edits cannot alter historical outreach.
6. **No catalogue audit feed.** CUD actions are authorised and tested but do not create a
   cross-product audit event. This is not required for the Sprint 4 catalogue and should be
   revisited before broader administration.

## Carried into Sprint 5

- render drafts from the current approved policy **or** a complete current human eligibility
  decision; policy-approved SMS must not be forced back into manual review;
- accept only active offers and active templates whose parent offer is active;
- define and enforce channel body limits and final opt-out wording before campaign approval;
- complete missing copy variants and price guidance before a real campaign;
- handle blank prices and optional lead variables through visible skip reasons;
- snapshot template/offer content, eligibility basis and policy version on every generated
  draft;
- finish the 13-screen product inventory before campaign UI implementation is declared ready;
- preserve idempotent draft generation and one draft per eligible lead.

## Deferred beyond Sprint 5

- template version history and multi-step approval;
- catalogue audit/version comparison;
- offer/variant analytics;
- sending, FikaTu delivery, retries and inbound replies;
- WhatsApp delivery while FikaTu has no provider;
- billing, quotations, public catalogue pages and e-commerce.

## One keep, one change

- **Keep:** commercial offer and copy data are editable without changing code.
- **Change:** Sprint 5 starts from an explicit, small campaign/draft contract and snapshots
  content immediately; it does not treat mutable catalogue rows as historical truth.

## Repository state at review

Sprint 4 catalogue, closeout fixes and the approved compliance-policy follow-up are merged into
`main` at `32bc30c`. Sprint 5 now branches from that merged state.

## Closure checklist

- [x] Offers and templates implemented with reversible migration
- [x] Admin and Sales permissions enforced
- [x] Variable and opt-out validation implemented
- [x] Raw contact values rejected
- [x] Inactive offers excluded from Sales template results
- [x] Seed idempotence verified
- [x] Backend, frontend, lint, build and migration drift checks pass
- [x] Limitation register and carry-forward decisions documented
- [x] Sprint 5 reviewed separately
