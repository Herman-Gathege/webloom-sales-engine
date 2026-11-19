# ADR-002 — Campaign drafts are immutable, one-shot historical records

**Date:** 2026-11-19  
**Status:** Accepted  
**Deciders:** Herman Gathege, Mark Mwenesi, Sharon Kendi, Anne

## Context

Sprint 5 prepares SMS campaigns but does not approve or send them. Allowing drafts to change
silently would make later approval, suppression checks and learning unreliable. Regenerating a
campaign would also create ambiguous relationships to policy decisions and catalogue content.

## Decision

- A campaign is editable only before its first successful generation.
- Generation is one atomic, one-shot operation over its fixed explicit lead set.
- Rerunning generation returns the existing drafts and skips unchanged.
- Skipped leads remain skipped in that campaign. A new campaign is required to retry them.
- Each draft is read-only and labelled **Not sent**.
- Drafts preserve the rendered body, offer/template snapshots, eligibility and policy references,
  SMS metrics and generation timestamp.
- Archiving is reversible. Archived campaigns and all historical records remain visible but
  immutable until restored.
- No hard-delete campaign API is introduced.

Campaigns use `generated_at` and `archived_at` instead of a broad sending-oriented status field:
Draft, Generated or Archived.

## Why

This gives the team a stable record of what was selected, what was skipped and why, and exactly
what text the seller reviewed. It makes duplicate prevention enforceable with database
constraints and keeps draft preparation separate from later approval and delivery.

## Trade-offs

- A mistaken campaign must be archived and rebuilt rather than regenerated in place.
- Newly eligible skipped leads are not picked up by another generation attempt.
- The schema stores more snapshot data than a minimal draft table would.

These costs are accepted because historical correctness is more important than regeneration
convenience during the first campaign slice.

## Revisit when

Sprint 6 introduces approval versions, or if the team demonstrates a concrete need for
versioned regeneration while preserving approval and suppression history.
