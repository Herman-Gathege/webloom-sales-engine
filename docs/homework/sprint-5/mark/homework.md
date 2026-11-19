# Mark — Sprint 5 Architecture Review

## Your mission

Review Herman's Sprint 5 implementation for architecture, security and integration risks without
creating a competing implementation.

## What to review

- Read the [Sprint 5 contract](../../../delivery/sprint-5-campaigns-drafts.md).
- Check the campaign/draft boundaries and whether mutable catalogue data is snapshotted.
- Review the migration, constraints, ownership and 200-lead limit.
- Confirm policy-approved SMS is eligible without falling back to mandatory human review.
- Confirm suppression, opt-out, stale evidence and technical availability gates cannot be
  bypassed.
- Confirm idempotency prevents duplicate or replacement drafts.
- Confirm no approval, send, queue or FikaTu path leaked into Sprint 5.
- Identify only decisions that block Sprint 6 or would be expensive to reverse.

## Done means

- [ ] Architecture approval or a concise findings list.
- [ ] Migration and security concerns have evidence.
- [ ] Sprint 6 dependencies are named.
- [ ] No direct code is pushed by you.

## Bring back

Approve/block verdict, findings ordered by severity, and any required fix before merge.
