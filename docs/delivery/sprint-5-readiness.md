# Sprint 5 — Seller Readiness

**Status:** lead preparation barriers removed; campaign implementation and business decisions
below still determine the final seller-walkthrough verdict.

This page turns [Anne's Sprint 5 review](../homework/sprint-5/anne/anne-review.md) into concrete
requirements. It does not expand Sprint 5 into approval, sending or FikaTu delivery.

## Lead preparation

Sellers now have two supported paths:

1. **Add lead** in the Lead Desk creates one researched business. Business name and source are
   required, plus at least one phone number or email. Phone values use the importer's Kenyan
   format rules; duplicate phones are refused. The lead receives provenance, three
   `needs_review` channel records, a compliance snapshot and audit activity.
2. **Import** explains required and optional columns and offers a downloadable template
   generated from the importer's own schema. Replace the fictional rows with authorised data;
   upload the completed file as UTF-8 CSV.

The campaign fixture is
[`backend/tests/fixtures/campaign_readiness.csv`](../../backend/tests/fixtures/campaign_readiness.csv).
It uses reserved phone ranges, fictional names and `example.test` contacts.

### Loading the campaign fixture

1. Sign in as an `admin` or `sales` user.
2. Open **Import** and upload `campaign_readiness.csv` unchanged.
3. Review the returned eligible, review, blocked and invalid counts.
4. The fixture expects all eight rows to be accepted. It covers websites, no-website and
   social-only research, mobile and landline numbers, present and absent email, approved
   Yellow Pages SMS evidence, and contexts that correctly fall back to review.

| Records | What they exercise |
|---|---|
| Bakery, Tailors, Dental and Landline Studio | Yellow Pages evidence that can be evaluated against the current SMS policy, plus mobile/landline, email/no-email, website and social-only variation. |
| Logistics and Hardware | Google Maps records that correctly remain review-only under the current policy; one has no email. |
| Agrovet and Optician | Seller-researched records that remain review-only, including has-website and no-website cases. |

Importing the same file twice is safe: every phone is refused as a duplicate and no second
lead is created.

### Removing fixture data from a development database

Run this only against a known development database:

```sql
BEGIN;
DELETE FROM leads
WHERE business_name LIKE 'Synthetic Wadi %'
  AND id IN (
    SELECT lead_id
    FROM lead_provenance
    WHERE source_url LIKE 'https://example.test/%'
  );
DELETE FROM import_batches
WHERE filename = 'campaign_readiness.csv';
COMMIT;
```

The import batches are deleted only after their synthetic leads. A full `docker compose down -v`
is a clean development reset, but it removes every local database record and volume; do not use
it where real data matters.

## Campaign requirements from Anne

These are requirements for the campaign/draft implementation, not claims that they are built.

### A. Generation warning and campaign archiving

- Before generating, show the campaign name, offer, template, channel, selected count,
  eligibility recheck boundary and the fact that generated drafts cannot be regenerated in
  Sprint 5.
- Require explicit confirmation.
- A mistaken campaign needs a soft-archive action, never hard deletion.
- Recommendation for team approval: archived campaigns retain drafts, skips and audit history;
  remain viewable through an archive filter; and can be restored by an authorised user.

### B. Plain-language skip reasons

- Show seller-facing reasons such as **Landline only**, **Opted out**, **Missing contact
  details**, **Needs review** and **Research incomplete**.
- Show a count beside each reason in preview and campaign detail.
- Map these labels from the actual evaluator outcomes; do not replace the detailed internal
  reason codes or policy evidence used for audit.

### C. Website and social-presence targeting

- Filters must distinguish `has website`, `no website`, and `not checked`; an empty field alone
  must never mean “no website.”
- Social presence needs a structured, researched value before social-only copy is targeted.
- Unknown and unverified values are separate from confirmed absence and must remain visible in
  preview selection rules.

### D. Draft status

- Every generated draft is visibly labelled **Not sent**.
- Generation is not approval and is not delivery.
- Approval and sending remain separate, out-of-scope stages.

### E. SMS length and segment count

Every SMS draft preview must show:

- character count;
- encoding: GSM-7 or Unicode;
- segment count;
- a warning when more than one segment is required.

Use GSM-7 limits of 160 characters for one segment and 153 per concatenated segment. Unicode
(UCS-2) uses 70 characters for one segment and 67 per concatenated segment. Characters outside
the GSM-7 alphabet force Unicode encoding.

### F. Campaign goal

The goal describes the intended business outcome, not the message body. Guidance example:

> Book five qualified website consultations with independent pharmacies in Nairobi this month.

### G. No-website credibility

- Show the lead's `collection_date` beside website research.
- Mark old or missing research as needing a re-check.
- Do not present stale or absent research as a verified “no website” fact.
- A future verification field should record `unchecked`, `verified_present`,
  `verified_absent` and the verification date. That field does not exist yet.

### H. Sender identity

An approved message must identify:

- Webloom as the organisation;
- the real person responsible for the outreach;
- a registered SMS sender ID where the provider requires one.

The sender ID and the named sender are not yet confirmed. Do not present an invented sender ID
as approved.

### I. Replies and opt-out ownership

Reply monitoring is human-owned until an inbound-reply process exists. The team must name:

- who checks replies;
- who records an opt-out or objection;
- where the record is maintained;
- how the terminal suppression is verified before any later campaign.

No owner is assigned in this readiness change.

### J. Starter Website pricing

The repository seed contains **KES 40,000** for Starter Website, but Anne's review asks whether
customer copy should say **from KES 40,000** or **exactly KES 40,000**. That is an open business
decision. Campaign copy must not make an unconfirmed pricing promise.

### K. Business-name verification

Before draft approval, a human verifies spelling, capitalisation, branch name and whether the
message addresses the correct business. Generated text alone never establishes approval.

### L. Timing restrictions

No messages at night or on Sundays is explicitly a **Sprint 6** requirement. Scheduling and
delivery remain outside this sprint.

## Open decisions

| Decision | Current state | Recommendation |
|---|---|---|
| Campaign archive and restore | Open | Soft archive, retain history, allow authorised restore |
| Starter Website wording | Open | Anne/business owner confirms before live copy |
| Reply and opt-out owner | Open | Assign one named human and a daily check |
| Named sender and SMS sender ID | Open | Confirm both before approval/sending |
| Social-presence representation | Not modelled | Add a structured verified value before social-only targeting |

## Readiness verdict

**Ready with known limitations.** Sellers can now create individual leads and download a
compatible CSV template. The campaign workflow can be exercised once its Sprint 5 implementation
is present, but the open business decisions above must be resolved before any real campaign is
approved or sent.
