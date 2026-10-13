# Webloom Sales Engine — Epic Plan

**Date:** 2026-10-13 · **Backlog owner:** Herman Gathege · **Reviewed by:** Mark Mwenesi
**Scope:** [scope spec](../superpowers/specs/2026-10-08-webloom-sales-engine-scope.md) ·
**Detail:** [product roadmap](product-roadmap.md) · **Rules:** [how we work](../team/how-we-work.md)

This is the plan we act on. It decides **what we build next, in what order, and who owns each
piece**. The acceptance criteria, task hours, and per-story owner and reviewer live in the
[product roadmap](product-roadmap.md) — this file does not repeat them.

Read this in five minutes. Follow a link only when you need the detail.

**Epic 1 — First Lego Block is closed.** What it shipped and what we learned is in the
[closure record](../homework/epic-1/status.md).

---

## Now

**Nothing is in flight.** Epic 1 is closed and merged. The next block starts when we pick
Epic 2 and write the four homework cards for it.

## Next — Epics 2 to 9

We build in vertical slices, so every epic below ends in something a seller could recognise,
not a layer. "Areas" are roadmap areas; "size" is roadmap story points, where **1 point ≈ half
a focused day**. Size compares epics against each other. It is not a schedule.

| Epic | What it delivers | Areas | Owner | Reviewer | Size |
|---|---|---|---|---|---|
| **2** | The Lead Desk is real: the 52-row list imports with a rejected-rows report, leads are filterable, and CI makes a red test visible | R1.2–R1.4, R4 | Sharon | Mark | ~28 pts |
| **3** | Only we can see the pipeline: login, users, roles | R2 | Mark | Herman | ~8 pts |
| **4** | What we sell is data, not code: offers, message templates, and the pilot copy pack | R3, R5.1, R12.1 | Sharon | Mark | ~11 pts |
| **5** | A campaign produces real personalised drafts, one per eligible lead | R5.2, R5.3, R6.1 | Herman | Mark | ~16 pts |
| **6** | A human approves, and only then does it send — through FikaTu | R1.5, R6.2, R7 | Mark | Sharon | ~39 pts |
| **7** | Replies are captured and classified, and interested leads are handed to a person | R8, R9 | Anne | Sharon | ~29 pts |
| **8** | The funnel is visible: deals, outcomes, and reports that say which sector converts | R1.6, R10, R11 | Herman | Mark | ~31 pts |
| **9** | One real campaign run end to end, then hardened and deployed | R12.2–R12.4, R13 | Mark | Anne | ~32 pts |

### What we demo at the end of each epic

The demo is the point. An epic is not finished until a non-author can run its demo.

- **2 —** import the real 52-row CSV, see the rejected rows explained, filter the list by
  sector, open a lead and read its timeline. Then break a test on purpose and watch CI go red.
- **3 —** log in as each of the four roles; the `viewer` cannot see contact details.
- **4 —** add a FikaTu-platform offer through the UI with no code change; create a template
  that uses a lead field.
- **5 —** create a campaign for "opticians with no website" and get one rendered draft per
  lead; a lead missing a variable is skipped and the reason is listed.
- **6 —** approve a draft, watch it go `approved → queued → sent`, and see delivery status come
  back. Try to send an unapproved draft and get refused.
- **7 —** record a reply, classify it, qualify the lead, hand it to a person — then confirm it
  is excluded from every future automated send.
- **8 —** open the funnel report and read which sector, source, and message variant converts.
- **9 —** run a real campaign of 40+ leads through the whole loop, and produce the
  retrospective that says where to sell next.

## Who carries what

Owning an epic means being accountable for it, sequencing it, and writing the four homework
cards when it starts. It does not mean building every story: each story in the roadmap already
names its own owner and reviewer, and the reviewer is a different person.

| Person | Owns | Main work |
|---|---|---|
| **Sharon** | Epics 2, 4 | Migrations, the CSV importer, backend features end to end |
| **Mark** | Epics 3, 6, 9 | Architecture, auth, the FikaTu send path, deployment |
| **Herman** | Epics 5, 8 | Frontend, product decisions, reports, the backlog |
| **Anne** | Epic 7 | Replies, qualification, handoff, and running the pilot |

Remaining stories by accountable owner, as a load sanity-check: Sharon ~74 pts, Herman ~55,
Mark ~46, Anne ~19. Mark's number is low on purpose — he is the reviewer on the risky paths,
so his capacity is spent reviewing as much as building. Anne's is low because her heaviest
work (the pilot) is scheduled late, not because it is small.

## Order and dependencies

1. **Epic 2 first.** Everything after it needs leads that came from a real spreadsheet, and CI
   before we have more people writing code.
2. **Epic 3 can run alongside Epic 2** — different code, no shared files — but it must land
   before anything is exposed beyond our four machines.
3. **Epics 4 → 5 → 6 are a chain.** Offers and templates, then campaigns and drafts, then
   approval and sending. Nothing meaningful parallelises across these three.
4. **Epic 6 has a prerequisite outside this repository.** FikaTu (R1.5) needs a
   `sales.outreach.send` event type added to `Herman-Gathege/notifications_pipeline_system`,
   because its event registry is hardcoded and an unknown type is rejected. Mark owns that
   change and it must ship before Epic 6's send path starts. This is the one dependency we
   cannot satisfy inside this repo.
5. **Epic 7 needs Epic 6** — there are no replies until something has sent.
6. **Epic 8 needs Epics 5–7** — there is nothing to report until the funnel has data.
7. **Epic 9 last.** It is the pilot plus the hardening that happens before real businesses.

## Later

Deliberately out of the next eight epics. Each needs its own scope decision before anyone
builds it: AI-generated drafts and AI reply classification · WhatsApp Business API inbound
webhooks and automatic reply capture · lead scoring and automatic segment discovery · email
enrichment · multi-tenant support, billing, and quotations · calendar and meeting booking · a
public marketing site for the product · a mobile application.

## Decisions we still owe

Flagged rather than invented. Settle these as a team before the epic they affect.

1. **Where R1.4 (the 13-screen inventory) belongs.** Proposed: Epic 2, because Epic 2 already
   extends the UI. It could equally be an Epic 3 design task. Confirm.
2. **Whether R10.3 (disposition and outcome capture) is Epic 8 or Epic 7.** It produces the
   data Epic 8 reports on, so it may belong at the end of Epic 7.
3. **Whether Epic 9 should split.** A pilot run and a security/hardening pass are different
   kinds of work; if it feels too big, cut it into 9a (pilot) and 9b (harden and deploy).
4. **The pilot channel.** The scope spec leaves it open with SMS as the default, because the
   list is phone-only and FikaTu's WhatsApp provider is not implemented. Anne decides, before
   Epic 6.

## How this plan changes

- Estimates are guidance, not commitments. We re-cut after every epic, and this document is
  the only place the order lives.
- At the end of each epic the team writes down one thing to keep and one thing to change, and
  that note travels into the next epic's homework cards.
- Herman owns this document and the backlog. Changing the order is a team decision, recorded
  here.
