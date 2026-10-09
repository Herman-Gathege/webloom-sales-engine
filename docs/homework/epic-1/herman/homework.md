# Herman — Epic 1

> **Status: done and merged** (PR #5). The shell is in
> [`frontend/`](../../../../frontend/README.md) and runs with `npm run dev`. The agreed shape
> is written up in
> [`docs/delivery/epic-1-lead-contract.md`](../../../delivery/epic-1-lead-contract.md), and
> Sharon's API now implements it.

## Your mission

Get the first visible product shell working and make sure everyone's work has somewhere
to land.

## What to do

- Stand up the app shell: a React app that starts with one command and can talk to the API.
- Add basic navigation and layout — a header or sidebar with Leads as the first item.
- Build the first Lead List and Lead Detail views with placeholder data. Two screens, not
  thirteen.
- Agree the Lead shape with the backend — the exact fields Sharon's API will return — and
  write it down where everyone can see it.
- Wire the list to that shape so it shows the first real lead the moment the API is up.
- Keep it intentionally simple. Do not try to finish the frontend.

## Done means

- [x] The app starts with one command — `cd frontend && npm run dev`. Needs Node 22; Vite 8
      will not run on Node 21, which is now pinned in `.nvmrc`.
- [x] Navigation exists and moves between the list and a lead.
- [x] Lead List renders — a row per lead, with sector, area, phone, website and status.
- [x] Lead Detail renders, including the lead's activity history.
- [x] The UI can display a Lead in the agreed shape.
- [x] The PR is reviewable, with a caveat: 43 files, but ~4,600 of those lines are
      `package-lock.json` and ~350 are generated shadcn components. The hand-written part is
      ~900 lines across 12 files.

One follow-up he still owes, found by Sharon: `.env.example` set
`VITE_API_BASE_URL=http://localhost:8000`, but the client appends `/leads` to that base, so
following the file literally would miss the `/api/v1` prefix. Fixed on
`docs/epic-1-standings`.

## Bring back

- The working UI — `frontend/`, on the `feat/epic-1-frontend-shell` branch.
- Your pull request.
- The note "what should the backend give me?", written up as the agreed Lead contract.
- The thing worth saying out loud: the shell runs on sample data until the API answers, and
  says so on screen. That is what lets Sharon build in parallel without either side waiting.
