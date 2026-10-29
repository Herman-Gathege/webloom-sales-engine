# Sprint 3 solidification — CSV to the outreach boundary

**Status:** implemented on `feature/sprint-3-solidification`; backend and frontend checks pass.
This extends the Sprint 3 authentication work without replacing it.

This slice turns an imported CSV into a reviewed, filterable pipeline. It deliberately stops
at the outreach eligibility boundary because queueing, campaign approval, dispatch, FikaTu,
and inbound reply processing do not exist yet.

## Current flow

```text
CSV upload
  → required-column and row validation
  → phone/email/text normalisation
  → phone de-duplication and provenance
  → automatic lead compliance snapshot
  → Lead Desk filters and row-level explanation
  → human channel review and/or manual suppression
  → automatic re-evaluation
  → individual or bulk outreach-readiness gate
  → [Sprint 5–6: queue, approval, dispatch, delivery, replies]
```

## Compliance outcomes

One persisted `lead_compliance_evaluation` row represents the current lead-level result.
Per-channel human decisions remain in `lead_channel_eligibility`.

| Outcome | Meaning | Can enter outreach? |
|---|---|---|
| `eligible` | At least one technically available channel has a complete human decision with a current legal basis, evidence, purpose, contact context, and rationale. Suppression and provenance checks also pass. | Yes, for the listed eligible channel only |
| `needs_review` | Source, evidence, human decision, technical availability, or another material fact is missing, stale, or ambiguous. | No |
| `blocked` | The lead is opted out, all marketing is suppressed, or every technically available channel is suppressed. | No |
| `invalid` | Required identity or usable contact data is missing or invalid. | No |

`data_quality_status` is separate: `complete`, `incomplete`, or `invalid`. A valid-looking
public phone number or email address is never treated as consent or a lawful basis.

## Automatic checks

The evaluator in `backend/app/services/compliance_evaluator.py` applies rule version
`2026-10-27.1`. It:

- applies terminal suppression and `opted_out` lead status before approval;
- checks that the selected channel has a technically usable contact;
- requires source/provenance information before eligibility;
- accepts only a complete, current human channel decision;
- preserves a stale decision for audit but refuses to use it;
- records reason codes, a readable explanation, channel results, eligible/suppressed
  channels, eligibility timestamp, rule version, and an input fingerprint; and
- reuses the saved result while that fingerprint is unchanged.

Relevant changes to contacts, provenance, source, lead status, suppression, or review evidence
change the fingerprint. Import, human review, suppression recording, and an outreach check
trigger re-evaluation.

## Human checks

An `eligible` channel review requires a lawful-basis category, evidence summary and source,
intended purpose, contact context, rationale, reviewer, and timestamp. The API takes the
reviewer from the authenticated session. A review is bound to the inputs it assessed through
`reviewed_input_fingerprint`.

The smallest action for an exception is:

1. Open the lead from the filtered Lead Desk.
2. Read the automatic result and its reason codes.
3. Correct missing provenance elsewhere, or record current channel evidence on Lead Detail.
4. Record a terminal objection through the existing suppression control when applicable.
5. Confirm the re-evaluated result before a future outreach action.

There is no bulk approval. Bulk outreach checks return one decision per lead and preserve each
lead's own blocking reason.

## Lead Desk filters

`GET /api/v1/leads` applies filters before counting and pagination. Existing sector, area,
website, status, search, limit, and offset parameters remain. The extension adds:

- `compliance_status`
- `data_quality_status`
- `provenance=available|missing|incomplete`
- `outreach_ready`
- `has_suppression`
- `batch_id`
- `source`
- `sort=newest|oldest|business_name|compliance_status`

`GET /api/v1/leads/filter-options` supplies real distinct values for the dropdowns. The Lead
Desk keeps filters in the URL and shows the automatic outcome plus concise reason on each row.

## Import summary

The existing import fields remain. The response also distinguishes:

- `created` and `accepted`;
- `matched` existing phone numbers without overwriting those leads;
- duplicate rows inside the upload;
- rejected validation rows;
- saved `eligible`, `needs_review`, `blocked`, and `invalid` outcomes;
- `provenance_incomplete`; and
- `review_rows` with row number, business name, outcome, reason codes, and explanation.

The import response links directly to batch-filtered Lead Desk views. The exact request and
response contract remains in the [CSV import contract](sprint-2-import-contract.md).

## Outreach boundary and opt-outs

`POST /api/v1/leads/{id}/outreach-check/{channel}` checks one lead.
`POST /api/v1/leads/outreach-check` checks one to 200 leads for a selected channel. Both force
a fresh evaluation and allow only a current eligible channel. They are guards, not a queue or
send endpoint.

Manual suppression is terminal. A channel restriction blocks that channel; all-marketing
suppression blocks every available marketing channel and survives lead deletion/re-import
through contact fingerprints. There is intentionally no delete-suppression endpoint.

## Not implemented

- campaign, segment, draft, queue, approval, or send records;
- FikaTu delivery calls, provider retries, or delivery status;
- inbound reply ingestion, automatic objection classification, or automatic opt-out capture;
- assignment and temperature fields, so their filters are not offered;
- WhatsApp delivery, which FikaTu does not provide.

Those gaps must close in Sprint 5–6 before the readiness gate is a true end-to-end dispatch
guard. The gate must remain a required call before every individual, bulk, retry, and
follow-up dispatch.

## Legal and business decisions still needed

- which lawful-basis category applies to each prospecting method;
- the direct-marketing interpretation of DPA section 37 and the General Regulations;
- DPIA, registration, processor-term, and cross-border requirements;
- retention periods and data-subject request procedures;
- channel-specific opt-out wording and timing.

See [compliance implementation notes](../compliance/implementation-notes.md) and the
[outreach SOP](../compliance/outreach-sop.md).
