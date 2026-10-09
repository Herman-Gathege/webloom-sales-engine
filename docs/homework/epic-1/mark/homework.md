# Mark — Epic 1

> **Status: ready, and the frontend half now exists.** `frontend/` is on the
> `feat/epic-1-frontend-shell` branch — Vite + React 19 + TS + Tailwind v4 + shadcn/ui, with
> a Lead List, a Lead Detail, and an API client that falls back to sample data. The shapes
> the two halves must agree on are frozen in
> [`docs/delivery/epic-1-lead-contract.md`](../../../delivery/epic-1-lead-contract.md). The
> backend half — `backend/` and Docker Compose — is still empty, which is the piece nobody
> else is filling.

## Your mission

Make sure the first Lego block is built on solid technical rails.

## What to do

- Review the proposed app structure: the backend and frontend folders, and how they talk.
- Define the minimum boundaries we will reuse — where routes, logic, and data access live.
  Keep it minimal and follow FikaTu's layout.
- Make one small technical implementation that sets a convention everyone copies (for
  example the app skeleton, config, or the health endpoint).
- Review Herman's first frontend structure once it is open.
- Flag only the decisions that would be painful to reverse later.
- Write a short "watch-outs" note.

You are the safety net, not the whole backend. Keep this to about a day.

## Done means

- [ ] One useful technical piece is implemented and merged.
- [ ] The basic architecture is clear enough for the others to follow.
- [ ] Obvious future traps are written down.
- [ ] Herman's work has been reviewed.
- [ ] No abstraction was added that we do not need yet.

## Bring back

- A small PR.
- A short architecture / watch-outs note.
- 2–3 decisions the team should agree on before we continue.
