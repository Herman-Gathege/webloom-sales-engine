# Sharon — Sprint 5 Backend Review

## Your mission

Audit the campaign/draft backend and tests as a reviewer, without opening a parallel branch.

## What to review

- Run the migration upgrade/downgrade and Alembic drift check.
- Verify campaign creation and selection enforce the 200-lead maximum.
- Verify active offer/template rules and role permissions.
- Verify preview and generation use current policy or current human eligibility.
- Verify every skip path is persisted or returned with a clear reason.
- Verify snapshots cannot change when offers or templates are edited later.
- Verify rerunning generation neither duplicates nor replaces drafts.
- Check transaction behaviour, rollback safety and query efficiency for 200 leads.
- Review failure-path tests, not only the happy path.

## Done means

- [ ] Backend approval or findings with reproduction commands.
- [ ] Migration and idempotency evidence included.
- [ ] Missing tests identified explicitly.
- [ ] No direct code is pushed by you.

## Bring back

Approve/block verdict, commands run, and exact failing cases or missing coverage.
