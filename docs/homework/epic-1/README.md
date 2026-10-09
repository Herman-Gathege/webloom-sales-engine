# Epic 1 — First Lego Block

## Goal

Get one tiny piece of the Sales Engine working together.

## Where we are right now

- **Herman — done.** The frontend shell is in [`frontend/`](../../../frontend/README.md):
  Lead List, Lead Detail with activity, and a client that runs on sample data until the API
  answers. Branch `feat/epic-1-frontend-shell`.
- **Sharon — next.** The Lead model, migration, seed data, API and tests. The exact shapes
  are already agreed, so she can start without waiting on anyone.
- **Mark — open.** The backend rails and Docker Compose, plus a review of the frontend
  structure. `backend/` does not exist yet.
- **Anne — can start now.** The two screens exist to click through and give feedback on.

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
