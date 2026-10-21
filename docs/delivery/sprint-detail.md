# Sprint detail — what each sprint contains

This is the detail behind [the sprint plan](sprint-plan.md): the individual pieces of work
inside each sprint, with their acceptance criteria and rough estimates. It is reference
material, not a reading path. Read the sprint you are working on, and read the
[scope spec](../superpowers/specs/2026-10-08-webloom-sales-engine-scope.md) when you need to
know what is in scope at all. Nobody reads this end to end.

**Estimates:** 1 point ≈ half a focused day. The numbers compare stories against each other;
they are guidance, not a schedule. The owner is accountable for the piece, and the reviewer is
always someone else.

---

## Sprint 1 — the first working slice ✅ done

Shipped 2026-10-13 by all four of us. What it was, what is verified, and what we learned is in
[the Sprint 1 record](../homework/sprint-1/status.md). The criteria below are the full
definition of each story; the italic note under each one says what the thin slice deliberately
left out.

### Repository scaffold and one-command local environment
*Owner: Mark · Reviewer: Herman · ~5 pts*
As a developer, I want one command that brings up the whole stack, so nobody loses a day to setup.

- [ ] `docker compose up --build` starts api, worker, postgres, redis, and frontend from a clean clone
- [ ] `GET /health` returns 200 and reports database and redis status
- [ ] Swagger is reachable at `/docs`
- [ ] `.env.example` lists every variable; no secret is committed
- [ ] The README instructions actually work when followed literally

Tasks: backend Dockerfile and entrypoint (Mark, 5h) · compose file with six services (Mark, 5h) ·
health endpoint (Sharon, 3h) · env template and setup docs (Herman, 3h) · frontend Vite scaffold
wired to the API (Herman, 4h). **Total 20h.**

*Left:* the slice ships the database, the API and the frontend only. The worker and Redis arrive
with sending in Sprint 6.

### Lead schema and first migration
*Owner: Mark · Reviewer: Sharon · ~5 pts*
As a team, we want leads stored in a structure we can report on, so the list is an asset not a spreadsheet.

- [ ] Fields include source, source_url, consent_basis, reviews_count, has_website, social_presence, status, owner
- [ ] Phone is stored normalised (E.164) with the original string preserved
- [ ] De-duplication is enforced on normalised phone at the database level
- [ ] Status is derived from evidence, with manual overrides recorded as activity events
- [ ] Migration is reversible

Tasks: model and migration (Mark, 8h) · status derivation service plus tests (Mark, 6h) · migration
review and backfill script (Sharon, 6h). **Total 20h.**

*Left:* the shipped table covers the fields the first slice needed — business, sector, area,
phone, website status, source and status — with a reversible migration and a repeatable seed.
`reviews_count`, `social_presence` and `consent_basis` are an open decision the team owes before
the importer lands, because the real list carries those columns.

### Leads list and lead detail timeline
*Owner: Herman · Reviewer: Mark · ~6 pts*
As Anne, I want to filter leads by sector, area, website status, and owner, and open one to see its full history.

- [ ] List API supports filters, search, and pagination returning under 500ms on 5,000 leads
- [ ] UI filters by sector, area, website status, status, and owner
- [ ] Lead detail shows contact points, source, consent basis, and notes
- [ ] Every change to a lead appears in a timestamped timeline with the actor's name
- [ ] Contact details are hidden from roles that may not see them

Tasks: list and detail endpoints with filters (Sharon, 8h) · leads table UI (Herman, 8h) · lead detail
and timeline UI (Herman, 6h) · activity log write path (Sharon, 4h) · role-based field visibility tests
(Sharon, 4h). **Total 30h.**

*Left:* the list and the detail with its activity history shipped. Filters and search are Sprint 2.
Hiding contact details by role needs login, so it lands in Sprint 3.

---

## Sprint 2 — the Lead Desk is real ← we are here

**Owner:** Sharon · **Reviewer:** Mark. The real 52-row list goes in, the list becomes filterable,
and CI lands so a red test is visible to everyone instead of only to whoever ran it.

### Continuous integration
*Owner: Mark · Reviewer: Sharon · ~3 pts*
As a team, we want every PR checked automatically, so broken code cannot merge.

- [ ] CI runs on every PR: backend lint, backend tests, frontend lint, frontend build
- [ ] A deliberately failing test fails the build
- [ ] CI status is required before merge

Tasks: workflow file (Mark, 4h) · backend lint and test job (Mark, 3h) · frontend lint and
build job (Mark, 3h) · branch protection settings (Sharon, 2h). **Total 12h.**

### CSV import with mapping, validation, and an error report
*Owner: Sharon · Reviewer: Mark · ~8 pts*
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

### Leads list with filters, search, and lead detail timeline
*Owner: Herman · Reviewer: Mark · ~6 pts*
As Anne, I want to filter leads by sector, area, website status, and owner, and open one to see its full history.

- [ ] List API supports filters, search, and pagination returning under 500ms on 5,000 leads
- [ ] UI filters by sector, area, website status, status, and owner
- [ ] Lead detail shows contact points, source, consent basis, and notes
- [ ] Every change to a lead appears in a timestamped timeline with the actor's name
- [ ] Contact details are hidden from roles that may not see them

Tasks: list and detail endpoints with filters (Sharon, 8h) · leads table UI (Herman, 8h) · lead detail
and timeline UI (Herman, 6h) · activity log write path (Sharon, 4h) · role-based field visibility tests
(Sharon, 4h). **Total 30h.**

*Left from Sprint 1:* the filters, the search box, and the parts of the detail that need the
fields the importer brings in. The timeline itself already works.

### Screen inventory and wireframes signed off
*Owner: Herman · Reviewer: Anne · ~3 pts*
As a team, we want the 13 screens sketched and agreed, so builds match a shared picture.

- [ ] All 13 surfaces from scope §6.5 have a sketch or clear description
- [ ] The approval queue and handoff flows are drawn in detail (they carry the most risk)
- [ ] Anne has confirmed the screens match how she actually sells
- [ ] Sign-off recorded in this repo

Tasks: wireframes (Herman, 8h) · sales workflow review session (Anne, 4h). **Total 12h.**

*Open question:* this may move to Sprint 3. It is listed here because Sprint 2 already changes the
Lead Desk. The team decides.

---

## Sprint 3 — lock the door

**Owner:** Mark · **Reviewer:** Herman. Login, users and roles. Only we can reach the pipeline.

### Authentication and login
*Owner: Mark · Reviewer: Herman · ~5 pts*
As a team member, I want to log in securely, so only we can see our pipeline.

- [ ] Login with email and password returns a JWT; wrong credentials return 401
- [ ] Passwords are stored with bcrypt; no plaintext or reversible hash anywhere
- [ ] Protected endpoints reject missing, malformed, and expired tokens
- [ ] Token expiry and refresh behaviour are documented
- [ ] Lockout or delay after repeated failed attempts

Tasks: user model and password hashing (Mark, 6h) · login endpoint and JWT issue/verify (Mark, 6h) ·
auth middleware and dependency (Mark, 4h) · auth tests including failure paths (Sharon, 4h).
**Total 20h.**

### User management and role enforcement
*Owner: Sharon · Reviewer: Mark · ~3 pts*
As an owner, I want to manage users and roles, so access matches responsibility.

- [ ] Owners can create, deactivate, and re-role users
- [ ] `owner`, `sales`, `engineer`, `viewer` are enforced on the API, not only hidden in the UI
- [ ] A `viewer` cannot read contact details; a `sales` user can
- [ ] Attempts to exceed a role are covered by tests

Tasks: user CRUD endpoints (Sharon, 6h) · role guard dependency (Sharon, 3h) · role tests (Sharon,
3h). **Total 12h.**

---

## Sprint 4 — what we sell, in the system

**Owner:** Sharon · **Reviewer:** Mark. Offers and message templates become data, not code.

### Offer catalogue with seeded website packages
*Owner: Sharon · Reviewer: Mark · ~3 pts*
As a seller, I want the things we sell stored as data, so we can add non-website offers without code.

- [ ] Offers can be created, edited, deactivated; fields: name, slug, description, price range, currency, pitch angle
- [ ] Starter, Business, and Custom website offers are seeded
- [ ] A FikaTu notification platform offer can be added through the UI with no code change
- [ ] Inactive offers cannot be selected in a campaign

Tasks: offer model and migration (Sharon, 4h) · CRUD endpoints and schemas (Sharon, 5h) · seed
data (Herman, 3h). **Total 12h.**

### Message templates with variants
*Owner: Sharon · Reviewer: Mark · ~5 pts*
As Anne, I want reusable templates per offer and channel with variants, so I can test copy without code.

- [ ] Templates belong to an offer and a channel and carry a variant label (for example `A`, `B`)
- [ ] Variables are declared and validated against the lead fields they reference
- [ ] A template with an unknown variable is rejected with a clear message
- [ ] The five-line pattern from the existing lead list is stored as the seed template

Tasks: template model and migration (Sharon, 5h) · CRUD endpoints and variable validation (Sharon,
8h) · template editor UI (Herman, 5h) · seed templates from the lead list (Anne, 2h). **Total 20h.**

### Website offer copy pack
*Owner: Anne · Reviewer: Herman · ~3 pts*
As Anne, I want tested copy variants ready before the send path exists, so the pilot is not blocked by writing.

- [ ] Variants A/B for the no-website case, and a separate variant for social-only businesses
- [ ] Each variant follows the five-line pattern and stays under 500 characters
- [ ] Each variant states price and a clear question, and includes no false claims
- [ ] Each variant has an opt-out line suitable for the channel

Tasks: copy variants (Anne, 8h) · review against brand voice (Herman, 4h). **Total 12h.**

---

## Sprint 5 — campaigns and drafts

**Owner:** Herman · **Reviewer:** Mark. A campaign produces one personalised draft per eligible lead.

### Campaign creation
*Owner: Mark · Reviewer: Sharon · ~5 pts*
As Anne, I want to create a campaign from an offer, a segment, a template, and a cadence, so a batch of outreach is a deliberate act.

- [ ] A campaign requires an offer, a channel, a template, an owner, and a goal
- [ ] Leads are attached by segment or by explicit selection, with a preview count before saving
- [ ] A campaign cannot include leads that have opted out
- [ ] Campaign preview shows effective channel eligibility, purpose, and technical-contact skips
- [ ] Campaign status moves through `draft`, `active`, `paused`, `completed`

Tasks: campaign model and migration (Sharon, 6h) · create and preview endpoints (Mark, 8h) · campaign
creation UI (Herman, 6h). **Total 20h.**

### Saved segments
*Owner: Herman · Reviewer: Sharon · ~3 pts*
As Anne, I want to save a filter as a named segment, so I can reuse "opticians with no website" without retyping it.

- [ ] A segment stores a named filter definition
- [ ] Segments can be previewed with a live count
- [ ] Segments can be used as a campaign source

Tasks: segment model and endpoints (Sharon, 5h) · segment builder UI (Herman, 5h) · tests (Sharon, 2h).
**Total 12h.**

### Personalised draft generation
*Owner: Sharon · Reviewer: Mark · ~8 pts*
As Anne, I want a personalised draft per lead generated from the template, so I review messages instead of writing them.

- [ ] Generating drafts for a campaign produces exactly one draft per eligible lead
- [ ] Rendered text matches the seed message for the seed leads, byte for byte
- [ ] Leads missing a required variable are skipped and listed with the reason
- [ ] Opted-out and call-only leads are excluded according to channel rules
- [ ] Only a human `eligible` decision for the selected channel can produce a sendable draft
- [ ] Generation is idempotent: running it twice does not duplicate drafts

Tasks: rendering service with tests (Sharon, 12h) · eligibility rules (Sharon, 6h) · generation job and
endpoint (Sharon, 8h) · generation UI with progress and skip report (Herman, 6h). **Total 32h.**

---

## Sprint 6 — approve, then send

**Owner:** Mark · **Reviewer:** Sharon. A human approves, and only then does it send — through
FikaTu. **Channels for now: SMS through Africa's Talking in FikaTu's sandbox, and email.**
WhatsApp is not implemented in FikaTu and is deferred.

### Register the Sales Engine as a FikaTu application
*Owner: Mark · Reviewer: Herman · ~2 pts*
As a team, we want real credentials and a verified publish path, so delivery is not blocked later.

- [ ] An application is registered in FikaTu and its key and secret are stored locally, not in git
- [ ] A test event is published successfully to a safe recipient
- [ ] The result is documented in the integration research note

Tasks: registration and local secret handling (Mark, 4h) · publish smoke test and write-up
(Mark, 4h). **Total 8h.**

### Approval queue
*Owner: Herman · Reviewer: Mark · ~8 pts*
As Anne, I want to review, edit, approve, or reject each draft before it sends, so nothing goes out without a human deciding.

- [ ] Drafts are visible with lead context (business, sector, area, source, review count)
- [ ] A draft can be edited inline; edits are stored on the outreach, not the template
- [ ] Approve, reject, and bulk approve work; each records the actor and timestamp
- [ ] `draft` cannot move directly to `sent`; the API rejects an attempt
- [ ] Sent items are the approved message version, with approval actor/time and campaign purpose retained
- [ ] Rejected drafts require a reason chosen from a list
- [ ] The queue loads 100 drafts without noticeable lag

Tasks: approve/reject/edit endpoints and state guard (Sharon, 10h) · approval queue UI with bulk actions
(Herman, 14h) · state machine tests including the forbidden transition (Sharon, 4h) · rejection reason
list (Anne, 4h). **Total 32h.**

### FikaTu client module
*Owner: Mark · Reviewer: Sharon · ~8 pts*
As a developer, I want one module that speaks to FikaTu, so no other code knows it exists.

- [ ] The client handles token acquisition, caching, and refresh
- [ ] One method publishes an outreach message and returns a delivery reference
- [ ] Network failures, timeouts, 4xx, and 5xx are distinguished and surfaced with the provider's message
- [ ] The client is tested against a fake HTTP layer, with no live calls in the test suite
- [ ] A single live smoke test runs only when an env flag is set

Tasks: client module with tests (Mark, 16h) · configuration and secret loading (Mark, 6h) · fake-server
test harness (Sharon, 6h) · live smoke test guarded by env flag (Sharon, 4h). **Total 32h.**

### Outreach state machine
*Owner: Mark · Reviewer: Sharon · ~5 pts*
As a team, we want outreach to move through explicit states, so a bug cannot send something it should not.

- [ ] States: `draft`, `approved`, `queued`, `sent`, `delivered`, `failed`, `cancelled`
- [ ] Only `approved` may be queued; only `queued` may be sent
- [ ] Every transition records actor, timestamp, and reason
- [ ] Queued follow-ups are cancelled when a matching suppression is recorded
- [ ] Illegal transitions raise a typed error and are covered by tests
- [ ] The state machine is the only writer of `sent_at` and `delivery_status`

Tasks: state machine implementation (Mark, 8h) · transition tests including illegal paths (Sharon, 8h) ·
activity event recording (Sharon, 4h). **Total 20h.**

### Send worker with idempotency
*Owner: Sharon · Reviewer: Mark · ~8 pts*
As Anne, I want approved messages sent exactly once, so a retry never double-messages a business.

- [ ] A Celery task sends queued outreaches in batches with pacing
- [ ] The FikaTu reference is persisted before any retry is possible
- [ ] Every attempt and retry rereads approval, eligibility, purpose, suppression, and opt-out content
- [ ] Re-running the task never sends the same outreach twice
- [ ] Terminal failures move the outreach to `failed` with a reason
- [ ] A kill-and-restart mid-batch sends no duplicates

Tasks: send task and batching (Sharon, 12h) · idempotency key and persistence (Sharon, 8h) · retry and
failure handling (Mark, 8h) · crash-and-resume test (Sharon, 4h). **Total 32h.**

### Delivery status sync and outreach log
*Owner: Herman · Reviewer: Mark · ~5 pts*
As Anne, I want to see what was delivered, so a silence is never mistaken for success.

- [ ] A scheduled task polls FikaTu for status updates and updates outreach records
- [ ] Unknown status is displayed as unknown, never as delivered
- [ ] The outreach log filters by campaign, state, channel, and date
- [ ] Failures show the failure reason and allow one retry

Tasks: status sync task (Sharon, 8h) · outreach log API (Sharon, 4h) · outreach log UI with filters
(Herman, 8h). **Total 20h.**

### Channel eligibility, pacing, and opt-out guard at send time
*Owner: Sharon · Reviewer: Mark · ~3 pts*
As a team, we want the guardrails enforced at send time, so a stale campaign cannot break a platform rule.

- [ ] Send-time checks reject opted-out leads, call-only leads on WhatsApp/SMS, and leads without a valid number
- [ ] Send-time checks reject `needs_review`, missing provenance/evidence, stale purpose, and unapproved campaigns
- [ ] Sends are paced per channel so a batch cannot burst
- [ ] A guardrail rejection is recorded as an activity event with the reason
- [ ] Each guardrail has a test that proves it blocks

Tasks: guardrail service and tests (Sharon, 8h) · pacing configuration (Mark, 4h). **Total 12h.**

---

## Sprint 7 — replies and handoff

**Owner:** Anne · **Reviewer:** Sharon. Replies are captured, leads are qualified, and the moment a
lead shows interest automation stops for it.

### Reply capture
*Owner: Herman · Reviewer: Sharon · ~5 pts*
As Anne, I want to record a reply against the message that caused it, so the funnel reflects reality.

- [ ] A reply is recorded against an outreach and its lead
- [ ] Reply text, channel, and timestamp are stored
- [ ] A reply can be classified positive, negative, neutral, or opt-out
- [ ] An opt-out reply immediately makes the lead terminal and blocks all future sends
- [ ] Recording a reply updates the lead's derived status

Tasks: reply model and endpoints (Sharon, 8h) · reply capture UI (Herman, 8h) · opt-out propagation tests
(Sharon, 4h). **Total 20h.**

### Funnel transition rules
*Owner: Sharon · Reviewer: Mark · ~5 pts*
As a team, we want derived lead status, so nobody maintains a status field by hand.

- [ ] Positive reply moves the lead to `replied` and flags it for handoff
- [ ] Negative reply moves the lead to `not_interested` and stops its cadence
- [ ] Opt-out moves the lead to `opted_out`, which is terminal
- [ ] Cadence exhaustion moves the lead to `no_response`
- [ ] Every derived transition has a test

Tasks: transition rules service (Sharon, 12h) · rule tests (Sharon, 6h) · manual override with recorded
reason (Herman, 2h). **Total 20h.**

### Qualification capture
*Owner: Herman · Reviewer: Sharon · ~3 pts*
As Anne, I want one form to record what a conversation revealed, so knowledge survives the conversation.

- [ ] Fields: need, budget signal, timeline, decision maker, next step, free notes
- [ ] Qualification is attached to the lead and time-stamped with who captured it
- [ ] A lead cannot be marked qualified without need and next step
- [ ] The most recent qualification is visible on the lead and on pipeline cards

Tasks: qualification model and endpoints (Sharon, 5h) · qualification form UI (Herman, 6h) · validation
tests (Sharon, 1h). **Total 12h.**

### Handoff to a human
*Owner: Herman · Reviewer: Mark · ~5 pts*
As Anne, I want an interested lead handed to me and removed from automation, so a real conversation is never interrupted by a bot.

- [ ] A handoff assigns the lead to a user and records reason and timestamp
- [ ] After handoff, the lead is excluded from all automated sends in every campaign
- [ ] Handed-off leads appear in a "my conversations" queue for the assignee
- [ ] A handoff sends a notification to the assignee through FikaTu
- [ ] Attempting to include a handed-off lead in a new campaign is blocked

Tasks: handoff model and endpoints (Sharon, 8h) · exclusion rule plus tests (Sharon, 6h) · handoff UI and
"my conversations" queue (Herman, 8h) · assignee notification event (Mark, 4h). **Total 26h.**
*(6 pts effectively — this one is a flag to split, not a reason to work late.)*

### Follow-up cadence scheduler
*Owner: Sharon · Reviewer: Mark · ~8 pts*
As Anne, I want follow-ups scheduled automatically with a stop rule, so persistence happens without nagging.

- [ ] A cadence policy defines touches (default day 0, day 3, day 7)
- [ ] Cadence stops on reply, opt-out, handoff, or exhaustion
- [ ] Follow-up drafts are generated into the approval queue, not sent automatically
- [ ] A paused campaign generates no new touches
- [ ] Each stop condition has a test

Tasks: cadence scheduler and Celery beat (Sharon, 16h) · stop-condition tests (Sharon, 8h) · cadence
policy configuration UI (Herman, 8h). **Total 32h.**

### Follow-up due list
*Owner: Herman · Reviewer: Sharon · ~3 pts*
As Anne, I want a daily list of what needs attention, so nothing goes stale.

- [ ] A due list shows drafts awaiting approval, replies awaiting classification, and follow-ups due today
- [ ] Stale leads (no touch in 7 days) are surfaced
- [ ] The dashboard shows the same three counts

Tasks: due-list queries (Sharon, 5h) · dashboard and due-list UI (Herman, 6h) · tests (Sharon, 1h).
**Total 12h.**

---

## Sprint 8 — the funnel, visible

**Owner:** Herman · **Reviewer:** Mark. Deals, outcomes, and reports that say which sector, source
and message actually convert.

### Agreed funnel metric definitions
*Owner: Anne · Reviewer: Herman · ~2 pts*
As a team, we want one agreed definition per metric, so reports mean the same thing to everyone.

- [ ] Every metric in scope §7 has a one-sentence definition and a formula
- [ ] Reply rate and positive-reply rate are unambiguous, including what counts as a reply
- [ ] Each metric has an owner and the screen where it appears

Tasks: definitions document (Anne, 6h) · review with the team (Herman, 2h). **Total 8h.**

### Deal model and stage transitions
*Owner: Sharon · Reviewer: Mark · ~5 pts*
As Anne, I want a deal per qualified lead, so money is tracked, not just conversations.

- [ ] A deal has an offer, amount, currency, expected close date, and stage
- [ ] Stages: `qualified`, `proposal`, `negotiation`, `won`, `lost`
- [ ] Closing a deal requires a disposition and, when lost, a lost reason
- [ ] Stage changes are recorded as activity events

Tasks: deal model and migration (Sharon, 8h) · stage transition endpoints and tests (Sharon, 8h) ·
disposition and lost-reason taxonomy (Anne, 4h). **Total 20h.**

### Pipeline board
*Owner: Herman · Reviewer: Mark · ~5 pts*
As Anne, I want to see deals by stage, so I know what to work on today.

- [ ] A board shows deals grouped by stage with amount totals per column
- [ ] Cards show business name, offer, amount, age in stage, and last activity
- [ ] A card can be moved between stages
- [ ] The board is usable on a laptop screen without horizontal scrolling

Tasks: pipeline API (Sharon, 6h) · kanban UI with drag or stage selector (Herman, 14h). **Total 20h.**

### Disposition and outcome capture
*Owner: Herman · Reviewer: Sharon · ~3 pts*
As a team, we want every lead to end in a recorded outcome, so the funnel has no leaks.

- [ ] Every lead reaches a terminal disposition: won, lost, no response, not interested, opted out
- [ ] Won deals record the amount actually earned
- [ ] Lost deals require a reason from a controlled list
- [ ] A report of undecided leads is available

Tasks: disposition endpoints (Sharon, 5h) · outcome capture UI on lead detail (Herman, 6h) · tests
(Sharon, 1h). **Total 12h.**

### Funnel metric computation
*Owner: Sharon · Reviewer: Mark · ~5 pts*
As Herman, I want funnel rates computed per campaign and segment, so the numbers are computed once and consistently.

- [ ] Metrics from scope §7 are computed: reply rate, positive rate, handoff rate, meeting rate, close rate, revenue
- [ ] Every metric matches the agreed definition document and has a unit test with known fixture data
- [ ] Metrics can be sliced by sector, area, source, offer, and message variant
- [ ] Metrics exclude opted-out leads from denominators where the definition requires it

Tasks: metrics service and queries (Sharon, 12h) · fixture-based unit tests for every metric (Sharon, 8h).
**Total 20h.**

### Reports screen
*Owner: Herman · Reviewer: Mark · ~8 pts*
As a team, I want to see which sector, source, and message actually converts, so we decide where to sell next from evidence.

- [ ] Campaign report shows counts and rates across the funnel
- [ ] Segment report compares sectors and areas side by side
- [ ] Message variant report compares reply and positive rates per variant
- [ ] Source report compares cold research against referrals and existing clients
- [ ] Empty states explain what must happen before numbers appear

Tasks: reports API (Sharon, 8h) · campaign and funnel view (Herman, 10h) · segment, variant and source
comparison views (Herman, 10h) · empty-state and definition tooltips (Anne, 4h). **Total 32h.**

### Logged exports
*Owner: Sharon · Reviewer: Mark · ~3 pts*
As Herman, I want exports to be deliberate and recorded, so personal data does not leak quietly.

- [ ] Lead and campaign data export to CSV
- [ ] Every export writes an activity event with actor, timestamp, and row count
- [ ] Only owner and sales roles can export
- [ ] Exports exclude fields the role may not see

Tasks: export endpoints with audit events (Sharon, 8h) · role tests (Sharon, 4h). **Total 12h.**

---

## Sprint 9 — pilot and harden

**Owner:** Mark · **Reviewer:** Anne. One real campaign run end to end, then security review,
deployment and backups.

### Warm and referral lead sourcing
*Owner: Anne · Reviewer: Herman · ~3 pts*
As a team, we want warm leads in the system, so the pilot can compare cold against warm.

- [ ] At least 10 referral or warm-introduction leads added, with source recorded as `referral` or `existing_client`
- [ ] Each warm lead records who referred it
- [ ] Cold and warm leads are distinguishable in reports

Tasks: source and add warm leads (Anne, 10h) · verify in reports (Herman, 2h). **Total 12h.**

### Pilot campaign execution
*Owner: Anne · Reviewer: Herman · ~8 pts*
As a team, we want one real campaign run end to end, so the engine is proven on real businesses.

- [ ] A campaign of at least 40 cold leads and every available warm lead is run through the full loop
- [ ] Every outreach has a recorded outcome
- [ ] Every reply is classified, and every positive reply is handed off within one working day
- [ ] Post-pilot metrics are available in reports
- [ ] No guardrail violation occurred (verified in the activity log)

Tasks: campaign setup (Anne, 8h) · daily review of approval queue and replies (Anne, 16h) · tracker of
incidents and questions raised by real use (Herman, 8h). **Total 32h.**

### Pilot retrospective and "where to sell next" report
*Owner: Anne · Reviewer: Herman · ~3 pts*
As the owners, we want a written answer to what we learned, so the next campaign is better than this one.

- [ ] Report answers: which sector responded, which source converted, which variant worked, what stalled
- [ ] At least three concrete changes proposed for the next campaign
- [ ] At least one decision on the next offer to push beyond websites
- [ ] Report is reviewed by the whole team

Tasks: analysis and report (Anne, 8h) · team review session (Herman, 4h). **Total 12h.**

### Security review
*Owner: Mark · Reviewer: Herman · ~5 pts*
As owners, we want the system reviewed before real data scales, so we do not leak our pipeline or our clients'.

- [ ] No secret is committed; secrets load from environment only
- [ ] Every endpoint enforces authentication and role where required
- [ ] Access to contact details is enforced and tested
- [ ] Rate limits and pacing limits are verified in a live test
- [ ] Findings are written down with severity and an owner

Tasks: security review pass (Mark, 12h) · fixes for findings (Sharon, 4h) · role and secret tests
(Sharon, 4h). **Total 20h.**

### Test coverage and CI hardening
*Owner: Sharon · Reviewer: Mark · ~5 pts*
As a team, we want confidence to change code, so the engine can keep evolving after the pilot.

- [ ] Critical paths have tests: auth, import, generation, approval guard, send idempotency, cadence stop, opt-out
- [ ] Coverage on services is at a level the team agrees to and records
- [ ] CI blocks on failures across both applications
- [ ] Tests run in under five minutes locally

Tasks: coverage pass on services (Sharon, 12h) · CI tuning for runtime (Sharon, 4h) · flaky test triage
(Sharon, 4h). **Total 20h.**

### Deployment and backups
*Owner: Mark · Reviewer: Sharon · ~5 pts*
As a team, we want the engine running somewhere real with backups, so the pilot data is safe.

- [ ] Deployed on the VPS with Docker Compose and Nginx, alongside FikaTu patterns
- [ ] Database backups run on a schedule and a restore has been tested once
- [ ] Basic metrics and logs are visible
- [ ] Deployment steps are documented well enough for someone else to follow

Tasks: deployment (Mark, 8h) · backups and a tested restore (Mark, 6h) · logging and metrics (Sharon,
4h) · deployment doc (Herman, 2h). **Total 20h.**

### Team onboarding and demo script
*Owner: Herman · Reviewer: Anne · ~3 pts*
As a team, we want a short demo and onboarding path, so new members and hired salespeople can be productive.

- [ ] A five-minute demo script covering the full loop
- [ ] An onboarding checklist: get running, run tests, make a trivial PR
- [ ] A one-page guide for a new sales user
- [ ] Walkthrough recorded or written for the four of us

Tasks: demo script and onboarding guide (Herman, 8h) · sales-user guide (Anne, 4h). **Total 12h.**

---

## What we are not building yet

Deliberately out of the nine sprints. Each needs its own scope decision before anyone builds it.

- AI-generated message drafts and AI reply classification.
- WhatsApp: sending, and inbound webhooks for automatic reply capture.
- Lead scoring and automatic segment discovery.
- Email enrichment to add addresses to the current phone-only list.
- Multi-tenant support, billing, and quotation generation.
- Calendar integration and meeting booking.
- A public marketing site for the product.
- A mobile application.

## Where the work came from

The [scope spec](../superpowers/specs/2026-10-08-webloom-sales-engine-scope.md) is the authority
for what is in scope and what is not. This file is the detailed backlog that delivers it. Where
this file and the [sprint plan](sprint-plan.md) disagree about order or ownership, the sprint
plan wins.
