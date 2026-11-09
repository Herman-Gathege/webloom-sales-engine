# Eligibility Policy Approval Worksheet

**Status:** approved and enabled

This worksheet records the decision needed before Wadi enables automatic eligibility for the
2026-11-09 niche research batch. Completing it does not itself approve outreach; it captures the
human decision that will be translated into the versioned policy file.

## Proposed rule

| Field | Proposed value |
|---|---|
| Rule ID | `yellow-pages-generic-business-sms-v1` |
| Rule version | `1` |
| Channel | SMS only |
| Normalized source | `yellow_pages_kenya_listing` |
| Source name | `Yellow Pages Kenya listing` |
| Collection method | `Public business directory review` |
| Intended purpose | `Business outreach` |
| Contact type | `generic_business` |
| Required evidence | `source`, `source_name`, `source_url`, `collection_date`, `collection_method`, `intended_purpose`, `contact_type` |
| WhatsApp | Disabled because no source declared WhatsApp capability and FikaTu has no WhatsApp provider |
| Email | No rule because none of the current 30 records published an email address |

The public listing establishes provenance and a published business phone number. It does not
establish consent or permission to market.

## Compliance decision

### Lawful basis

Select exactly one documented category:

- [x] `legitimate_interests`
- [ ] `consent`
- [ ] `contract`
- [ ] `legal_obligation`
- [ ] `vital_interests`
- [ ] `public_interest`
- [ ] `research_statistics`

### Approval

- Policy set version: `2026-11-09.1`
- Effective date: `2026-11-09`
- Approved by, including role: `Herman Gathege, authorised policy approver`
- Approval date: `2026-11-09`
- Approval reference: `this Codex conversation dated 2026-11-09`
- Policy rationale: `Publicly published business contact details are processed for narrowly targeted B2B website outreach, with provenance, human oversight, opt-out and terminal suppression safeguards.`

### Required confirmations

- [x] The lawful basis and rationale apply to SMS outreach for generic business contacts sourced
  from a public business directory for business outreach.
- [x] Missing or ambiguous evidence must remain in `needs_review`.
- [x] A current human `needs_review` decision must remain a hold against automatic approval.
- [x] A stale human approval must not survive changed contact or provenance inputs.
- [x] Any opt-out, objection or suppression remains terminal and overrides this policy.
- [x] The policy must be disabled immediately if its legal or operational basis changes.

## Enabling the rule

The confirmed values are recorded in `backend/app/config/compliance_policy.json`. Restart the
API after changing that file and re-evaluate affected leads.
