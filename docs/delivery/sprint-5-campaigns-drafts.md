# Sprint 5 Review — Campaigns and Drafts

**Status:** contract review; implementation has not started.

This review turns the Sprint 5 backlog into a practical first slice. It does not replace
[the sprint detail](sprint-detail.md); it records what must be decided before implementation.

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
SMS rule. Email rendering may be implemented behind the same interface, but email leads still
need a current approved policy or complete human eligibility decision.

## Gates carried from Sprint 4

- Campaign inputs must be active; an active template under an inactive offer is not usable.
- Eligibility means a current approved policy or a complete current human decision.
- Raw phone numbers and email addresses never appear in template bodies.
- Every active template includes `{{opt_out}}`.
- Missing price guidance cannot produce an unsupported price claim.
- Draft generation snapshots offer/template content, eligibility basis, policy version and the
  exact rendered body.

## Decisions required before implementation

1. **Lead selection:** explicit selection first, saved segments in the same slice, or saved
   segments immediately after the first demo?
2. **Campaign size:** what maximum keeps preview and generation predictable for a four-person
   team?
3. **Channel scope:** SMS only for the first demo, or SMS plus email rendering?
4. **Eligibility scope:** require current policy/human eligibility at campaign creation,
   generation time, or both? Recommendation: both, with the final check repeated later at send.
5. **Missing variables:** which variables are required for each channel, and what exact skip
   reason is shown?
6. **Copy pack:** approve A/B and social-only variants, channel length limits, price phrasing and
   final opt-out text before a real campaign.
7. **Template history:** confirm that snapshotting the rendered draft is sufficient for Sprint 5
   and full template version history remains later.
8. **Roles:** may Sales create campaigns and generate drafts, or only Admins? Current role model
   has no campaign-specific decision.
9. **Screen inventory:** settle how Campaign List, Campaign Detail, Segments and Draft Preview
   fit the unresolved 13-screen inventory.
10. **Idempotency:** confirm regeneration replaces untouched drafts, skips approved/historical
    drafts, or is refused once generation has completed.

## Proposed acceptance criteria

- A campaign records offer, template, channel, owner, goal and selection criteria.
- Inactive offers/templates cannot be selected.
- Preview returns the eligible count and one explainable skip reason per excluded lead.
- Generation creates one draft per eligible lead and no duplicate on rerun.
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

## Readiness verdict

Sprint 5 is technically ready for a small SMS campaign slice, but not ready for implementation
until decisions 1–4, 6 and 8–10 are accepted. The 13-screen inventory is still a planning gap,
not a reason to block this review.
