# Sprint 5 — implementation status

**Updated:** 2026-11-19  
**Status:** implementation complete; awaiting Mark, Sharon and Anne review

## Delivered

- Reversible migration `0006` with normalized website state, campaigns, stored selection
  context, selected campaign leads, immutable outreach drafts and campaign events.
- Explicit SMS campaign selection using Lead Desk filters and a 200-lead cap.
- Eligibility/skip preview through the existing `OutreachGateService`.
- Catalogue drift detection and snapshot preservation.
- One-shot, atomic draft generation with canonical opt-out text and SMS segment accounting.
- Read-only **Not sent** drafts, persisted skip reasons, archive/restore and campaign history.
- Responsive Campaign List, Create/Edit and Detail screens.
- Activity technical-detail disclosure, clickable provenance/search fallback, and the Wadi CSV
  guide.
- Starter Website public guidance now reads “From KES 40,000.”

## Verified

- Backend suite: 263/263 tests pass against PostgreSQL 17.
- Frontend suite: 76/76 tests pass; lint and production build pass.
- Migration round trip and website backfill pass.
- A synthetic campaign was previewed, generated with two SMS drafts and archived through the
  running HTTP API. Drafts remained retained after archive.
- The live frontend exposed Campaigns to a Sales account and returned `1 eligible · 0 skipped`
  for a synthetic selected lead through the real preview endpoint.
- Docker API and frontend containers are healthy.

## Deferred by decision

- Saved segments.
- Structured social presence and social-only copy.
- Draft editing, approval and rejection.
- Sender identity and registered SMS sender ID.
- Reply monitoring and opt-out ownership.
- Scheduling, quiet hours and Sunday restrictions.
- FikaTu delivery, retries and delivery status.

## Review lenses

- **Mark:** architecture, authorization, snapshot drift and transaction boundaries.
- **Sharon:** migration, repository queries, idempotency, renderer and failure-path tests.
- **Anne:** seller wording, preview clarity, draft readability, Import tutorial and responsive
  Campaign walkthrough.
