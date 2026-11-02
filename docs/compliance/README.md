# Compliance foundation

**Status:** Sprint 2 foundation, extended in Sprint 3 with durable automatic evaluation and an
outreach readiness gate · **Not legal certification or a definitive legal opinion**

This folder is the operating summary for lead research, CSV import, channel review,
campaign approval, outreach, replies, and opt-outs. It covers the Kenya Data Protection Act,
2019 (DPA), the Data Protection (General) Regulations, 2021, and relevant Office of the Data
Protection Commissioner (ODPC) guidance. Unresolved interpretations need appropriate
professional review.

The product still exists to find a useful business prospect, prepare a relevant campaign,
obtain human approval, deliver it, record the reply, and hand an interested prospect to a
person. Compliance controls protect that work; they are not a separate product.

## Responsibility boundary

| System | Owns | Does not own |
|---|---|---|
| Wadi / Sales Engine | Lead provenance, duplicate checks, channel eligibility review, suppression, campaign approval, the human send decision, and decision history | Provider delivery, retries, templates, and channel infrastructure |
| FikaTu | Events, templates, channel providers, delivery, provider retries, and delivery status | Whether a sales prospect is eligible or a campaign is approved |
| People | Source review, truthful evidence, eligibility decisions, campaign approval, reply handling, and opt-out recording | Bypassing terminal suppression or the approved state machine |

A research CSV contains candidates. It is not consent, proof of a lawful basis, or campaign
approval. A publicly visible phone number or email address does not automatically authorise
direct marketing. All B2B contexts are not automatically exempt.

## Where to go next

- [Outreach SOP](outreach-sop.md) for the practical workflow.
- [Implementation notes](implementation-notes.md) for architecture, tests, limitations, and
  Sprint 5–6 gates.
- [Sprint 3 solidification](../delivery/sprint-3-solidification.md) for the CSV-to-outreach
  boundary, status meanings, filters, and current gaps.
- [CSV import contract](../delivery/sprint-2-import-contract.md) for exact import behavior.
- [FikaTu integration research](../research/2026-10-08-fikatu-integration-notes.md) for the
  verified delivery surface.

## Terminology

| Term | Meaning |
|---|---|
| Provenance | Traceable source, collection method/date, contact context, and intended purpose |
| `needs_review` | No positive channel decision exists; the lead may be useful but cannot be dispatched |
| `eligible` | An authorised human recorded a lawful basis and the required context for one channel |
| `suppressed` | A terminal opt-out, objection, or manual restriction overrides the saved review |
| All-marketing opt-out | Suppresses every available marketing contact, not only the channel where it was received |
| Lead compliance evaluation | The latest automatic lead-level snapshot, with data quality, reason codes, eligible/suppressed channels, timestamp, rule version, and input fingerprint |

Eligibility is independent for email, SMS, and WhatsApp. A decision for one channel never
approves another.

## Requirement types

**Confirmed legal baseline to apply with professional advice**

- Process personal data lawfully, fairly, and transparently for specified purposes, collecting
  only what is necessary and retaining it only as needed.
- Identify and record an applicable lawful basis before relying on a lead for outreach.
- Provide clear opt-out information and honour objections to direct marketing.
- Protect accuracy, security, access, and applicable data-subject rights.
- Respect restrictions and objections without requiring the person to repeat them.

Source links:

- [Kenya Data Protection Act, 2019](https://new.kenyalaw.org/akn/ke/act/2019/24/eng@2022-12-31)
- [Data Protection (General) Regulations, 2021](https://www.odpc.go.ke/wp-content/uploads/2024/03/THE-DATA-PROTECTION-GENERAL-REGULATIONS-2021-1.pdf)
- [ODPC guidance for MSMEs](https://www.odpc.go.ke/wp-content/uploads/2025/11/ODPC-%E2%80%93-Guidance-Note-on-Processing-by-MSMEs.pdf)
- [ODPC consent guidance](https://www.odpc.go.ke/wp-content/uploads/2025/09/Guidance-note-on-Consent.pdf)

**Internal operating rules in this repository**

- Every lead records source and an honestly described basis; missing evidence stays visible.
- Imports cannot mark a channel eligible.
- Suppression is terminal and checked before import, campaign preparation, and every future
  send or retry.
- Audit details identify decisions and reasons without raw contact values or message bodies.
- A human approves every campaign and every send path starts from `approved`.

**Unresolved questions requiring human or professional review**

- Which lawful basis applies to each prospecting method, including whether legitimate interests
  can be relied on in the particular context.
- The direct-marketing interpretation of DPA section 37 and the relevant General Regulations.
- Whether a DPIA, ODPC registration update, or another governance step is required.
- Retention periods and the process for responding to access, correction, objection, or erasure
  requests.
- Processor terms and cross-border arrangements for FikaTu and its providers.
- The exact wording and timing required for effective channel-specific opt-out notices.

## Review cadence

Review this folder when a channel, provider, data source, campaign process, or legal reference
changes. Compliance is a continuing product constraint. New discovery, enrichment, imports,
AI assistance, follow-ups, scoring, analytics, and integrations must preserve the same
provenance, eligibility, suppression, and audit guarantees.
