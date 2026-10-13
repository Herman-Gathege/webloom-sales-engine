# Sprint 1 — the first working slice

## Goal

Get one tiny piece of the Sales Engine working together.

## Where this sprint ended

**Closed on 2026-10-13.** All four pieces are in, and one command starts the slice.

- **Herman — done** (PR #5). The frontend shell: Lead List, Lead Detail with activity, and a
  client that runs on sample data until the API answers.
- **Sharon — done** (PR #7). The Lead backend: the two tables, the migration, the idempotent
  seed, the two read endpoints and their tests.
- **Mark — done** (PR #10). One command: PostgreSQL, the API and the UI in Compose, on
  <http://localhost:5174>.
- **Anne — done, verbally.** She walked the screens as a seller and agreed the direction is
  right. Her written notes and example lead are the first story of Sprint 2.

What shipped, what is verified, what we learned, and the one honest gap are in
[status.md](status.md). What comes next is the [sprint plan](../../delivery/sprint-plan.md).

The agreed Lead and Activity shapes live in
[`docs/delivery/sprint-1-lead-contract.md`](../../delivery/sprint-1-lead-contract.md).

## The loop

Agree → Build → PR → Review → Merge → Run → Demo → Next sprint

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
reviews the integration, and everyone demos the sprint.

## Team rule

Nobody disappears for a week. Small pieces, small PRs, frequent integration.

## Sprint 1 is done when

- [x] Everyone has contributed.
- [x] Everyone's work has been integrated.
- [x] The first vertical slice works, from one command.
- [x] Everyone understands how we want to work.
- [x] We wrote down what to change before Sprint 2 — see [status.md](status.md).
