# Compliance implementation notes

**Implemented:** 2026-10-21 in the Sprint 2 Lead Desk slice

**Extended 2026-10-27:** automatic, durable lead eligibility and the outreach readiness gate.
The original Sprint 2 notes below remain the history of the channel-review and suppression
foundation. The current end-to-end boundary is documented in
[Sprint 3 solidification](../delivery/sprint-3-solidification.md).

This note records the current implementation, not a future-state claim. Campaign, outreach,
worker, retry, FikaTu client, and delivery-result models do not exist yet. Sprint 5–6 must use
the records and gates below when those models are added.

## Decisions

Deployment runs the reversible `0002` Alembic migration before the API starts. It adds
`leads.email`, structured activity details, import batches, provenance, channel eligibility,
and suppressions, then backfills three `needs_review` rows for every existing lead.

### Provenance

Each imported lead may have one `lead_provenance` row with import batch, CSV row, source URL,
collection date/method, intended purpose, contact type, and contact name. Optional fields may
be null; missing evidence is not replaced with invented values. An `import_batches` row records
file totals, including uploads where every row was refused.

### Channel review

`lead_channel_eligibility` has one row per lead and channel. New, seeded, and migrated leads
start `needs_review` for email, SMS, and WhatsApp. `eligible` requires a lawful-basis category,
evidence summary/source, purpose, contact context, reviewer, timestamp, and rationale.

The API is:

- `PUT /api/v1/leads/{id}/eligibility/{channel}`
- `POST /api/v1/leads/{id}/suppressions`

Lead Detail returns provenance, three effective channel states, each channel's technical contact
availability, and suppression history. Since Sprint 3 the reviewer identity comes from the
authenticated session; a request body can no longer claim to be someone else.

### Suppression

Suppression rows store a SHA-256 fingerprint and contact kind instead of raw contact details.
The row is linked to a lead for navigation, but the fingerprint is canonical: deleting or
re-importing a lead does not erase the restriction. All-marketing suppression creates a record
for every available contact. It makes all three effective channel states `suppressed`.

There is deliberately no API operation to remove a suppression. Recording the same scope again
is idempotent and does not duplicate the audit event.

### Import behavior

The seven original required columns and phone de-duplication remain unchanged. Optional columns
are `Email`, `Contact name`, `Contact type`, `Source URL`, `Collection date`, `Collection method`,
and `Intended purpose`. `Date added` is the collection-date fallback; written `Source` is the
collection-method fallback.

Invalid optional values create warnings. They do not reject a lead that is otherwise usable.
An all-marketing suppression blocks a fresh import with `suppressed_contact`. Channel-specific
suppressions do not block import but remain effective against the recreated lead.

### Audit

Eligibility and suppression changes create append-only `activities` entries with structured
details. Audit details contain state, channel, scope, reason code, and actor facts. They must
not contain phone numbers, email addresses, message bodies, or export contents.

## Test coverage

The PostgreSQL-backed suite covers:

- legacy and extended CSV mapping;
- import totals and all-refused batches;
- provenance persistence and fallback values;
- independent channel review and missing-evidence rejection;
- suppress/re-import and channel-independent effective state;
- all-marketing idempotency;
- audit details without raw contacts;
- seed backfill and migration upgrade/downgrade/upgrade.

The frontend suite covers provenance and state display, independent review submission,
all-marketing confirmation, sample-mode mutation blocking, and import summary counts.

## Known limitations

- Authentication arrived in Sprint 3 with two roles, `admin` and `sales`. Both may see contact
  details because both work the lead desk; there is no read-only role yet. Add field-level
  gating when such a role exists.
- Nothing sends yet, so no dispatch attempt can be blocked or audited in this slice.
- FikaTu has no WhatsApp provider. WhatsApp eligibility is stored but delivery is unavailable.
- There is no automated reply ingest; replies and opt-outs are recorded by a person.
- Legal interpretation, retention, DPIA need, registration, processor terms, and detailed
  notice wording remain human decisions.
- The CI workflow verifies both applications, but marking its checks as required in GitHub
  branch protection remains a repository-administrator action.

## Sprint 5–6 carry-forward gates

Campaign preparation:

- exclude `needs_review`, `suppressed`, technically unavailable, and opted-out leads;
- keep channel selection explicit and record the policy/version used;
- show approval conditions and skip reasons before a campaign is approved.

Approval and dispatch:

- only `approved` outreach may be queued; only `queued` outreach may be sent;
- re-read campaign approval, purpose, eligibility, suppression, and technical contact state
  immediately before each FikaTu attempt and each retry;
- block queued follow-ups when a new objection or opt-out arrives;
- persist an idempotency key and FikaTu reference before retry is possible;
- record blocked attempts, provider outcomes, failures, and terminal status without raw
  message/contact data in audit details;
- enforce channel-specific opt-out content and pacing;
- leave WhatsApp disabled while the provider is absent.

These are acceptance criteria for the sending sprint, not claims that sending is already safe.

## 2026-10-27 solidification

Migration `0004` adds `lead_compliance_evaluation`, provenance `source_name`, reviewed-input
fingerprints, and import outcome counters. `ComplianceEvaluator` (rule `2026-10-27.1`) now
derives one durable lead-level outcome: `eligible`, `needs_review`, `blocked`, or `invalid`.
Data quality is stored separately as `complete`, `incomplete`, or `invalid`.

An approval is current only while its channel review remains complete and its
`reviewed_input_fingerprint` matches current contacts, source, provenance, and evidence.
Stale human decisions stay in history but cannot make a lead eligible. Unchanged inputs reuse
the same snapshot and do not append a repeated audit event.

Imports automatically evaluate saved rows and return actual created, matched, duplicate,
rejected, eligible, needs-review, blocked, invalid, provenance-incomplete, and row-review
counts. The Lead Detail API and Lead Desk list expose the current snapshot and reasons.

The canonical action boundary is `POST /leads/{id}/outreach-check/{channel}` or the bulk
`POST /leads/outreach-check`. It forces re-evaluation immediately before the decision. This is
still not a queue or send path. Sprint 5–6 must call it from every dispatch and retry.

Inbound replies and automatic opt-out ingestion remain absent. A signed-in person records an
opt-out or objection through the existing suppression endpoint.
