# Sprint 2 — the Lead Desk is real

**Started:** 2026-10-13 · **Owner:** Sharon · **Reviewer:** Mark

## Where we are

Sprint 1 is done and merged. One command starts the whole thing — database, API and UI — and
you can see eight **sample** leads and open one to read its history. That record is in
[the Sprint 1 card](../sprint-1/status.md), and you do not need to read it.

Eight invented businesses are the problem. This sprint puts the **real 52-business list** into
the system and makes the list usable.

## What we are doing

**The real list goes in, and the list gets filters.** Plus CI, so a broken test is visible to
everyone instead of only to whoever ran it.

By the end of the sprint, someone who wrote none of it can import the list, see every rejected
row explained, filter by sector, open a lead and read its timeline — and break a test on
purpose and watch CI go red.

## Who is doing what

| Who | Their piece | Card |
|---|---|---|
| **Sharon** | The importer: the CSV goes in, the rejects come back explained | [sharon](sharon/homework.md) |
| **Mark** | CI: every pull request gets checked automatically | [mark](mark/homework.md) |
| **Herman** | The Lead List gets filters and a search box | [herman](herman/homework.md) |
| **Anne** | The seller's pass: her notes from Sprint 1, her example lead, and reviewing the two PRs | [anne](anne/homework.md) |

Read only your own card. Each one tells you what you need.

## Two things to keep in mind

- **This is a side project.** Every card here is about one normal workday, and nothing is due
  overnight. If yours is turning into two days, say so in the group and we will cut it.
- **Channels, decided:** we send on **SMS through Africa's Talking (FikaTu's sandbox)** and
  **email**. No WhatsApp. Nothing sends this sprint — that starts in Sprint 6.

## The loop

Agree → Build → PR → Review → Merge → Run → Demo → Next sprint

## This sprint is done when

- The real 52-row list is in the database, with rejected rows explained.
- The Lead List filters and searches.
- CI runs on every pull request and blocks on failure.
- Someone who wrote none of it can run the demo above.
