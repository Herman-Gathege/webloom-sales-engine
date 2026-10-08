# Webloom Sales Engine — Product Scope & Design Spec

**Date:** 2026-10-08
**Status:** Draft for team review
**Owners:** Herman Gathege (product), Mark Mwenesi (engineering)
**Team:** Herman Gathege, Mark Mwenesi, Anne, Sharon Kendi
**Repo:** https://github.com/Herman-Gathege/webloom-sales-engine
**Related systems:** FikaTu / notification platform — https://github.com/Herman-Gathege/notifications_pipeline_system

> This is the scope document we agree on before any code is written. Everything below is
> a proposal to be corrected by the team, not a settled contract. Open questions are
> collected at the end.

---

## 1. Problem statement

Webloom + Innovations can build far more than websites: SaaS products, enterprise systems,
APIs, automation, AI, ERP, payments, and the FikaTu notification platform. The constraint
is not capability. It is **sales throughput and sales learning**.

Today, winning work depends on a human doing repetitive prospecting work by hand: finding
businesses, checking whether they are worth approaching, writing a message, remembering to
follow up, and keeping track of what happened. Every lead that is not contacted is a
campaign that never happened. Every conversation that is not recorded is a lesson the
company cannot reuse.

Two specific pressures make this urgent:

1. **Website-only selling will stall.** Website build cost is collapsing as tooling
   improves. If the only thing we sell is a website, price pressure will eat the business,
   and we already pay KES 5,000 of a KES 40,000 website sale to the person who closes it.
2. **Our real products are invisible.** FikaTu, ERP/enterprise work, and automation are
   higher-value and harder to sell because they require a conversation, not a price list.
   We need a systematic way to find the businesses that need them.

## 2. Vision

Build a **sales engine**: a system that reliably turns a market into qualified, human-ready
conversations, and that learns from every one of them.

The engine automates the ~80% of sales work that happens *before* a human is valuable —
finding, researching, segmenting, writing, sending, following up, and recording. It stops
and hands over at the ~20% that actually closes: a real conversation with a person.

Three commitments define the product:

1. **Automation creates opportunity; a human converts it.** Nothing sends without human
   approval in v1, and interest triggers handover to a person.
2. **Every interaction is data.** The system should eventually answer: which sector buys,
   which lead source converts, which message works, which offer sells — and therefore where
   to sell and what to sell next.
3. **Websites are the entry offer, not the ceiling.** The engine is product-agnostic from
   day one. A website package is simply the first row in an offers table.

### 2.1 Why this also fixes the website stall

The engine does not try to make websites more profitable by selling them harder. It uses
websites as a low-friction entry point and converts the conversation into a relationship
and a diagnosis of what the business actually needs. The lead record accumulates evidence
(sector, size, complaints, systems in use, what they asked about) and that evidence becomes
the pipeline for FikaTu, ERP, automation, and AI work. The website is the door; the engine
decides which doors are worth knocking on and what is behind them.

## 3. Users and roles

The first users are the four of us. The system is internal, single-company, and
role-based — **not** multi-tenant SaaS in v1.

| Role | Who | Can do |
|---|---|---|
| `owner` | Herman, Mark | Everything, including user management and settings |
| `sales` | Anne (later: hired salespeople) | Leads, campaigns, approval, replies, qualification, handoff, deals |
| `engineer` | Mark, Herman, Sharon | Read-only on sales data; full access to offers/templates/config |
| `viewer` | stakeholders | Read-only dashboards and reports |

### 3.1 How each person's skills map to the work

Everyone is a developer here, so delivery work is shared. Product and sales
responsibilities sit *on top of* development work, not instead of it. This is a starting
proposal — swap freely, the point is that nobody is idle and nobody is a bottleneck.

| Person | Primary contribution | Also owns |
|---|---|---|
| **Mark Mwenesi** (lead, most skilled) | Architecture, backend + infrastructure, code review, hardest integration work, unblocking others | Technical decisions, ADRs, deployment, security review |
| **Herman Gathege** | Product scope, backlog and prioritisation, user stories and acceptance criteria, sprint ceremonies, stakeholder communication | Frontend delivery, documentation, demo/pilot coordination |
| **Anne** | Sales workflow design, message copy and templates, lead-list curation, qualification criteria, handoff playbook, pilot campaign execution | Definition of the funnel metrics, feedback loop from real conversations |
| **Sharon Kendi** (co-intern) | Backend features end-to-end (models, services, APIs), tests, migrations, integration work | Documentation of what she builds, paired work with Mark on hard tasks |

**Growth intent:** assignments deliberately mix strength with stretch. Sharon gets
well-bounded backend slices with review, not only ticket-factory work. Herman gets
delivery-visible frontend work alongside PM duties. Anne's sales knowledge is treated as a
first-class engineering input (she defines the funnel, we implement it).

## 4. Scope

### 4.1 In scope for v1 (the MVP)

The MVP is a working loop, end to end, on a real lead list:

> import leads → build a campaign → generate personalised drafts → approve → send via
> FikaTu → record replies → qualify → hand over to a human → record the outcome

Concretely:

1. **Auth and users** — login, four roles, permissions.
2. **Offers** — the things we sell, with price guidance and a pitch angle. Website packages
   first; other services storable from day one.
3. **Leads** — create, edit, list, filter (sector, area, website status, status, owner),
   CSV import with validation and de-duplication on normalised phone number.
4. **Lead detail** — full timeline: every outreach, reply, note, status change, who did it
   and when.
5. **Message templates** — per offer and channel, with variables, and A/B variants.
6. **Campaigns** — a named batch of leads, one offer, one template (or variant set), one
   channel, an owner, and a goal.
7. **Draft generation** — render personalised drafts per lead from template + lead data.
8. **Approval queue** — a human reviews, edits, approves, or rejects each draft before it
   can be sent. Bulk approve is allowed; bulk *send without review* is not.
9. **Sending via FikaTu** — publish the approved message to FikaTu, store the returned
   notification reference, and sync delivery status back.
10. **Replies** — record an inbound reply against a lead and outreach, with a
    classification (positive / negative / neutral / opt-out).
11. **Handoff** — mark a lead as human-owned; it leaves the automated funnel and appears in
    a "my conversations" queue.
12. **Qualification** — structured fields captured during a conversation (need, budget
    signal, timeline, decision maker, next step).
13. **Pipeline** — a deal per qualified lead with stages and an outcome (won / lost / no
    response / not interested / opted out), including amount and lost reason.
14. **Follow-up tasks** — scheduled next touches, with a due list, so the engine does not
    forget.
15. **Reports v1** — campaign and segment performance: contacted, replied, positive,
    handoffs, meetings, won, revenue, plus rates.
16. **Activity log** — an append-only record of every state change, actor, and timestamp.
    This is the raw material for the learning phase.

### 4.2 Explicitly out of scope for v1

- Multi-tenant SaaS, billing, subscriptions, or invoicing.
- Fully autonomous sending, or any send path that bypasses human approval.
- Indiscriminate bulk WhatsApp blasting. See §9.
- Automated scraping of Google Maps or any site whose terms forbid it.
- AI-generated message copy as a hard dependency. Templates + variables are enough for v1;
  AI drafting is a later, additive capability.
- Automatic reply detection from WhatsApp. v1 records replies manually; the integration
  gap is documented in the FikaTu research note.
- Full CRM features: email sync, call logging, calendar booking, quotation generation.
- A public marketing site for the product itself.

### 4.3 Deferred but designed for (v2+)

Reply ingestion via WhatsApp Business webhooks, AI draft assistance and reply
classification, lead scoring, automatic segmentation discovery, revenue attribution across
offers, and a referral/partner pipeline. The data model below is shaped so these are
additions, not rewrites.

## 5. Core concepts and vocabulary

Shared language, used consistently in code, UI, and conversation. One term per idea.

| Term | Meaning |
|---|---|
| **Offer** | Something we sell, e.g. "Starter website", "Notification platform (FikaTu)". Has price guidance and a pitch angle. |
| **Lead** | A business entity we may approach. Identified by normalised phone. |
| **Source** | Where the lead came from: `google_maps`, `referral`, `inbound`, `existing_client`, `walk_in`. Drives the learning analysis. |
| **Segment** | A saved filter over leads (e.g. opticians, no website, Westlands). |
| **Campaign** | A batch of leads × one offer × one template × one channel, with an owner and a goal. |
| **Touch** / **Outreach** | One message to one lead within a campaign. This is the unit that has a delivery status. |
| **Reply** | An inbound message from the lead, tied to a touch. |
| **Qualification** | The structured result of a conversation: need, budget signal, timeline, decision maker, next step. |
| **Handoff** | The moment a lead stops being automated and becomes a human's conversation. |
| **Deal** | A qualified lead being worked toward money. Has a stage, an amount, and an outcome. |
| **Disposition** | How a lead ended: `won`, `lost`, `no_response`, `not_interested`, `opted_out`. |
| **Touch cadence** | The follow-up schedule for a campaign (e.g. day 0, day 3, day 7), with a stop rule. |

### 5.1 The funnel

Every lead moves through a single, visible funnel. Anything not in the funnel is a bug.

```
New → Contacted → Replied → Qualified → Handed off → Proposal → Won
                                                              ↘ Lost
        ↘ No response (after cadence exhausted)
        ↘ Not interested          ↘ Opted out (terminal, never contact again)
```

## 6. System architecture

### 6.1 Shape

Two applications, one integration seam:

```
  ┌───────────────────────────────┐        ┌──────────────────────────────┐
  │  Webloom Sales Engine         │        │  FikaTu (existing)           │
  │  (this repo)                  │        │  (notifications_pipeline_    │
  │                               │        │   system)                    │
  │  React SPA ──► FastAPI API    │        │                              │
  │                    │          │        │  FastAPI API                 │
  │                    ▼          │        │      │                       │
  │              PostgreSQL       │        │  PostgreSQL + Redis          │
  │                    │          │        │      │                       │
  │                 Redis         │        │  Celery workers              │
  │                    │          │        │      │                       │
  │              Celery workers   │        │  Providers: email, SMS,      │
  │                    │          │        │  WhatsApp                    │
  └────────────────────┼──────────┘        └──────┼───────────────────────┘
                       │  publish event (HTTP)    │
                       └──────────────────────────┘
                            + poll delivery status
```

**The boundary rule:** the Sales Engine knows about leads, campaigns, replies, and deals.
FikaTu knows about events, templates, channels, providers, and delivery. FikaTu must never
learn anything about sales; the Sales Engine must never implement provider integrations
itself.

### 6.2 Stack (reused from FikaTu, deliberately)

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI (Python 3.12), SQLAlchemy 2.0, Alembic | Same as FikaTu; shared patterns, shared review muscle |
| Database | PostgreSQL 17 | Same |
| Queue | Redis 7 + Celery 5.5 | Needed for scheduled cadences and status sync |
| Validation / config | Pydantic v2, pydantic-settings | Same |
| Auth | JWT (python-jose), passlib/bcrypt, middleware | Same pattern as FikaTu, roles added |
| Frontend | React 19, Vite, TypeScript, Tailwind v4, shadcn/ui, React Router v7, TanStack Table, Axios | Same as FikaTu's frontend stack |
| Infra | Docker, Docker Compose, Nginx | Same |
| Logging / metrics | structlog, prometheus-client | Same |

Adopting the FikaTu stack is a deliberate trade: we lose the novelty of a new framework and
gain the ability to move fast, reuse code and conventions, and have Mark review both
systems with the same mental model.

### 6.3 Backend layering

Follow the FikaTu layout so contribution is uniform across both repos:

```
backend/app/
├── api/v1/          # route handlers only: parse, authorise, delegate
├── schemas/         # Pydantic request/response models
├── services/        # business logic (the layer that holds the rules)
├── repositories/    # data access; the only layer that writes SQL
├── models/          # SQLAlchemy ORM models
├── workers/         # Celery tasks (cadence scheduling, status sync)
├── middleware/      # auth, request id, logging
├── config/          # settings
├── database/        # session, base
└── integrations/    # FikaTu client (one module, one clear interface)
```

`integrations/fikatu/` is the only place that knows FikaTu's HTTP API exists. Everything
else calls a small internal interface (e.g. `send_message(...) -> DeliveryRef`), which keeps
the seam testable with a fake.

### 6.4 Data model sketch

Indicative tables — final schema is a design task in Sprint 0.

| Table | Purpose | Key fields |
|---|---|---|
| `users` | team members | email, password_hash, full_name, role, is_active |
| `offers` | what we sell | name, slug, description, price_min, price_max, currency, pitch_angle, is_active |
| `leads` | businesses | business_name, sector, area, phone_normalised, whatsapp_capable, website_status, source, status, owner_id, consent_basis, notes |
| `lead_contact_points` | phone/email per lead | lead_id, kind, value, is_primary, consent_status |
| `message_templates` | copy | offer_id, channel, name, variant, body, variables, is_active |
| `campaigns` | batches | name, offer_id, template_id, channel, owner_id, segment_filter, goal, status, cadence_policy |
| `outreaches` | one message to one lead | campaign_id, lead_id, template_id, channel, rendered_body, state, approved_by, approved_at, sent_at, provider_ref, delivery_status, failure_reason |
| `replies` | inbound messages | outreach_id, lead_id, body, received_at, classification, classification_source, recorded_by |
| `follow_up_tasks` | scheduled next touches | lead_id, campaign_id, due_at, kind, state, owner_id |
| `qualifications` | conversation outcomes | lead_id, need, budget_signal, timeline, decision_maker, next_step, captured_by |
| `handoffs` | automation → human | lead_id, from_campaign_id, to_user_id, reason, handed_off_at |
| `deals` | money | lead_id, offer_id, stage, amount, currency, expected_close, disposition, lost_reason, closed_at |
| `activity_events` | append-only audit + learning feed | entity_type, entity_id, actor_id, event_type, payload (JSONB), created_at |
| `import_batches` | CSV provenance | filename, uploaded_by, row_count, accepted_count, rejected_count, error_report |

Two invariants worth stating early, because they protect the whole product:

- **`outreaches.state` is a state machine.** The send path is reachable only from
  `approved`. There is no edge from `draft` to `sent`.
- **`leads.status` is derived from evidence, not typed by hand.** It is computed from
  touches, replies, handoffs, and deals. Manual override is recorded as an activity event.

### 6.5 Frontend surfaces (v1)

| Screen | Job |
|---|---|
| Login | Auth |
| Dashboard | Funnel snapshot, today's actions, stale leads |
| Leads | Filterable list, CSV import, bulk actions |
| Lead detail | Timeline, contact points, qualification, handoff, notes |
| Campaigns | Create campaign from offer + segment + template + cadence |
| Campaign detail | Draft generation, progress, per-lead state |
| Approval queue | Review / edit / approve / reject drafts |
| Outreach log | Delivery status per message, failures, retries |
| Replies | Record and classify replies; the trigger for handoff |
| My conversations | Handed-off leads owned by the current user |
| Pipeline | Deal stages, amounts, disposition |
| Reports | Campaign and segment performance |
| Settings | Offers, templates, users, channels |

### 6.6 Error handling and reliability

- Sending is **idempotent per (outreach, attempt)**: retries must not double-send. The
  FikaTu reference is stored before any retry is possible.
- Delivery status sync is a Celery task with backoff; unknown status is never treated as
  success, and the UI shows `unknown` honestly.
- Failures are surfaced in the outreach log with a reason, never silently swallowed.
- CSV import is **all-or-nothing per row**: bad rows are rejected with a reason and a
  downloadable error report; good rows still import.

### 6.7 Testing strategy

- Backend: `pytest` + `pytest-asyncio` (matches FikaTu). Services and the state machine get
  real unit tests; the FikaTu client is tested against a fake, plus one optional live
  smoke test behind an env flag.
- Frontend: lint + typecheck + build in CI; component tests for the approval queue and
  handoff flow, which are the two places where a bug has real-world cost.
- The four of us review each other's PRs; Mark reviews anything touching auth, sending, or
  the schema.

### 6.8 Integration with FikaTu

The Sales Engine registers itself in FikaTu as an **application**, obtains an API key and
secret, and publishes events. It does not talk to Resend, Africa's Talking, or WhatsApp
directly.

The exact endpoint shapes, token flow, event-type registration steps, template management,
delivery-status query, and a list of gaps are documented in
`docs/research/2026-10-08-fikatu-integration-notes.md` (produced alongside this spec).

What the Sales Engine will need from FikaTu, in order of confidence:

1. **Send an outreach message** — high confidence FikaTu supports this shape today for
   email and SMS; likely needs a new registered event type.
2. **Read delivery status per message** — needs verification.
3. **Receive inbound replies** — almost certainly not supported today; the near-term
   workaround is manual reply capture in the Sales Engine UI.

## 7. Success metrics

Metrics exist to answer "where should we sell and what should we sell", so they are
defined now, not bolted on later.

**Activity (weekly):** leads added, leads contacted, follow-ups completed on time, campaigns
run.

**Conversion:** reply rate, positive-reply rate, handoff rate, meeting rate, proposal rate,
close rate, revenue per 100 leads contacted.

**Efficiency:** cost per lead, cost per handoff, time from lead added to first touch,
percentage of approved messages actually sent.

**Learning (the point of the whole thing):** conversion by sector, by source, by message
variant, and by offer — feeding a monthly "where to sell next" decision.

Each metric needs a definition we all accept, an owner, and a place it is displayed.
Anne owns the definitions; the Reports screen owns the display.

## 8. Delivery approach

Agile, four people, two-week sprints, all four as developers. The detailed backlog,
epics, stories, task assignments, and per-sprint goals live in
`docs/delivery/2026-10-08-agile-delivery-plan.md`.

Shape of the plan:

| Sprint | Theme | Milestone |
|---|---|---|
| Sprint 0 (1 week) | Alignment, scaffold, environments, schema review, FikaTu app registration | Everyone can run the stack locally |
| Sprint 1 | Lead Desk: auth, users, leads, CSV import, lead detail, activity log | The 52-lead list is in the system |
| Sprint 2 | Offers, templates, campaigns, draft generation, approval queue | Real personalised drafts, reviewed by a human |
| Sprint 3 | FikaTu integration, sending, delivery status sync | **M1: first live emails/SMS to a small slice** |
| Sprint 4 | Replies, qualification, handoff, follow-up tasks | **M2: a real conversation handed to Anne** |
| Sprint 5 | Pipeline, deals, reports v1 | **M3: funnel visible end to end** |
| Sprint 6 | Hardening, onboarding, full pilot on the lead list | **M4: pilot campaign executed and reviewed** |

**Definition of Done (every story):** code reviewed by one other person, tests written and
passing, runs in Docker locally, docs/README updated if behaviour changed, and the story is
demoed in the sprint review.

**Working agreements:** trunk-based with short-lived branches (`feat/…`, `fix/…`),
conventional commits, PR required before merge, Mark reviews auth/sending/schema changes.
Daily 15-minute standup; sprint review + retrospective at sprint end. Decisions that are
hard to reverse get an ADR in `docs/decisions/`.

## 9. Guardrails and compliance

These are product requirements, not nice-to-haves. A sales engine that burns the company's
reputation or a provider account is worse than no sales engine.

1. **No indiscriminate WhatsApp blasting.** Cold, untargeted bulk messaging violates
   platform rules and destroys trust. WhatsApp use requires an approved template, a clear
   opt-out path, and a legitimate basis for the contact.
2. **Human approval before send.** Enforced in the state machine, not just the UI.
3. **Opt-out is terminal.** An opted-out lead is never contacted again by any campaign. The
   check happens at send time, not just at campaign-build time.
4. **Consent and provenance recorded.** Every lead stores its source, the basis on which we
   hold the data, and the purpose. Business contact information gathered from public
   listings is recorded as such.
5. **Real lead data never enters git.** The lead list contains real phone numbers. It lives
   in a gitignored `data/` directory; the repo carries only a schema file with synthetic
   examples. Bulk exports are deliberate, logged actions.
6. **Access control on personal data.** Only `owner` and `sales` roles see contact details;
   exports are logged in `activity_events`.
7. **Rate limiting and pacing.** Sending is paced per channel so a campaign cannot burst
   into a provider ban.
8. **Honest reporting.** Delivery status shown as reported; unknown is unknown.

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Cold outreach damages the Webloom brand | High | Tight targeting, human approval, opt-out, small pilot first |
| Website sales stall before the engine proves itself | High | The engine's first job is to expose higher-value needs; keep selling manually in parallel |
| FikaTu cannot deliver what we assume (status, inbound) | Medium | Research note above; design the seam so it can be swapped or supplemented |
| Scope creep into a full CRM | High | The out-of-scope list in §4.2 is enforced at sprint planning |
| Four people, other commitments, exam/iteration periods | Medium | Sprint 0 is small; stories are bite-sized; no story depends on one person finishing late |
| Team is learning Scrum and the stack simultaneously | Medium | Small sprints, visible demo, Mark pairs with Sharon |
| Personal data mishandled | High | §9 rules, gitignored data, access control, audit log |

## 11. Open questions

To be resolved during Sprint 0 or as they arise. Each has an owner and a default so we are
never blocked.

| # | Question | Default we will assume | Owner |
|---|---|---|---|
| 1 | Do we run the first pilot on email, SMS, or WhatsApp? | **SMS.** The current list has phone numbers and no email addresses, and FikaTu's WhatsApp provider is an empty file, so SMS is the only channel that is both available and addressed today. Email becomes viable once addresses are sourced. | Anne |
| 2 | Is the lead list data legal for cold outreach, and what is our stated basis? | Publicly listed business contact details, B2B, opt-out honoured | Herman |
| 3 | Do we need multi-channel within one campaign in v1? | No — one channel per campaign | Mark |
| 4 | Where do we host for the pilot? | Docker Compose on the existing VPS, same box family as FikaTu | Mark |
| 5 | Who is the first hired salesperson, and does the UI need to support them? | Not yet; roles are designed so they can be added without schema change | Herman |
| 6 | Do we sell from a price list or a discovery-first conversation? | Discovery-first, with price guidance on the offer record | Anne |
| 7 | What is the follow-up cadence, and when do we stop? | 3 touches over 10 days, then `no_response` | Anne |
| 8 | What is the first non-website offer to put in the catalogue? | FikaTu-powered notification platform | Herman |

## 12. Approval

This spec is the gate. Once the four of us agree on it, we write the implementation plan
(`docs/superpowers/plans/…`) and start Sprint 0. Changes after approval are proposed as
edits to this file, so the written scope stays the single source of truth.
