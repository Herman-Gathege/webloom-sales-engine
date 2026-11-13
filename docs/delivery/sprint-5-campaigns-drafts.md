# Sprint 5 — Campaigns and Drafts

**Status:** active · **Branch:** `sprint/5-campaigns-drafts`

**Implementation owner:** Herman — implementation is intentionally solo this sprint.

**Reviewers:** Mark (architecture/backend), Sharon (backend/tests), Anne (seller workflow/copy).
Reviewers do not open parallel implementation work.

This contract turns the Sprint 5 backlog into a practical vertical slice. It does not replace
[the sprint detail](sprint-detail.md).

## Goal

Create a deliberate campaign from an active offer and active template, select eligible leads,
preview what will be skipped and why, and generate exactly one historical draft per eligible
lead. Sprint 5 stops before approval and sending.

## First vertical slice

```text
Active offer + active template
  → explicit lead selection or saved segment
  → live eligibility/skip preview
  → create campaign
  → generate one draft per eligible lead
  → persist rendered body and source versions
  → show draft and skip counts
  → stop
```

SMS is the first channel because the approved policy currently supports one Yellow Pages Kenya
SMS rule. Email rendering may be implemented behind the same interface and tested, but the
Sprint 5 live demo is SMS-only. Email leads still need a current approved policy or complete
human eligibility decision.

## Gates carried from Sprint 4

- Campaign inputs must be active; an active template under an inactive offer is not usable.
- Eligibility means a current approved policy or a complete current human decision.
- Raw phone numbers and email addresses never appear in template bodies.
- Every active template includes `{{opt_out}}`.
- Missing price guidance cannot produce an unsupported price claim.
- Draft generation snapshots offer/template content, eligibility basis, policy version and the
  exact rendered body.

## Decisions locked for Sprint 5

1. **Lead selection:** explicit lead selection ships in the first vertical slice. Saved segments
   follow after that checkpoint works end to end, within the same sprint if time allows.
2. **Campaign size:** a campaign may contain at most 200 selected leads, matching the existing
   bulk outreach-check limit.
3. **Channel scope:** SMS is the live/demo channel. Email may share implementation and test
   coverage but is not presented as outreach-ready without an approved email policy or current
   human decisions.
4. **Eligibility scope:** eligibility is checked in preview and rechecked during generation.
   Sprint 6 must check again at approval and dispatch.
5. **Missing variables:** every variable declared by the template must resolve to a nonblank
   value. Missing lead or offer data produces a visible skip reason; blank price guidance skips a
   template that uses `{{price_range}}`.
6. **Copy pack:** the existing seeded SMS template is sufficient for implementation tests. Anne
   must review final A/B, social-only, price phrasing, channel length and opt-out copy before a
   real campaign is approved.
7. **Template history:** Sprint 5 snapshots the exact rendered body plus offer/template content
   and policy/decision references. Full template version history remains later work.
8. **Roles:** both `admin` and `sales` may create campaigns and generate drafts. Only `admin`
   continues to manage the catalogue.
9. **Screens:** Campaign List, Campaign Create/Preview, Campaign Detail with Draft and Skip
   sections, and Segments. These settle the Sprint 5 portion of the unresolved screen inventory.
10. **Idempotency:** generation is one-way for a campaign. Once drafts exist, rerunning returns
    the existing drafts and never replaces or duplicates them in Sprint 5.

## Proposed acceptance criteria

- A campaign records offer, template, channel, owner, goal and selection criteria.
- Inactive offers/templates cannot be selected.
- Preview returns the eligible count and one explainable skip reason per excluded lead.
- Generation creates one draft per eligible lead, and rerunning returns the existing drafts
  without replacement or duplication.
- Every draft has a stable campaign/lead/template reference and rendered-body snapshot.
- Missing required variables and blank price guidance produce visible skips, never invented
  content.
- Suppressed, opted-out, technically unavailable, stale or review-only channels do not receive
  sendable drafts.
- The UI identifies policy-approved versus human-approved eligibility.
- No approval, queue, send or FikaTu call exists in this sprint.

## Out of scope

- human approval or rejection;
- sending, FikaTu delivery, retries or status sync;
- reply capture, qualification or handoff;
- AI-generated copy or automatic segmentation;
- full template version history;
- WhatsApp delivery;
- analytics.

## Ownership and hand-off

| Person | Sprint responsibility |
|---|---|
| Herman | All implementation, migrations, APIs, frontend, tests and demo |
| Mark | Architecture/security review and final demo challenge |
| Sharon | Backend correctness, migration and test review |
| Anne | Seller workflow, copy, skip reasons and usability review |

No reviewer creates a competing implementation branch. Reviews are performed against Herman's
hand-offs on `sprint/5-campaigns-drafts`.

## Readiness verdict

Sprint 5 is ready to implement. The branch was cut from merged Sprint 4 main, the first vertical
slice is bounded, and approval/sending remain outside the sprint.
