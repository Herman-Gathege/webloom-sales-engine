# Compliance implementation notes

**Implemented:** 2026-10-21 in the Sprint 2 Lead Desk slice

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
availability, and suppression history. Reviewer identity is currently self-asserted; Sprint 3
will connect it to an authenticated user.

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

- Authentication and role-gated contact visibility arrive in Sprint 3.
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
