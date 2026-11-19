# Sprint 5 — Campaigns and Drafts

**Status:** implemented and awaiting team review
**Branch:** `sprint/5-campaigns-drafts`
**Implementation owner:** Herman
**Reviewers:** Mark (architecture/security), Sharon (backend/tests), Anne (seller/copy)

This is the authoritative Sprint 5 contract. It narrows the older backlog in
[sprint-detail.md](sprint-detail.md) to one reliable seller slice.

## Goal

Create an SMS campaign from explicitly selected leads, preview who is eligible and why anyone
is skipped, then generate one immutable historical draft per eligible lead. Sprint 5 stops
before approval, scheduling or sending.

```text
active SMS offer + active SMS template
  → seller filters the Lead Desk
  → explicit selection of 1–200 leads
  → live eligibility and skip preview
  → save campaign with catalogue snapshots
  → generate once
  → immutable “Not sent” drafts + persisted skips
```

Generating a draft is not approval and is not permission to send.

## Locked decisions

1. **Selection:** explicit lead selection only. The selected lead IDs and active filter context
   are stored with the campaign. Named saved segments are deferred.
2. **Cohort cap:** 1–200 unique leads per campaign.
3. **Channel:** the Sprint 5 UI and acceptance path are SMS-only. Rendering remains
   channel-generic and email is covered by backend tests.
4. **Campaign editing:** name, goal, offer, template and selected leads may change only before
   successful generation.
5. **Generation:** one-shot and idempotent. A generated campaign is immutable. Rerunning returns
   existing drafts and skips; it creates nothing new.
6. **Missed leads:** skipped leads remain skipped in that campaign. To change the cohort or retry
   skipped leads, archive it and create a new campaign.
7. **Archive:** reversible soft archive. Drafts, skips, snapshots and events are retained.
8. **Visibility:** Admin and Sales users can view all campaigns. The creator or an Admin may edit
   before generation and archive/restore. No hard delete exists.
9. **Website:** `website_presence` is `has_website`, `no_website` or `unknown`.
10. **Social:** structured social presence and social-only copy are deferred. No social filter is
    presented in Sprint 5.
11. **Research freshness:** show the provenance collection date. Research older than 90 days or
    missing a date receives a re-check warning but does not automatically block generation.
12. **Skip copy:** seller-facing reason labels and grouped counts; technical decision detail
    remains available through disclosure.
13. **Goal:** required free text describing the intended business outcome. It is not used for
    reporting in Sprint 5.
14. **Draft state:** read-only in Sprint 5 and visibly labelled **Not sent**. Editing belongs to
    the Sprint 6 approval queue.
15. **Catalogue drift:** campaign creation snapshots offer/template content and fingerprints.
    Generation is rejected if those records changed or became inactive.
16. **Draft snapshot:** exact rendered body, offer/template content and IDs, eligibility/policy
    references, evaluation time, SMS metrics and generation time.
17. **Opt-out variable:** `{{opt_out}}` renders as **“Reply STOP to opt out.”**
18. **Sender identity:** not required to generate drafts. Sender name, responsible person and a
    registered sender ID are hard prerequisites before Sprint 6 sending.
19. **Reply/opt-out ownership:** deferred to Sprint 6. Sending must not begin until a named human
    owns reply monitoring and suppression recording.
20. **Business-name verification:** happens at the later approval stage.
21. **Source review:** click the stored provenance URL when present. If absent, show a clearly
    labelled Google Search fallback based on business name and area. Do not scrape or persist a
    guessed URL as provenance.
22. **Starter Website:** public copy may say **“From KES 40,000.”**
23. **Timing:** quiet-hours and Sunday restrictions belong to Sprint 6.
24. **Activity UI:** show seller-relevant fields normally and put long technical values in a
    wrapped, collapsed disclosure.
25. **Import help:** a compact three-step Wadi tutorial, not a separate wizard.

## Seller workflow

1. Open **Campaigns → New campaign**.
2. Enter a campaign name and outcome-oriented goal.
3. Choose an active offer and active SMS template.
4. Reuse Lead Desk filters, then explicitly select 1–200 leads.
5. Preview current eligibility and grouped skip reasons.
6. Save the campaign as Draft.
7. Edit it before generation if required.
8. Confirm generation with a warning that drafts freeze and will not be sent.
9. Review read-only **Not sent** drafts and excluded leads.
10. Archive or restore the campaign when needed.

## Screens

- **Campaign List:** status, archived filter, owner, counts and dates.
- **Campaign Create/Edit:** name, goal, offer, SMS template, filtered lead selector and preview.
- **Campaign Detail:** configuration, eligibility basis, drafts, skips, generation and archive
  controls.

No Segments screen ships in this slice.

## Eligibility and suppression

- `OutreachGateService` remains the only outreach eligibility boundary.
- Preview rechecks every selected lead and does not create drafts.
- Generation rechecks every lead immediately before rendering.
- A restriction, opt-out, stale review, missing contact or policy/human-review failure between
  preview and generation becomes a persisted skip.
- The existing policy-approved SMS versus human-approved distinction remains visible.
- Sprint 6 must check again at approval and dispatch.

## Draft rendering

Allowed variables remain `business_name`, `sector`, `area`, `website_status`, `has_website`,
`offer_name`, `price_range`, `pitch_angle` and `opt_out`.

- Missing required lead or offer data skips that draft.
- Website-dependent copy is skipped when `website_presence=unknown`.
- Missing price guidance skips a template using `price_range`.
- No unresolved placeholder or raw contact detail may appear in a draft.
- SMS metrics account for GSM-7 and Unicode; the exact encoding, character/septet count and
  segment count are stored.

## State and idempotency

- `generated_at IS NULL` and `archived_at IS NULL` → **Draft**
- `generated_at` set and `archived_at IS NULL` → **Generated**
- `archived_at` set → **Archived**

Draft and skip writes happen in one transaction. `generated_at` is set only after the complete
set succeeds. The database enforces one draft per campaign/lead/channel. Migration `0006`
creates the campaign records and preserves the seller's filter context.

## API surface

- `POST /api/v1/campaigns/preview`
- `POST /api/v1/campaigns`
- `GET /api/v1/campaigns`
- `GET /api/v1/campaigns/{id}`
- `PATCH /api/v1/campaigns/{id}`
- `POST /api/v1/campaigns/{id}/generate`
- `POST /api/v1/campaigns/{id}/archive`
- `POST /api/v1/campaigns/{id}/restore`

All require a password-current `admin` or `sales` session. Catalogue writes remain Admin-only.

## Out of scope

- saved segments;
- social-presence targeting or social-only copy;
- draft editing;
- approval or rejection;
- campaign scheduling, quiet hours or Sunday restrictions;
- sending, FikaTu, retries or delivery status;
- replies, qualification, handoff or analytics;
- AI generation or automatic segmentation.

## Acceptance

- A Sales user can filter, explicitly select up to 200 leads, preview and create an SMS campaign.
- Preview returns explainable eligible and skipped counts.
- Generation creates exactly one immutable draft per currently eligible lead.
- All other selected leads have persisted, readable skip reasons.
- A second generation request returns the first result unchanged.
- Later catalogue, policy or template edits do not change stored drafts.
- Suppression or eligibility changes after preview are caught at generation.
- Suspended dependencies do not leak into code: no sender integration, approval queue,
  scheduling, FikaTu client or send path exists.
- Archive/restore preserves all campaign history.
