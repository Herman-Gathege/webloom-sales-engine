# Mark — Sprint 2

> **Where we are:** Sprint 1 shipped — the API, the UI and the containers you built all work.
> Nothing checks our work automatically yet. **Your piece this sprint:** CI, and keeping the
> importer honest on the way in.

## Your mission

Make a broken test impossible to ignore.

## What to do

- Add one GitHub Actions workflow that runs on every pull request: backend lint and tests, and
  frontend lint, build and tests.
- The backend suite needs PostgreSQL 17 — a service container is fine. Use the same setup that
  already works in Compose rather than inventing a second one.
- Turn on branch protection so the checks must pass before a merge.
- Review Sharon's importer PR — it touches the schema, so it needs two approvals with you as one
  of them. Look for the rows that would be silently dropped.

If this is turning into more than a day, stop after the backend job lands and tell us — one
working check is worth more than two broken ones.

## Done means

- Opening any pull request shows the checks running.
- A deliberately broken test fails the build — prove it once, then revert the break.
- `main` requires the check before merge.
- Sharon's schema changes have been reviewed.

## Bring back

- A small PR with the workflow file.
- One red run and one green run, so we can all see what it looks like.
- The one thing that surprised you, and anything you had to decide alone.
