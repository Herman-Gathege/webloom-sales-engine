# Outreach SOP

This is the practical path from research to a human sales conversation. Use synthetic examples
in documentation; real contact data stays in the gitignored `data/` directory.

## 1. Research a useful batch

- Work in practical batches, normally about 50 candidate businesses.
- Use sources whose terms permit the research.
- Capture the listing/source URL, collection date and method, contact type, business identity,
  available contact details, and intended purpose.
- Do not write "consent" or "permission" unless evidence actually exists.
- Remove businesses already known to be suppressed before preparing outreach.

**Stop:** do not turn an uncertain source or public contact into a claimed lawful basis.

## 2. Review the CSV

Use the [import contract](../delivery/sprint-2-import-contract.md). The seven original columns
remain required. Add the optional provenance columns whenever the research process supports
them. Missing optional fields do not reject a useful business; they leave it in review.

Check the import result for:

- accepted rows;
- refused rows and actionable reasons;
- duplicate rows;
- accepted rows requiring compliance review;
- warnings for malformed optional provenance values.

Never invent a source URL, collection date, evidence, or review decision to clear a warning.

## 3. Review provenance and channel eligibility

Open each imported lead and confirm provenance before making a channel decision. Email, SMS,
and WhatsApp are reviewed separately.

For an `eligible` decision, record:

- the applicable lawful-basis category;
- the permission evidence and its source;
- the intended purpose;
- the contact context;
- the reviewer and timestamp;
- a decision rationale.

The stored categories are `consent`, `contract`, `legal_obligation`, `vital_interests`,
`public_interest`, `legitimate_interests`, and `research_statistics`. Choosing a category is a
human assessment; the system records it and does not decide whether it is legally sufficient.

If the evidence is absent or ambiguous, leave the channel `needs_review`. Do not infer consent
from a public listing or from the fact that a business owns a contact channel.

## 4. Prepare the campaign

- Use an approved offer and a sanctioned channel template.
- Select only leads whose channel review says `eligible` and whose effective state is not
  `suppressed`.
- Confirm the message is relevant to the recorded purpose and contact context.
- Include a clear, channel-appropriate way to object or opt out.
- Keep pacing configured; the objective is targeted outreach, not a burst.
- Do not enable WhatsApp while FikaTu has no WhatsApp provider.

## 5. Obtain human approval

A campaign and every send must pass the existing human approval path. The approved record must
identify the approver, timestamp, campaign, channel, message version, and any conditions.

**Never:** approve in bulk merely to clear a queue, send from `draft`, or route around a blocked
lead.

## 6. Dispatch through FikaTu

Before every attempt and every retry, the Sales Engine must recheck:

1. campaign approval is current;
2. the selected channel is `eligible`;
3. no all-marketing or channel restriction applies;
4. the intended purpose/contact context still match the approved campaign;
5. the opt-out mechanism is present;
6. a stable idempotency reference prevents a retry from creating a second send.

Record allowed and blocked decisions, reason codes, FikaTu references, delivery outcomes, and
failures. FikaTu owns provider retries and delivery status; it does not decide sales eligibility.

## 7. Handle replies and objections

- Record a reply against the relevant lead and outreach.
- If the person objects to one channel, record that channel restriction.
- If they request no more marketing, record `all_marketing`; this covers every available
  channel and all future follow-ups.
- Cancel queued messages when a new restriction applies.
- Keep the note short and relevant. Never copy unnecessary message content into audit details.

Suppression is terminal. The current UI offers no removal path.

## Dispatch decision checklist

| Check | Block when |
|---|---|
| Campaign approval | Missing, rejected, expired, or changed after approval |
| Channel decision | `needs_review`, missing evidence, or stale purpose |
| Suppression | Any matching all-marketing or selected-channel restriction |
| Technical contact | Missing address/number, or unusable for the channel |
| Message | Missing required opt-out path or unapproved content |
| Idempotency | No stable outreach/attempt reference |
| Delivery channel | WhatsApp while the provider is absent |

The full current implementation status is in [implementation notes](implementation-notes.md).
