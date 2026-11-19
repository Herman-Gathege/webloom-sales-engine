# Sprint 5 — Team Roadmap

Welcome. Wadi is a sales-scouting tool for Webloom + Innovations (Nairobi). It turns a
researched market into qualified, human-ready conversations. **Websites are the entry
offer, not the ceiling.** Automation creates the opportunity; a human converts it.

## How we got here

| Sprint | What it added |
|---|---|
| 1 | Lead and Activity model, Lead Desk, seed data |
| 2 | CSV importer, filters, compliance foundations (provenance, suppression, eligibility review) |
| 3 | Authentication: email/password login, `admin`/`sales` roles, forced first-login password change |
| 4 | Offers and templates catalogue (prices, variables, SMS/email) |
| 5 | **Campaigns and drafts** — select leads, preview eligibility, generate immutable "Not sent" drafts, archive/restore |

## What Sprint 5 adds

- Explicit SMS campaign selection (Lead Desk filters, 200-lead cap).
- Eligibility/skip preview through `OutreachGateService`.
- One-shot, atomic draft generation with canonical opt-out text and SMS segment counts.
- Catalogue drift detection and snapshot preservation.
- Read-only "Not sent" drafts, persisted skip reasons, archive/restore, campaign history.

## Where the workflow ends today

```
Lead discovery → import → provenance → compliance → eligibility decision
  → offer/template selection → campaign selection → preview → draft generation → Not sent
```

Wadi stops **before** approval and sending. There is no approval queue, no FikaTu delivery,
no scheduling, no reply capture yet (Sprints 6–9).

## What comes next (high level)

- Sprint 6: approval queue + FikaTu delivery (needs a change in the FikaTu repo first).
- Sprint 7: reply capture, qualification, handoff.
- Sprint 8: deals, reporting.
- Sprint 9: pilot, security review, deployment.

## Why everyone tests the full workflow first

Campaigns only make sense once you have imported a lead, read its provenance, checked its
compliance, and understood why a lead is skipped. Skipping the earlier stages makes the
campaign screen look like a simple form. It is not.

## Read next

- [Team walkthrough](team-walkthrough.md)
- [Sprint 5 contract](../../delivery/sprint-5-campaigns-drafts.md)
- [Visual workflow](../../workflow-description.md)
- [Sprint 5 status](status.md)
