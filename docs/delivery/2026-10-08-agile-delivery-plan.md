# Webloom Sales Engine — Agile Delivery Plan

**Date:** 2026-10-08
**Scope authority:** `docs/superpowers/specs/2026-10-08-webloom-sales-engine-scope.md`
**Supporting input:** `docs/research/2026-10-08-lead-list-audit.md`, `docs/research/2026-10-08-fikatu-integration-notes.md`
**Team:** Mark Mwenesi (lead), Herman Gathege (PM), Anne (sales), Sharon Kendi (backend)

**Goal:** deliver the MVP sales loop end to end — import leads, build a campaign, generate
personalised drafts, approve them, send through FikaTu, record replies, qualify, hand over
to a human, and record the outcome — then run it on a real lead list.

---

## 1. How this plan works

- **Sprints are 2 weeks**, except Sprint 0, which is 1 week.
- **1 story point ≈ 4 focused hours.** Estimates are relative effort, not calendar time.
- **Capacity assumption:** everyone works part-time alongside other commitments. Nominal
  capacity is 5 days × 4 focused hours = 20h per sprint-week. We commit to about **70%**
  of nominal so that reviews, interruptions and life do not blow up the sprint.
- **Committed capacity per 2-week sprint:** ~28h per person → ~7 points per person → **30
  points per sprint team-wide** (rounded).
- **Sprint 0 committed capacity:** ~18 points team-wide.
- These numbers are a starting hypothesis. After Sprint 1 the team writes down its **actual**
  velocity and this plan is re-cut against reality. An assumption we correct is worth more
  than a schedule we pretend to hit.

## 2. Working agreements

### 2.1 Definition of Ready (a story can enter a sprint only if)

1. It has a clear user-visible outcome and testable acceptance criteria.
2. Its dependencies are already done, or explicitly satisfied by another story in the same sprint.
3. It is estimated by at least two people.
4. It fits within one sprint, and ideally within three days.
5. For anything touching auth, sending, schema, or personal data, Mark has seen the approach.

### 2.2 Definition of Done (a story is done only when)

1. Acceptance criteria are demonstrably met in a demo, not asserted in a chat message.
2. Tests exist and pass: unit tests for logic, plus a test for the failure path of anything
   that sends, imports, or transitions state.
3. Code is reviewed and approved by the named reviewer.
4. It runs in Docker locally from a clean clone.
5. Migrations are committed and reversible.
6. Documentation is updated when behaviour or setup changed.
7. No real lead data, secret, or credential is in the diff.

### 2.3 Git and PR rules

- Branches: `feat/<short-name>`, `fix/<short-name>`, `chore/<short-name>`.
- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- Every change lands through a pull request. No direct pushes to `main`.
- One approval required. Mark must approve anything touching auth, the send path, the
  database schema, or the FikaTu integration.
- A PR that changes a decision that is expensive to reverse also adds an ADR in
  `docs/decisions/`.

### 2.4 Ceremonies and timeboxes

| Ceremony | When | Timebox | Output |
|---|---|---|---|
| Daily standup | Every working day, morning | 15 min | Yesterday / today / blockers |
| Sprint planning | Day 1 of the sprint | 90 min | Sprint goal, committed stories |
| Backlog refinement | Mid-sprint, once | 45 min | Next sprint's stories at Definition of Ready |
| Sprint review / demo | Last day of the sprint | 45 min | Working software demoed to the whole team |
| Retrospective | After the review | 45 min | One thing to keep, one to change |
| Tech huddle (optional) | Weekly | 30 min | Mark unblocks technical questions |

### 2.5 Blocked-work protocol

- A blocker is raised at standup the moment it is known, not at sprint end.
- "Blocked" means: a named person must do something the blocker-owner cannot do alone.
  "I have not started" is not a blocker.
- If a story is blocked for more than 2 working days, the owner and Mark either narrow the
  story, swap it for another sprint item, or pair for an hour.
- Unfinished work returns to the backlog at sprint end. It does not silently roll into the
  next sprint; if it is still the top priority, it is re-committed deliberately.

---

## 3. Epics

| ID | Epic | Scope spec reference | Primary owner |
|---|---|---|---|
| E1 | Foundations, environments, and alignment | §6.2, §6.3, §8 | Mark |
| E2 | Identity, users, and roles | §3, §4.1 (1) | Mark |
| E3 | Offer catalogue | §4.1 (2), §5 | Sharon |
| E4 | Lead Desk | §4.1 (3, 4), §9 (5) | Sharon |
| E5 | Templates, segments, and campaigns | §4.1 (5, 6) | Sharon |
| E6 | Draft generation and approval queue | §4.1 (7, 8), §9 (2) | Herman |
| E7 | Delivery through FikaTu | §4.1 (9), §6.8, §9 (1, 3, 7) | Mark |
| E8 | Replies and qualification | §4.1 (10, 12) | Herman |
| E9 | Handoff and follow-up cadence | §4.1 (11, 14) | Sharon |
| E10 | Pipeline and deals | §4.1 (13) | Sharon |
| E11 | Reporting and funnel metrics | §4.1 (15, 16), §7 | Herman |
| E12 | Pilot campaign operations | §7, §11 | Anne |
| E13 | Hardening, deployment, and onboarding | §6.6, §6.7, §9 | Mark |

---

## 4. Stories

Every story lists acceptance criteria (AC), an owner, a reviewer, and its sprint. Story
points map to the task hour totals that follow each story.

### Epic E1 — Foundations, environments, and alignment

#### E1-S1 — Repository scaffold and one-command local environment
*Sprint 0 · 5 pts · Owner: Mark · Reviewer: Herman*
As a developer, I want one command that brings up the whole stack, so nobody loses a day to setup.

- [ ] `docker compose up --build` starts api, worker, postgres, redis, and frontend from a clean clone
- [ ] `GET /health` returns 200 and reports database and redis status
- [ ] Swagger is reachable at `/docs`
- [ ] `.env.example` lists every variable; no secret is committed
- [ ] The README instructions actually work when followed literally

Tasks: backend Dockerfile and entrypoint (Mark, 5h) · compose file with six services (Mark, 5h) ·
health endpoint (Sharon, 3h) · env template and setup docs (Herman, 3h) · frontend Vite scaffold
wired to the API (Herman, 4h). **Total 20h.**

#### E1-S2 — Continuous integration
*Sprint 0 · 3 pts · Owner: Sharon · Reviewer: Mark*
As a team, we want every PR checked automatically, so broken code cannot merge.

- [ ] CI runs on every PR: backend lint, backend tests, frontend lint, frontend build
- [ ] A deliberately failing test fails the build
- [ ] CI status is required before merge

Tasks: workflow file (Sharon, 4h) · backend lint and test job (Sharon, 3h) · frontend lint and
build job (Herman, 3h) · branch protection settings (Mark, 2h). **Total 12h.**

#### E1-S3 — Database schema design review and migration skeleton
*Sprint 0 · 3 pts · Owner: Mark · Reviewer: Sharon*
As a team, we want the Sprint 1 schema agreed before code, so we do not rewrite migrations twice.

- [ ] An ERD covering users, offers, leads, campaigns, outreaches, replies, deals, activity events
- [ ] The two invariants from scope §6.4 are represented in the design
- [ ] Alembic is configured and `alembic upgrade head` runs on a clean database
- [ ] Decisions on normalisation and indexing are written down

Tasks: ERD and design notes (Mark, 6h) · Alembic configuration (Sharon, 4h) · review session with
all four (Herman, 2h). **Total 12h.**

#### E1-S4 — Screen inventory and wireframes signed off
*Sprint 0 · 3 pts · Owner: Herman · Reviewer: Anne*
As a team, we want the 13 screens sketched and agreed, so builds match a shared picture.

- [ ] All 13 surfaces from scope §6.5 have a sketch or clear description
- [ ] The approval queue and handoff flows are drawn in detail (they carry the most risk)
- [ ] Anne has confirmed the screens match how she actually sells
- [ ] Sign-off recorded in this repo

Tasks: wireframes (Herman, 8h) · sales workflow review session (Anne, 4h). **Total 12h.**

#### E1-S5 — Register the Sales Engine as a FikaTu application
*Sprint 0 · 2 pts · Owner: Mark · Reviewer: Herman*
As a team, we want real credentials and a verified publish path, so Sprint 3 is not blocked.

- [ ] An application is registered in FikaTu and its key and secret are stored locally, not in git
- [ ] A test event is published successfully to a safe recipient
- [ ] The result is documented in the integration research note

Tasks: registration and local secret handling (Mark, 4h) · publish smoke test and write-up
(Mark, 4h). **Total 8h.**

#### E1-S6 — Agreed funnel metric definitions
*Sprint 0 · 2 pts · Owner: Anne · Reviewer: Herman*
As a team, we want one agreed definition per metric, so reports mean the same thing to everyone.

- [ ] Every metric in scope §7 has a one-sentence definition and a formula
- [ ] Reply rate and positive-reply rate are unambiguous, including what counts as a reply
- [ ] Each metric has an owner and the screen where it appears

Tasks: definitions document (Anne, 6h) · review with the team (Herman, 2h). **Total 8h.**

### Epic E2 — Identity, users, and roles

#### E2-S1 — Authentication and login
*Sprint 1 · 5 pts · Owner: Mark · Reviewer: Herman*
As a team member, I want to log in securely, so only we can see our pipeline.

- [ ] Login with email and password returns a JWT; wrong credentials return 401
- [ ] Passwords are stored with bcrypt; no plaintext or reversible hash anywhere
- [ ] Protected endpoints reject missing, malformed, and expired tokens
- [ ] Token expiry and refresh behaviour are documented
- [ ] Lockout or delay after repeated failed attempts

Tasks: user model and password hashing (Mark, 6h) · login endpoint and JWT issue/verify (Mark, 6h) ·
auth middleware and dependency (Mark, 4h) · auth tests including failure paths (Sharon, 4h).
**Total 20h.**

#### E2-S2 — User management and role enforcement
*Sprint 1 · 3 pts · Owner: Sharon · Reviewer: Mark*
As an owner, I want to manage users and roles, so access matches responsibility.

- [ ] Owners can create, deactivate, and re-role users
- [ ] `owner`, `sales`, `engineer`, `viewer` are enforced on the API, not only hidden in the UI
- [ ] A `viewer` cannot read contact details; a `sales` user can
- [ ] Attempts to exceed a role are covered by tests

Tasks: user CRUD endpoints (Sharon, 6h) · role guard dependency (Sharon, 3h) · role tests (Sharon,
3h). **Total 12h.**

### Epic E3 — Offer catalogue

#### E3-S1 — Offer catalogue with seeded website packages
*Sprint 1 · 3 pts · Owner: Sharon · Reviewer: Mark*
As a seller, I want the things we sell stored as data, so we can add non-website offers without code.

- [ ] Offers can be created, edited, deactivated; fields: name, slug, description, price range, currency, pitch angle
- [ ] Starter, Business, and Custom website offers are seeded
- [ ] A FikaTu notification platform offer can be added through the UI with no code change
- [ ] Inactive offers cannot be selected in a campaign

Tasks: offer model and migration (Sharon, 4h) · CRUD endpoints and schemas (Sharon, 5h) · seed
data (Herman, 3h). **Total 12h.**

### Epic E4 — Lead Desk

#### E4-S1 — Lead schema and first migration
*Sprint 1 · 5 pts · Owner: Mark · Reviewer: Sharon*
As a team, we want leads stored in a structure we can report on, so the list is an asset not a spreadsheet.

- [ ] Fields include source, source_url, consent_basis, reviews_count, has_website, social_presence, status, owner
- [ ] Phone is stored normalised (E.164) with the original string preserved
- [ ] De-duplication is enforced on normalised phone at the database level
- [ ] Status is derived from evidence, with manual overrides recorded as activity events
- [ ] Migration is reversible

Tasks: model and migration (Mark, 8h) · status derivation service plus tests (Mark, 6h) · migration
review and backfill script (Sharon, 6h). **Total 20h.**

#### E4-S2 — CSV import with mapping, validation, and an error report
*Sprint 1 · 8 pts · Owner: Sharon · Reviewer: Mark*
As Anne, I want to import a researched lead list and see exactly what was rejected and why, so bad rows never silently disappear.

- [ ] Import accepts the current list's 16 columns without manual editing
- [ ] Free-text `Sector` and `Website status` are mapped into structured fields; unmapped values are reported
- [ ] Duplicate phones are detected and reported, not duplicated
- [ ] Landline-only leads are flagged as call-only and excluded from WhatsApp/SMS eligibility
- [ ] A downloadable error report lists every rejected row with a reason
- [ ] Good rows import even when some rows are rejected
- [ ] The 52-row list imports with a recorded summary of accepted and rejected counts

Tasks: import endpoint and parser (Sharon, 12h) · sector and website-status mapping with tests
(Sharon, 8h) · error report generation (Sharon, 4h) · import UI with progress and report download
(Herman, 8h). **Total 32h.**

#### E4-S3 — Leads list with filters, search, and lead detail timeline
*Sprint 1 · 6 pts · Owner: Herman · Reviewer: Mark*
As Anne, I want to filter leads by sector, area, website status, and owner, and open one to see its full history.

- [ ] List API supports filters, search, and pagination returning under 500ms on 5,000 leads
- [ ] UI filters by sector, area, website status, status, and owner
- [ ] Lead detail shows contact points, source, consent basis, and notes
- [ ] Every change to a lead appears in a timestamped timeline with the actor's name
- [ ] Contact details are hidden from roles that may not see them

Tasks: list and detail endpoints with filters (Sharon, 8h) · leads table UI (Herman, 8h) · lead detail
and timeline UI (Herman, 6h) · activity log write path (Sharon, 4h) · role-based field visibility tests
(Sharon, 4h). **Total 30h.**

### Epic E5 — Templates, segments, and campaigns

#### E5-S1 — Message templates with variants
*Sprint 2 · 5 pts · Owner: Sharon · Reviewer: Mark*
As Anne, I want reusable templates per offer and channel with variants, so I can test copy without code.

- [ ] Templates belong to an offer and a channel and carry a variant label (for example `A`, `B`)
- [ ] Variables are declared and validated against the lead fields they reference
- [ ] A template with an unknown variable is rejected with a clear message
- [ ] The five-line pattern from the existing lead list is stored as the seed template

Tasks: template model and migration (Sharon, 5h) · CRUD endpoints and variable validation (Sharon,
8h) · template editor UI (Herman, 5h) · seed templates from the lead list (Anne, 2h). **Total 20h.**

#### E5-S2 — Campaign creation
*Sprint 2 · 5 pts · Owner: Mark · Reviewer: Sharon*
As Anne, I want to create a campaign from an offer, a segment, a template, and a cadence, so a batch of outreach is a deliberate act.

- [ ] A campaign requires an offer, a channel, a template, an owner, and a goal
- [ ] Leads are attached by segment or by explicit selection, with a preview count before saving
- [ ] A campaign cannot include leads that have opted out
- [ ] Campaign status moves through `draft`, `active`, `paused`, `completed`

Tasks: campaign model and migration (Sharon, 6h) · create and preview endpoints (Mark, 8h) · campaign
creation UI (Herman, 6h). **Total 20h.**

#### E5-S3 — Saved segments
*Sprint 3 · 3 pts · Owner: Herman · Reviewer: Sharon*
As Anne, I want to save a filter as a named segment, so I can reuse "opticians with no website" without retyping it.

- [ ] A segment stores a named filter definition
- [ ] Segments can be previewed with a live count
- [ ] Segments can be used as a campaign source

Tasks: segment model and endpoints (Sharon, 5h) · segment builder UI (Herman, 5h) · tests (Sharon, 2h).
**Total 12h.**

### Epic E6 — Draft generation and approval queue

#### E6-S1 — Personalised draft generation
*Sprint 2 · 8 pts · Owner: Sharon · Reviewer: Mark*
As Anne, I want a personalised draft per lead generated from the template, so I review messages instead of writing them.

- [ ] Generating drafts for a campaign produces exactly one draft per eligible lead
- [ ] Rendered text matches the seed message for the seed leads, byte for byte
- [ ] Leads missing a required variable are skipped and listed with the reason
- [ ] Opted-out and call-only leads are excluded according to channel rules
- [ ] Generation is idempotent: running it twice does not duplicate drafts

Tasks: rendering service with tests (Sharon, 12h) · eligibility rules (Sharon, 6h) · generation job and
endpoint (Sharon, 8h) · generation UI with progress and skip report (Herman, 6h). **Total 32h.**

#### E6-S2 — Approval queue
*Sprint 2 · 8 pts · Owner: Herman · Reviewer: Mark*
As Anne, I want to review, edit, approve, or reject each draft before it sends, so nothing goes out without a human deciding.

- [ ] Drafts are visible with lead context (business, sector, area, source, review count)
- [ ] A draft can be edited inline; edits are stored on the outreach, not the template
- [ ] Approve, reject, and bulk approve work; each records the actor and timestamp
- [ ] `draft` cannot move directly to `sent`; the API rejects an attempt
- [ ] Rejected drafts require a reason chosen from a list
- [ ] The queue loads 100 drafts without noticeable lag

Tasks: approve/reject/edit endpoints and state guard (Sharon, 10h) · approval queue UI with bulk actions
(Herman, 14h) · state machine tests including the forbidden transition (Sharon, 4h) · rejection reason
list (Anne, 4h). **Total 32h.**

### Epic E7 — Delivery through FikaTu

#### E7-S1 — FikaTu client module
*Sprint 3 · 8 pts · Owner: Mark · Reviewer: Sharon*
As a developer, I want one module that speaks to FikaTu, so no other code knows it exists.

- [ ] The client handles token acquisition, caching, and refresh
- [ ] One method publishes an outreach message and returns a delivery reference
- [ ] Network failures, timeouts, 4xx, and 5xx are distinguished and surfaced with the provider's message
- [ ] The client is tested against a fake HTTP layer, with no live calls in the test suite
- [ ] A single live smoke test runs only when an env flag is set

Tasks: client module with tests (Mark, 16h) · configuration and secret loading (Mark, 6h) · fake-server
test harness (Sharon, 6h) · live smoke test guarded by env flag (Sharon, 4h). **Total 32h.**

#### E7-S2 — Outreach state machine
*Sprint 3 · 5 pts · Owner: Mark · Reviewer: Sharon*
As a team, we want outreach to move through explicit states, so a bug cannot send something it should not.

- [ ] States: `draft`, `approved`, `queued`, `sent`, `delivered`, `failed`, `cancelled`
- [ ] Only `approved` may be queued; only `queued` may be sent
- [ ] Every transition records actor, timestamp, and reason
- [ ] Illegal transitions raise a typed error and are covered by tests
- [ ] The state machine is the only writer of `sent_at` and `delivery_status`

Tasks: state machine implementation (Mark, 8h) · transition tests including illegal paths (Sharon, 8h) ·
activity event recording (Sharon, 4h). **Total 20h.**

#### E7-S3 — Send worker with idempotency
*Sprint 3 · 8 pts · Owner: Sharon · Reviewer: Mark*
As Anne, I want approved messages sent exactly once, so a retry never double-messages a business.

- [ ] A Celery task sends queued outreaches in batches with pacing
- [ ] The FikaTu reference is persisted before any retry is possible
- [ ] Re-running the task never sends the same outreach twice
- [ ] Terminal failures move the outreach to `failed` with a reason
- [ ] A kill-and-restart mid-batch sends no duplicates

Tasks: send task and batching (Sharon, 12h) · idempotency key and persistence (Sharon, 8h) · retry and
failure handling (Mark, 8h) · crash-and-resume test (Sharon, 4h). **Total 32h.**

#### E7-S4 — Delivery status sync and outreach log
*Sprint 3 · 5 pts · Owner: Herman · Reviewer: Mark*
As Anne, I want to see what was delivered, so a silence is never mistaken for success.

- [ ] A scheduled task polls FikaTu for status updates and updates outreach records
- [ ] Unknown status is displayed as unknown, never as delivered
- [ ] The outreach log filters by campaign, state, channel, and date
- [ ] Failures show the failure reason and allow one retry

Tasks: status sync task (Sharon, 8h) · outreach log API (Sharon, 4h) · outreach log UI with filters
(Herman, 8h). **Total 20h.**

#### E7-S5 — Channel eligibility, pacing, and opt-out guard at send time
*Sprint 3 · 3 pts · Owner: Sharon · Reviewer: Mark*
As a team, we want the guardrails enforced at send time, so a stale campaign cannot break a platform rule.

- [ ] Send-time checks reject opted-out leads, call-only leads on WhatsApp/SMS, and leads without a valid number
- [ ] Sends are paced per channel so a batch cannot burst
- [ ] A guardrail rejection is recorded as an activity event with the reason
- [ ] Each guardrail has a test that proves it blocks

Tasks: guardrail service and tests (Sharon, 8h) · pacing configuration (Mark, 4h). **Total 12h.**

### Epic E8 — Replies and qualification

#### E8-S1 — Reply capture
*Sprint 4 · 5 pts · Owner: Herman · Reviewer: Sharon*
As Anne, I want to record a reply against the message that caused it, so the funnel reflects reality.

- [ ] A reply is recorded against an outreach and its lead
- [ ] Reply text, channel, and timestamp are stored
- [ ] A reply can be classified positive, negative, neutral, or opt-out
- [ ] An opt-out reply immediately makes the lead terminal and blocks all future sends
- [ ] Recording a reply updates the lead's derived status

Tasks: reply model and endpoints (Sharon, 8h) · reply capture UI (Herman, 8h) · opt-out propagation tests
(Sharon, 4h). **Total 20h.**

#### E8-S2 — Funnel transition rules
*Sprint 4 · 5 pts · Owner: Sharon · Reviewer: Mark*
As a team, we want derived lead status, so nobody maintains a status field by hand.

- [ ] Positive reply moves the lead to `replied` and flags it for handoff
- [ ] Negative reply moves the lead to `not_interested` and stops its cadence
- [ ] Opt-out moves the lead to `opted_out`, which is terminal
- [ ] Cadence exhaustion moves the lead to `no_response`
- [ ] Every derived transition has a test

Tasks: transition rules service (Sharon, 12h) · rule tests (Sharon, 6h) · manual override with recorded
reason (Herman, 2h). **Total 20h.**

#### E8-S3 — Qualification capture
*Sprint 4 · 3 pts · Owner: Herman · Reviewer: Sharon*
As Anne, I want one form to record what a conversation revealed, so knowledge survives the conversation.

- [ ] Fields: need, budget signal, timeline, decision maker, next step, free notes
- [ ] Qualification is attached to the lead and time-stamped with who captured it
- [ ] A lead cannot be marked qualified without need and next step
- [ ] The most recent qualification is visible on the lead and on pipeline cards

Tasks: qualification model and endpoints (Sharon, 5h) · qualification form UI (Herman, 6h) · validation
tests (Sharon, 1h). **Total 12h.**

### Epic E9 — Handoff and follow-up cadence

#### E9-S1 — Handoff to a human
*Sprint 4 · 5 pts · Owner: Herman · Reviewer: Mark*
As Anne, I want an interested lead handed to me and removed from automation, so a real conversation is never interrupted by a bot.

- [ ] A handoff assigns the lead to a user and records reason and timestamp
- [ ] After handoff, the lead is excluded from all automated sends in every campaign
- [ ] Handed-off leads appear in a "my conversations" queue for the assignee
- [ ] A handoff sends a notification to the assignee through FikaTu
- [ ] Attempting to include a handed-off lead in a new campaign is blocked

Tasks: handoff model and endpoints (Sharon, 8h) · exclusion rule plus tests (Sharon, 6h) · handoff UI and
"my conversations" queue (Herman, 8h) · assignee notification event (Mark, 4h). **Total 26h.** *(6 pts
effectively — see estimation note in §7.)*

#### E9-S2 — Follow-up cadence scheduler
*Sprint 4 · 8 pts · Owner: Sharon · Reviewer: Mark*
As Anne, I want follow-ups scheduled automatically with a stop rule, so persistence happens without nagging.

- [ ] A cadence policy defines touches (default day 0, day 3, day 7)
- [ ] Cadence stops on reply, opt-out, handoff, or exhaustion
- [ ] Follow-up drafts are generated into the approval queue, not sent automatically
- [ ] A paused campaign generates no new touches
- [ ] Each stop condition has a test

Tasks: cadence scheduler and Celery beat (Sharon, 16h) · stop-condition tests (Sharon, 8h) · cadence
policy configuration UI (Herman, 8h). **Total 32h.**

#### E9-S3 — Follow-up due list
*Sprint 4 · 3 pts · Owner: Herman · Reviewer: Sharon*
As Anne, I want a daily list of what needs attention, so nothing goes stale.

- [ ] A due list shows drafts awaiting approval, replies awaiting classification, and follow-ups due today
- [ ] Stale leads (no touch in 7 days) are surfaced
- [ ] The dashboard shows the same three counts

Tasks: due-list queries (Sharon, 5h) · dashboard and due-list UI (Herman, 6h) · tests (Sharon, 1h).
**Total 12h.**

### Epic E10 — Pipeline and deals

#### E10-S1 — Deal model and stage transitions
*Sprint 5 · 5 pts · Owner: Sharon · Reviewer: Mark*
As Anne, I want a deal per qualified lead, so money is tracked, not just conversations.

- [ ] A deal has an offer, amount, currency, expected close date, and stage
- [ ] Stages: `qualified`, `proposal`, `negotiation`, `won`, `lost`
- [ ] Closing a deal requires a disposition and, when lost, a lost reason
- [ ] Stage changes are recorded as activity events

Tasks: deal model and migration (Sharon, 8h) · stage transition endpoints and tests (Sharon, 8h) ·
disposition and lost-reason taxonomy (Anne, 4h). **Total 20h.**

#### E10-S2 — Pipeline board
*Sprint 5 · 5 pts · Owner: Herman · Reviewer: Mark*
As Anne, I want to see deals by stage, so I know what to work on today.

- [ ] A board shows deals grouped by stage with amount totals per column
- [ ] Cards show business name, offer, amount, age in stage, and last activity
- [ ] A card can be moved between stages
- [ ] The board is usable on a laptop screen without horizontal scrolling

Tasks: pipeline API (Sharon, 6h) · kanban UI with drag or stage selector (Herman, 14h). **Total 20h.**

#### E10-S3 — Disposition and outcome capture
*Sprint 5 · 3 pts · Owner: Herman · Reviewer: Sharon*
As a team, we want every lead to end in a recorded outcome, so the funnel has no leaks.

- [ ] Every lead reaches a terminal disposition: won, lost, no response, not interested, opted out
- [ ] Won deals record the amount actually earned
- [ ] Lost deals require a reason from a controlled list
- [ ] A report of undecided leads is available

Tasks: disposition endpoints (Sharon, 5h) · outcome capture UI on lead detail (Herman, 6h) · tests
(Sharon, 1h). **Total 12h.**

### Epic E11 — Reporting and funnel metrics

#### E11-S1 — Funnel metric computation
*Sprint 5 · 5 pts · Owner: Sharon · Reviewer: Mark*
As Herman, I want funnel rates computed per campaign and segment, so the numbers are computed once and consistently.

- [ ] Metrics from scope §7 are computed: reply rate, positive rate, handoff rate, meeting rate, close rate, revenue
- [ ] Every metric matches the agreed definition document and has a unit test with known fixture data
- [ ] Metrics can be sliced by sector, area, source, offer, and message variant
- [ ] Metrics exclude opted-out leads from denominators where the definition requires it

Tasks: metrics service and queries (Sharon, 12h) · fixture-based unit tests for every metric (Sharon, 8h).
**Total 20h.**

#### E11-S2 — Reports screen
*Sprint 5 · 8 pts · Owner: Herman · Reviewer: Mark*
As a team, I want to see which sector, source, and message actually converts, so we decide where to sell next from evidence.

- [ ] Campaign report shows counts and rates across the funnel
- [ ] Segment report compares sectors and areas side by side
- [ ] Message variant report compares reply and positive rates per variant
- [ ] Source report compares cold research against referrals and existing clients
- [ ] Empty states explain what must happen before numbers appear

Tasks: reports API (Sharon, 8h) · campaign and funnel view (Herman, 10h) · segment, variant and source
comparison views (Herman, 10h) · empty-state and definition tooltips (Anne, 4h). **Total 32h.**

#### E11-S3 — Logged exports
*Sprint 5 · 3 pts · Owner: Sharon · Reviewer: Mark*
As Herman, I want exports to be deliberate and recorded, so personal data does not leak quietly.

- [ ] Lead and campaign data export to CSV
- [ ] Every export writes an activity event with actor, timestamp, and row count
- [ ] Only owner and sales roles can export
- [ ] Exports exclude fields the role may not see

Tasks: export endpoints with audit events (Sharon, 8h) · role tests (Sharon, 4h). **Total 12h.**

### Epic E12 — Pilot campaign operations

#### E12-S1 — Website offer copy pack
*Sprint 2 · 3 pts · Owner: Anne · Reviewer: Herman*
As Anne, I want tested copy variants ready before the send path exists, so the pilot is not blocked by writing.

- [ ] Variants A/B for the no-website case, and a separate variant for social-only businesses
- [ ] Each variant follows the five-line pattern and stays under 500 characters
- [ ] Each variant states price and a clear question, and includes no false claims
- [ ] Each variant has an opt-out line suitable for the channel

Tasks: copy variants (Anne, 8h) · review against brand voice (Herman, 4h). **Total 12h.**

#### E12-S2 — Warm and referral lead sourcing
*Sprint 3 · 3 pts · Owner: Anne · Reviewer: Herman*
As a team, we want warm leads in the system, so the pilot can compare cold against warm.

- [ ] At least 10 referral or warm-introduction leads added, with source recorded as `referral` or `existing_client`
- [ ] Each warm lead records who referred it
- [ ] Cold and warm leads are distinguishable in reports

Tasks: source and add warm leads (Anne, 10h) · verify in reports (Herman, 2h). **Total 12h.**

#### E12-S3 — Pilot campaign execution
*Sprint 6 · 8 pts · Owner: Anne · Reviewer: Herman*
As a team, we want one real campaign run end to end, so the engine is proven on real businesses.

- [ ] A campaign of at least 40 cold leads and every available warm lead is run through the full loop
- [ ] Every outreach has a recorded outcome
- [ ] Every reply is classified, and every positive reply is handed off within one working day
- [ ] Post-pilot metrics are available in reports
- [ ] No guardrail violation occurred (verified in the activity log)

Tasks: campaign setup (Anne, 8h) · daily review of approval queue and replies (Anne, 16h) · tracker of
incidents and questions raised by real use (Herman, 8h). **Total 32h.**

#### E12-S4 — Pilot retrospective and "where to sell next" report
*Sprint 6 · 3 pts · Owner: Anne · Reviewer: Herman*
As the owners, we want a written answer to what we learned, so the next campaign is better than this one.

- [ ] Report answers: which sector responded, which source converted, which variant worked, what stalled
- [ ] At least three concrete changes proposed for the next campaign
- [ ] At least one decision on the next offer to push beyond websites
- [ ] Report is reviewed by the whole team

Tasks: analysis and report (Anne, 8h) · team review session (Herman, 4h). **Total 12h.**

### Epic E13 — Hardening, deployment, and onboarding

#### E13-S1 — Security review
*Sprint 6 · 5 pts · Owner: Mark · Reviewer: Herman*
As owners, we want the system reviewed before real data scales, so we do not leak our pipeline or our clients'.

- [ ] No secret is committed; secrets load from environment only
- [ ] Every endpoint enforces authentication and role where required
- [ ] Access to contact details is enforced and tested
- [ ] Rate limits and pacing limits are verified in a live test
- [ ] Findings are written down with severity and an owner

Tasks: security review pass (Mark, 12h) · fixes for findings (Sharon, 4h) · role and secret tests
(Sharon, 4h). **Total 20h.**

#### E13-S2 — Test coverage and CI hardening
*Sprint 6 · 5 pts · Owner: Sharon · Reviewer: Mark*
As a team, we want confidence to change code, so the engine can keep evolving after the pilot.

- [ ] Critical paths have tests: auth, import, generation, approval guard, send idempotency, cadence stop, opt-out
- [ ] Coverage on services is at a level the team agrees to and records
- [ ] CI blocks on failures across both applications
- [ ] Tests run in under five minutes locally

Tasks: coverage pass on services (Sharon, 12h) · CI tuning for runtime (Sharon, 4h) · flaky test triage
(Sharon, 4h). **Total 20h.**

#### E13-S3 — Deployment and backups
*Sprint 6 · 5 pts · Owner: Mark · Reviewer: Sharon*
As a team, we want the engine running somewhere real with backups, so the pilot data is safe.

- [ ] Deployed on the VPS with Docker Compose and Nginx, alongside FikaTu patterns
- [ ] Database backups run on a schedule and a restore has been tested once
- [ ] Basic metrics and logs are visible
- [ ] Deployment steps are documented well enough for someone else to follow

Tasks: deployment (Mark, 8h) · backups and a tested restore (Mark, 6h) · logging and metrics (Sharon,
4h) · deployment doc (Herman, 2h). **Total 20h.**

#### E13-S4 — Team onboarding and demo script
*Sprint 6 · 3 pts · Owner: Herman · Reviewer: Anne*
As a team, we want a short demo and onboarding path, so new members and hired salespeople can be productive.

- [ ] A five-minute demo script covering the full loop
- [ ] An onboarding checklist: get running, run tests, make a trivial PR
- [ ] A one-page guide for a new sales user
- [ ] Walkthrough recorded or written for the four of us

Tasks: demo script and onboarding guide (Herman, 8h) · sales-user guide (Anne, 4h). **Total 12h.**

---

## 5. Sprint plan

### Sprint 0 — Alignment and foundations (1 week)
**Goal:** everyone can run the stack locally, the schema is agreed, and the FikaTu path is proven.
**Committed:** E1-S1 (5), E1-S2 (3), E1-S3 (3), E1-S4 (3), E1-S5 (2), E1-S6 (2) = **18 pts**
**Demo:** `docker compose up` on each of the four laptops, ERD walkthrough, a test event delivered through FikaTu.
**Risk retired:** unknown environment and unknown integration shape blocking Sprint 1.

### Sprint 1 — Lead Desk
**Goal:** the real lead list is in the system and Anne can work from it instead of a spreadsheet.
**Committed:** E2-S1 (5), E2-S2 (3), E3-S1 (3), E4-S1 (5), E4-S2 (8), E4-S3 (6) = **30 pts**
**Demo:** import the 52-row list, browse and filter leads, open a lead timeline, show a rejected-row report.
**Risk retired:** the data-quality problems in the audit turning into a dead end.

### Sprint 2 — Campaigns and approval
**Goal:** a campaign produces real personalised drafts that a human reviews before anything sends.
**Committed:** E5-S1 (5), E5-S2 (5), E6-S1 (8), E6-S2 (8), E12-S1 (3) = **29 pts**
**Demo:** build a campaign, generate drafts, edit one, approve some, reject one with a reason.
**Risk retired:** building a blaster instead of a reviewed pipeline; unapproved sending.

### Sprint 3 — Delivery through FikaTu
**Goal:** approved messages actually leave the building and we can prove what happened to each one.
**Committed:** E5-S3 (3), E7-S1 (8), E7-S2 (5), E7-S3 (8), E7-S4 (5), E7-S5 (3), E12-S2 (3) = **35 pts** *(over-committed — see §7)*
**Demo:** **M1 — first live sends** to a small slice (5-10 leads), then the outreach log showing delivery status.
**Risk retired:** the FikaTu integration being a guess, and duplicate sends on retry.

### Sprint 4 — Replies and handoff
**Goal:** a reply can be captured, qualified, and handed to a person who is notified.
**Committed:** E8-S1 (5), E8-S2 (5), E8-S3 (3), E9-S1 (5), E9-S2 (8), E9-S3 (3) = **29 pts**
**Demo:** **M2 — first handed-off conversation**, with the lead excluded from automation and the assignee notified.
**Risk retired:** automated follow-up nagging a hot lead; a reply going unnoticed.

### Sprint 5 — Pipeline and reporting
**Goal:** the funnel is visible end to end and can be sliced by sector, source, and message variant.
**Committed:** E10-S1 (5), E10-S2 (5), E10-S3 (3), E11-S1 (5), E11-S2 (8), E11-S3 (3) = **29 pts**
**Demo:** **M3 — funnel visible end to end**, with a segment comparison answering "which sector replied".
**Risk retired:** flying blind; no basis for deciding where to sell next.

### Sprint 6 — Hardening and the pilot
**Goal:** run the full pilot on the real list and come out with evidence.
**Committed:** E13-S1 (5), E13-S2 (5), E13-S3 (5), E13-S4 (3), E12-S3 (8), E12-S4 (3) = **29 pts**
**Demo:** **M4 — pilot campaign executed and reviewed**, with the "where to sell next" report presented.
**Risk retired:** the system working in a demo but not in the hands of a real seller.

---

## 6. Assignment matrix

Primary = owns the story end to end. Secondary = reviewing, pairing, or the same sprint's non-dev work.

| Person | Sprint 0 | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 | Sprint 5 | Sprint 6 |
|---|---|---|---|---|---|---|---|
| **Mark** | Primary: E1-S1, E1-S5. Secondary: E1-S3 review, CI branch protection | Primary: E2-S1, E4-S1. Secondary: review all backend PRs | Primary: E5-S2. Secondary: review E5-S1, E6-S2; pairing on E6-S1 | Primary: E7-S1, E7-S2. Secondary: E12-S2 review, E7-S5 pacing config | Primary: reviewer for E8-S2, E9-S1, E9-S2 | Primary: reviewer across E10-E11. Secondary: E10-S1 design support | Primary: E13-S1, E13-S3. Secondary: support E13-S2 |
| **Herman** | Primary: E1-S4. Secondary: E1-S1 frontend scaffold, E1-S6 review | Primary: E4-S3. Secondary: E2-S1 review, E3-S1 seed data | Primary: E6-S2. Secondary: E5-S1 template editor, E12-S1 review | Primary: E7-S4. Secondary: E5-S3, E7-S1 fake harness review | Primary: E8-S1, E8-S3, E9-S3. Secondary: E9-S1 UI | Primary: E10-S2, E11-S2. Secondary: E10-S3 | Primary: E13-S4. Secondary: E12-S3 incident tracker, E12-S4 review |
| **Anne** | Primary: E1-S6, E1-S4 sales review. Secondary: lead-list curation | Secondary: verify import result on the real list; qualification criteria draft | Primary: E12-S1. Secondary: E6-S2 rejection reasons, E5-S1 seed copy | Primary: E12-S2. Secondary: pilot plan draft | Secondary: validate qualification fields in a real conversation; review E8-S1 | Primary: E10-S1 disposition taxonomy. Secondary: E11-S2 empty-state copy | Primary: E12-S3, E12-S4. Secondary: E13-S4 sales-user guide |
| **Sharon** | Primary: E1-S2, E1-S3 Alembic. Secondary: E1-S1 health endpoint | Primary: E2-S2, E3-S1, E4-S2. Secondary: pairing with Mark on E4-S1 | Primary: E5-S1, E6-S1. Secondary: pairing on E7 prep | Primary: E7-S3, E7-S5, E5-S3. Secondary: E7-S1 fake harness, E7-S4 API | Primary: E9-S2, E8-S2. Secondary: E9-S3 queries | Primary: E10-S1, E11-S1, E11-S3. Secondary: E10-S2 API | Primary: E13-S2. Secondary: E13-S1 fixes, E13-S3 logging |

**Load check:** each sprint gives every person one primary story (sometimes two small ones) and
one secondary responsibility. Mark's sprint-1 load is the heaviest (two primaries plus all
backend review) — Sprint 2 deliberately reduces his primaries to one, and Sharon pairs on
E4-S1 in Sprint 1 so the review burden falls on two people, not one.

---

## 7. Estimation summary

| Sprint | Committed points | Team hours implied | Notes |
|---|---|---|---|
| Sprint 0 (1 week) | 18 | ~72h | Slightly above the 1-week nominal because alignment work is cheap and parallel |
| Sprint 1 | 30 | ~120h | At capacity |
| Sprint 2 | 29 | ~116h | At capacity |
| Sprint 3 | 35 | ~140h | **Over-committed.** See below |
| Sprint 4 | 29 | ~116h | At capacity |
| Sprint 5 | 29 | ~116h | At capacity |
| Sprint 6 | 29 | ~116h | At capacity |
| **Total** | **199** | **~796h** | Across roughly 13 working weeks |

**Sprint 3 is knowingly over-committed.** It carries the integration risk, and integration
work is the least predictable work in the plan. Two mitigations, decided at planning:

1. E5-S3 (saved segments, 3 pts) is the designated flex — it moves to Sprint 4 if the
   integration runs long, because segments are a convenience and the integration is not.
2. E7-S1 and E7-S3 are estimated at 8 points each and are the two most likely to be wrong.
   Mark and Sharon pair on both, and if either slips, the sprint is re-cut at the mid-sprint
   checkpoint rather than discovered at the end.

**If one person is unavailable for a sprint:** drop that person's primary story with the
lowest user-visible value, and let their secondary work be absorbed by the reviewer of the
story they share. The plan is built so no story has a single point of failure: every primary
owner has a named reviewer who can pick the story up.

**Velocity check:** after Sprint 1 the team records actual points completed and replaces the
30-point assumption with the real number. If actual velocity is materially lower, the
correct response is to cut scope from the later sprints, not to work longer hours.

---

## 8. Dependency graph

```
Sprint 0 (foundations)
   ├── E1-S1 scaffold ──► everything
   ├── E1-S3 schema ────► E4-S1 ──► E4-S2, E4-S3
   ├── E1-S4 wireframes ► E4-S3, E6-S2
   ├── E1-S5 FikaTu app ─► E7-S1
   └── E1-S6 metrics ───► E11-S1

Sprint 1 (Lead Desk) ──► Sprint 2 needs leads and users to exist
   E2-S1 auth ──► every protected endpoint
   E4-S2 import ──► the pilot's lead supply

Sprint 2 (campaigns, drafts, approval)
   E5-S1 templates ──► E5-S2 campaign ──► E6-S1 drafts ──► E6-S2 approval
   E12-S1 copy pack ─► E6-S1 (seed content)

Sprint 3 (delivery)
   E7-S1 client ──► E7-S3 send ──► E7-S4 status ──► M1 first live sends
   E7-S2 state machine ──► E7-S3 (must exist before sending)
   E7-S5 guardrails ──► E7-S3

Sprint 4 (replies, handoff)
   E7-S3 sent ──► E8-S1 replies ──► E8-S2 transitions ──► E9-S1 handoff ──► M2
   E9-S2 cadence ──► E9-S3 due list

Sprint 5 (pipeline, reports)
   E8-S3 qualification ──► E10-S1 deals ──► E10-S2 pipeline
   E1-S6 metric definitions ──► E11-S1 metrics ──► E11-S2 reports ──► M3

Sprint 6 (hardening, pilot)
   everything ──► E12-S3 pilot ──► E12-S4 retrospective ──► M4
```

### Critical path

1. E1-S1 scaffold → E1-S3 schema → E4-S1 lead model
2. E5-S2 campaign → E6-S1 draft generation → E6-S2 approval queue
3. E7-S2 state machine → E7-S1 FikaTu client → E7-S3 send → M1
4. E8-S1 replies → E9-S1 handoff → M2
5. E11-S1 metrics → E11-S2 reports → M3
6. E12-S3 pilot → E12-S4 retrospective → M4

The two places the critical path can break are **E4-S2 (CSV import)** in Sprint 1 and
**E7-S1/E7-S3 (FikaTu client and send)** in Sprint 3. Both are over-estimated on purpose
and both have a second pair of hands assigned.

---

## 9. Ceremonies calendar

Assumes a Monday sprint start.

| Day | Ceremony | Duration | Participants |
|---|---|---|---|
| Monday, week 1 | Sprint planning | 90 min | All four |
| Every working day | Daily standup | 15 min | All four |
| Wednesday, week 1 | Tech huddle (optional) | 30 min | Mark, Sharon, and anyone with technical blockers |
| Thursday, week 1 | Backlog refinement | 45 min | All four |
| Monday, week 2 | Mid-sprint checkpoint | 20 min | All four — re-cut if Sprint 3-style over-commitment is visible |
| Friday, week 2 | Sprint review / demo | 45 min | All four |
| Friday, week 2 | Retrospective | 45 min | All four |
| Friday, week 2 | Velocity and plan update | 20 min | Herman updates this document |

---

## 10. Traceability

Every in-scope item from the spec, mapped to the sprint that delivers it.

| Scope spec item | Epic / story | Sprint |
|---|---|---|
| §4.1 (1) Auth and users | E2-S1, E2-S2 | 1 |
| §4.1 (2) Offers | E3-S1 | 1 |
| §4.1 (3) Leads | E4-S1, E4-S2, E4-S3 | 1 |
| §4.1 (4) Lead detail and timeline | E4-S3 | 1 |
| §4.1 (5) Message templates | E5-S1 | 2 |
| §4.1 (6) Campaigns | E5-S2, E5-S3 | 2, 3 |
| §4.1 (7) Draft generation | E6-S1 | 2 |
| §4.1 (8) Approval queue | E6-S2 | 2 |
| §4.1 (9) Sending via FikaTu | E7-S1, E7-S2, E7-S3, E7-S4 | 3 |
| §4.1 (10) Replies | E8-S1, E8-S2 | 4 |
| §4.1 (11) Handoff | E9-S1 | 4 |
| §4.1 (12) Qualification | E8-S3 | 4 |
| §4.1 (13) Pipeline and deals | E10-S1, E10-S2, E10-S3 | 5 |
| §4.1 (14) Follow-up tasks | E9-S2, E9-S3 | 4 |
| §4.1 (15) Reports v1 | E11-S1, E11-S2 | 5 |
| §4.1 (16) Activity log | E4-S3 (write path), E7-S2, E11-S3 | 1, 3, 5 |
| §9 (1) No bulk WhatsApp blasting | E7-S5, E12-S3 | 3, 6 |
| §9 (2) Human approval before send | E6-S2, E7-S2 | 2, 3 |
| §9 (3) Opt-out is terminal | E7-S5, E8-S2 | 3, 4 |
| §9 (4) Consent and provenance recorded | E4-S1, E4-S2 | 1 |
| §9 (5) No real lead data in git | E1-S1 (env and ignore rules), E11-S3 | 0, 5 |
| §9 (6) Access control on personal data | E2-S2, E4-S3, E11-S3 | 1, 5 |
| §9 (7) Rate limiting and pacing | E7-S5 | 3 |
| §9 (8) Honest reporting | E7-S4, E11-S1 | 3, 5 |
| §7 Success metrics | E1-S6, E11-S1, E11-S2 | 0, 5 |
| §11 Open questions 1-8 | E1-S6 (Q1), E4-S1 (Q2, Q5), E7-S5 (Q3), E13-S3 (Q4), E12-S1 (Q6), E9-S2 (Q7), E3-S1 (Q8) | 0-6 |

---

## 11. Explicitly deferred

Not in this plan, deliberately. Each would need its own scope decision.

- AI-generated message drafts and AI reply classification.
- WhatsApp Business API inbound webhooks and automatic reply capture.
- Lead scoring and automatic segment discovery.
- Email enrichment to add addresses to the current phone-only list.
- Multi-tenant support, billing, and quotation generation.
- Calendar integration and meeting booking.
- A public marketing site for the product.
- Mobile application.
