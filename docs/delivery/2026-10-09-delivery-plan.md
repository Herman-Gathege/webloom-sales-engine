# Webloom Sales Engine — Delivery Plan

**Date:** 2026-10-09
**Team:** Mark Mwenesi (lead, architecture/backend), Herman Gathege (product/backlog/frontend),
Sharon Kendi (backend), Anne (sales workflow/product)
**Scope authority:** [scope spec](../superpowers/specs/2026-10-08-webloom-sales-engine-scope.md)
**Full product destination:** [product roadmap](product-roadmap.md)
**Rules of the road:** [how we work](../team/how-we-work.md)

---

## How we deliver

> Build the product like Lego. Build one small working piece. Bring everyone's pieces
> together. Test it. Learn how we worked. Then build the next piece.

Every block goes around the same loop:

```text
Agree → Build → PR → Review → Merge → Run → Demo → Next block
```

- **Vertical slices, not silos.** Nobody disappears for a week to reappear with a layer.
  We agree a tiny end-to-end piece, split it into complementary work, build in parallel
  where we can, and merge fast.
- **`main` is the latest integrated working state.** Short-lived branches, small PRs.
- **A feature is not done until someone else can pull it and run it.**
- **The first version of everything is small.** Extra abstraction is a cost we pay now for
  a guess about later. We don't pay it.
- **We have demanding day jobs.** Blocks are sized to fit normal weeks, not heroic ones.

The point of the first blocks is not how much we complete. It is establishing a way of
working that lets us move fast together for the rest of the MVP.

---

## Now — Epic 1: First Lego Block

**Promise:** from a clean clone, the team can start the Sales Engine, see the application,
load a small set of leads, view them in a list, open a lead, and see basic activity/history.

**The slice:**

```text
seed data → Lead → PostgreSQL → FastAPI → React → Lead List → Lead Detail → Activity/Event
```

**Size:** roughly 5–7 focused days end to end. Each person's individual piece is about one
normal workday. The cards live in [docs/homework/epic-1/](../homework/epic-1/README.md).

### What Epic 1 is really testing

This block is an experiment about the team, not a feature delivery:

- Can all four of us work comfortably in the same codebase?
- Can we divide work without creating silos?
- Can we use Codex/AI without four different architectures emerging?
- Can we review each other's work efficiently?
- Can we integrate continuously?
- Can we produce something demonstrable after each small increment?
- Can we do all of this without the project feeling like a second full-time job?

### The four pieces

| Person | Piece | Brings back |
|---|---|---|
| **Anne** | The seller's view: what a good lead looks like, and what must be on the List and Detail screens | Short notes, an example lead, feedback on the first UI |
| **Herman** | The frontend shell: navigation, layout, Lead List and Lead Detail views, and the API contract | A small PR, working UI, and "what should the backend give me?" |
| **Sharon** | The real Lead backend: model, migration, seed data, API, tiny activity/history, tests | A PR, the endpoint, an example response, and what Herman needs to connect |
| **Mark** | The rails: smallest backend skeleton that runs, the folder convention, and review of Herman's structure | A small PR, a short watch-outs note, and 2–3 decisions to agree |

Then Herman + Sharon connect frontend to backend, Anne tests it as a salesperson, Mark
reviews the integration, and everyone demos the working block.

### Not in Epic 1

Deliberately out, even though the roadmap lists them: the real 52-row CSV importer,
authentication and roles, campaigns, drafts, the approval queue, FikaTu delivery, replies,
pipeline, reports, and the other eleven screens. Epic 1 has two screens, not thirteen.

FikaTu must not block the first slice. If a seam is needed, a small fake adapter is enough
for now — the real integration is a later block with its own research note.

**One flagged exception.** `AGENTS.md` says contact details are role-gated. Epic 1 has no
auth, so that rule cannot hold yet. It is safe only because Epic 1 runs locally, for the
four of us, and is not deployed or reachable by anyone else. The rule starts applying in
the block that adds login. If we ever expose an Epic 1 build beyond our four machines, this
exception is void.

### Epic 1 is done when

- [ ] Everyone has contributed to the same working slice.
- [ ] Everyone's work has been integrated into `main`.
- [ ] Someone other than the author can clone, start the app, and see the demo flow below.
- [ ] Lead List and Lead Detail render real data from the API, with activity/history.
- [ ] Everyone understands how we want to work, and we have written down what to change
      before the next block.

```text
Start app
  ↓
Load/import sample leads
  ↓
See Lead List
  ↓
Open a Lead
  ↓
See Lead details
  ↓
See basic activity/history
```

### Risks we already know about

| Risk | What we do about it |
|---|---|
| Mark's "smallest backend that runs" is the piece most likely to exceed a workday | Cut scope to skeleton + `/health` + compose, or pair with Herman. Do not build models, auth, or the full layering. |
| Frontend and backend drift apart on the Lead shape | The contract is agreed before either side finishes; Sharon's example response is the source of truth. |
| The activity/history is the smallest interesting part and is easy to skip | It is in Sharon's card, and it is the last row of the demo flow. |
| Real lead data leaks into the repo | Epic 1 seeds a synthetic fixture only. `data/` is gitignored and the real list stays there. |
| There is no CI yet, so a red test is only visible to whoever ran it | Accepted for one block. CI is the first thing after Epic 1. |

---

## Next — the blocks after this one

The full destination is in the [product roadmap](product-roadmap.md). The order below is
the current best guess, not a commitment. We re-cut it after every block.

| Block | Outcome | Roadmap area | Rough size |
|---|---|---|---|
| 2 | A red test is visible to everyone: CI on every PR, plus tests around the slice | R1, R4 | 2–3 days |
| 3 | The real 52-row list imports, with rejected rows reported and explained | R4 | 1–2 weeks |
| 4 | Only we can see the pipeline: login, users, roles | R2 | 1–2 weeks |
| 5 | Offers and message templates live as data, not code | R3, R5 | 1–2 weeks |
| 6 | A campaign produces real personalised drafts per lead | R5, R6 | 1–2 weeks |
| 7 | A human reviews, edits, and approves every draft before anything sends | R6 | ~1 week |

Each block ends with the same loop and a demo that a non-author can run. Work that does not
finish returns to the backlog deliberately; it does not silently roll forward.

---

## Later

Beyond the MVP. Each of these needs its own scope decision before anyone builds it:

- AI-generated message drafts and AI reply classification.
- WhatsApp Business API inbound webhooks and automatic reply capture.
- Lead scoring and automatic segment discovery.
- Email enrichment to add addresses to the phone-only list.
- Multi-tenant support, billing, and quotation generation.
- Calendar integration and meeting booking.
- A public marketing site for the product; a mobile application.

---

## Where each document fits

| Document | Role |
|---|---|
| [Scope spec](../superpowers/specs/2026-10-08-webloom-sales-engine-scope.md) | What we are building and what is out of scope. The gate. |
| **This plan** | What we are building now, and the next few blocks. |
| [Product roadmap](product-roadmap.md) | The full destination and the long-term epics. Not a commitment. |
| [Homework cards](../homework/epic-1/README.md) | The current block, split into four pieces a person can start tonight. |
| [How we work](../team/how-we-work.md) | Branching, PRs, review, what "done" means, how we disagree. |
| [Research notes](../research/) | What we verified about the lead list and FikaTu. |

## Keeping this honest

- Estimates are guidance, not commitments. We re-cut after every block.
- Herman owns this document and the backlog; Mark owns architecture; Anne owns the sales
  workflow; Sharon owns the backend features she builds.
- When a block ends, the team writes down one thing to keep and one thing to change before
  starting the next one. That note travels with the next block's homework.
