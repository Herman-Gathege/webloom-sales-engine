# Webloom Sales Engine — Sprint Plan

**Updated:** 2026-11-02 · **Owner:** Herman Gathege · **Reviewed by:** Mark Mwenesi
**Scope:** [scope spec](../superpowers/specs/2026-10-08-webloom-sales-engine-scope.md) ·
**Detail:** [sprint detail](sprint-detail.md) · **Rules:** [how we work](../team/how-we-work.md)

This is the plan we act on. One sprint at a time. Read it in three minutes: what we build
next, in what order, and who owns each sprint.

We build like Lego. Each sprint is one small working piece — build it, bring everyone's
pieces together, run it, demo it, then start the next one. **A sprint is not finished until
someone other than the author can run its demo.**

Sizes below compare sprints to each other; they are not a promise of one week. Sprint 1 fitted
into about one normal workday each. **Sprint 2 is more like two or three per person, and
Sprints 6 to 9 are bigger again** — so when we get to those we cut them into smaller pieces
before we start, rather than after.

## Where we are

**Sprint 1 is done.** Seed data → Lead → PostgreSQL → FastAPI → React → Lead List → Lead
Detail → activity/history — and one command starts all of it. Shipped 2026-10-13 by all four
of us; the record is in [the Sprint 1 closure](../homework/sprint-1/status.md).

**Sprint 2 is closed** — the lead desk is real, and the exit review is in
[`docs/homework/sprint-2/status.md`](../homework/sprint-2/status.md).

**Sprint 3 is complete: lock the door**, owned by Mark. The scope and acceptance criteria are
in [`sprint-3-auth.md`](sprint-3-auth.md); the closeout evidence is in
[`docs/homework/sprint-3/status.md`](../homework/sprint-3/status.md). The review homework is in
[`docs/homework/sprint-3/`](../homework/sprint-3/README.md).

**Sprint 4 is in contract review.** Offers and templates are proposed in
[`sprint-4-offers-templates.md`](sprint-4-offers-templates.md). No implementation starts
until the five review decisions are accepted or corrected and the homework cards exist.

One thing we carry forward: Sprint 1 cost more in setup friction than in product. **From now
on, the first task of a sprint is "a new person can run it", not the last.**

---

## Sprint 2 — The Lead Desk is real ✅ closed

The real 52-row lead list goes in, instead of eight invented samples. Leads become
filterable. And CI lands, so a red test is visible to everyone instead of only to whoever
ran it.

**At the end you can:** import the real list, see the rejected rows explained, filter by
sector, open a lead and read its timeline — then break a test on purpose and watch CI go red.

**Owner:** Sharon · **Reviewer:** Mark

| Who | Their piece |
|---|---|
| Sharon | The importer: upload the CSV, validate every row, save the good ones, and report the rejects — one reason each. |
| Mark | CI: one workflow that runs the backend tests and the frontend lint, build and tests on every pull request. |
| Herman | Filters on the Lead List: sector, area, website status, and a search box. |
| Anne | The seller's pass on the Lead Desk — the notes, screen lists and example lead carried over from Sprint 1 — plus the words a rejected row shows. |

Anne's written seller review is the first story of this sprint, not a loose end. Cards:
[sharon](../homework/sprint-2/sharon/homework.md) ·
[mark](../homework/sprint-2/mark/homework.md) ·
[herman](../homework/sprint-2/herman/homework.md) ·
[anne](../homework/sprint-2/anne/homework.md).

FikaTu is not involved yet, and nothing here depends on another repository.

---

## Sprints 4 to 9

Each is one small piece. **1 point ≈ half a focused day**, and the sizes compare sprints to
each other — they are not a schedule.

**Sprint 4 — What we sell, in the system.** Offers (website packages first, other services
later) and message templates with variants — all editable without a code change.
[Implemented and awaiting manual acceptance](sprint-4-offers-templates.md). *Owner: Sharon ·
Reviewer: Mark · ~11 pts.*

**Sprint 5 — Campaigns and drafts.** A campaign is a batch of leads, one offer, one template.
It produces one personalised draft per eligible lead and skips the ones it cannot fill.
*Owner: Herman · Reviewer: Mark · ~16 pts.*

**Sprint 6 — Approve, then send.** A human review queue, then delivery through FikaTu.
Nothing sends without approval. Channels for now: **SMS through Africa's Talking (sandbox)**
and **email**. *Owner: Mark · Reviewer: Sharon · ~39 pts.*

**Sprint 7 — Replies and handoff.** Replies are captured and classified, interested leads
are qualified, and the moment a lead shows interest automation stops and a person takes over.
*Owner: Anne · Reviewer: Sharon · ~29 pts.*

**Sprint 8 — The funnel, visible.** Deals, outcomes, and reports that say which sector, which
source and which message actually converts. *Owner: Herman · Reviewer: Mark · ~31 pts.*

**Sprint 9 — Pilot and harden.** One real campaign run end to end, then security review,
deployment and backups. *Owner: Mark · Reviewer: Anne · ~32 pts.*

## Who leads what

Every sprint has one owner and one reviewer. The owner is accountable for the sprint's demo
and hand-off, not for writing every line. Sprint 1 was shared by all four.

| Person | Leads | Also carries |
|---|---|---|
| **Mark** | Sprint 6 (approve + send), Sprint 9 (pilot + harden); closed Sprint 3 | Architecture, schema, the FikaTu seam, security review |
| **Sharon** | Sprint 4 (offers + templates); closed Sprint 2 | Backend features end-to-end, migrations, tests |
| **Herman** | Sprint 5 (campaigns + drafts), Sprint 8 (funnel + reports) | Product, backlog, frontend, documentation |
| **Anne** | Sprint 7 (replies + handoff) | Sales workflow, copy, compliance wording, the pilot |

This spreads ownership deliberately: nobody leads two sprints in a row, and Mark reviews
rather than absorbs the work he would otherwise be expected to carry.

## Order, and what blocks what

- **Sprints 1–3 are closed.** They established the working slice, the real Lead Desk and CI,
  authentication, and the compliance gate. Everything below assumes them.
- **Sprints 4 → 5 → 6 are a chain.** Offers and templates, then campaigns and drafts, then
  approval and sending. They do not parallelise.
- **Sprint 6 needs one change outside this repository.** FikaTu's event registry is
  hardcoded, so a `sales.outreach.send` event type has to be added to
  `Herman-Gathege/notifications_pipeline_system` before the send path starts. Mark owns it.
  This is the only dependency we cannot satisfy here.
- **Sprint 7 needs Sprint 6** — there are no replies until something has sent.
- **Sprint 8 needs Sprints 5–7** — there is nothing to report until the funnel has data.
- **Sprint 9 is last.** It is the pilot.

## Channels — decided

We send on **SMS (Africa's Talking, sandbox)** and **email**. No WhatsApp for now: FikaTu's
WhatsApp provider is not implemented, and the lead list is phone-only. Revisit after the
pilot.

## Later — decided not to build yet

AI-written drafts and AI reply classification · WhatsApp inbound · lead scoring and automatic
segments · email enrichment · billing, quotations and multi-tenant · meeting booking · a
public marketing site for the product · a mobile app. Each needs its own scope decision
before anyone builds it.

## Decisions we still owe

Flagged, not invented. Settle each before the sprint it affects.

1. Where does the 13-screen inventory land now? Both Sprint 2 and Sprint 3 closed without it.
   It should be settled before Sprint 5 builds campaigns against the Lead Desk.
2. Is outcome capture the end of Sprint 7 or the start of Sprint 8? It produces the data
   Sprint 8 reports on.
3. Does Sprint 9 split into "run the pilot" and "harden and deploy"?

## How this plan changes

- Estimates guide, they do not commit. We re-cut after every sprint, and this file is the
  only place the order lives.
- At the end of every sprint we write down one thing to keep and one to change, and that note
  travels into the next sprint's homework.
- Herman owns this file and the backlog. Changing the order is a team decision, recorded here.
