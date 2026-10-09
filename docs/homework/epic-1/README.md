# Epic 1 — First Lego Block

## Goal

Get one tiny piece of the Sales Engine working together.

## Where we are right now

- **Herman — done.** The frontend shell is merged: Lead List, Lead Detail with activity, and
  a client that runs on sample data until the API answers.
- **Sharon — done.** The Lead backend is merged: the two tables, the migration, the seed,
  the two read endpoints and their tests.
- **Mark — next.** Containerise the system so one command starts the database and the API
  together, on a port that is not already taken. Branch `chore/epic-1-docker`.
- **Anne — next.** Use the two screens as a salesperson, give feedback, and land her example
  lead in the seed data. Branch `docs/epic-1-seller-review`.

Both halves are on `main` and the slice works when started by hand, but nothing starts them
together yet, and nobody has used it as a seller. The full picture — what is done, what is
verified, what is left — is in [status.md](status.md).

The agreed Lead and Activity shapes live in
[`docs/delivery/epic-1-lead-contract.md`](../../delivery/epic-1-lead-contract.md).

## The loop

Agree → Build → PR → Review → Merge → Run → Demo → Next block

## First demo

```text
Start app
  ↓
Load/import sample leads
  ↓
See Lead List
  ↓
Open Lead
  ↓
See Lead details
  ↓
See basic activity/history
```

## Who does what

- **Anne** → tells us what the seller needs.
- **Herman** → builds the first UI shell.
- **Sharon** → builds the real Lead backend.
- **Mark** → keeps the architecture and integration sane.

Then Herman + Sharon connect frontend and backend, Anne tests it as a salesperson, Mark
reviews the integration, and everyone demos the block.

## Team rule

Nobody disappears for a week. Small pieces, small PRs, frequent integration.

## Epic 1 is done when

- Everyone has contributed.
- Everyone's work has been integrated into `main`.
- The first vertical slice works.
- Everyone understands how we want to work.
- We know what to change before Epic 2.
