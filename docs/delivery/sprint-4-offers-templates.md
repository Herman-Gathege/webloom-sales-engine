# Sprint 4 — offers and templates

**Status:** closed with accepted deviations · **Owner:** Sharon · **Reviewer:** Mark
**Branch:** `sprint/4-offers-templates` · **Updated:** 2026-11-09

The exit review is [Sprint 4 status](../homework/sprint-4/status.md). PR
[#29](https://github.com/Herman-Gathege/webloom-sales-engine/pull/29) shipped the catalogue and
PR [#30](https://github.com/Herman-Gathege/webloom-sales-engine/pull/30) merged the completed
sprint branch.

## Goal

Make what Webloom sells and the copy used to introduce it editable data. An administrator can
create an offer, prepare reusable email or SMS templates for that offer, and deactivate either
without changing code.

Sprint 4 stops before campaigns and drafts. Its output is a trustworthy catalogue that Sprint 5
can select from.

## Why this slice

The current pipeline understands leads and compliance but not the product being sold. Without
offers and approved copy, campaign building would mix commercial data into code and make A/B
learning impossible.

The result is:

```text
Offer catalogue
  → reusable channel templates
  → validated personalisation variables
  → [Sprint 5: segments, campaigns, drafts]
```

## Roles

| Role | Access |
|---|---|
| `admin` | List active and inactive offers/templates; create, edit and deactivate |
| `sales` | Read active offers/templates |

The API enforces these permissions. Hiding controls in the UI is not authorization.

## Offers

An offer stores:

| Field | Rule |
|---|---|
| `id` | UUID |
| `name` | Required, trimmed, up to 120 characters |
| `slug` | Required, unique, lowercase kebab-case |
| `description` | Plain text |
| `price_min` | Optional non-negative decimal |
| `price_max` | Optional non-negative decimal, greater than or equal to `price_min` |
| `currency` | Three-letter uppercase code, default `KES` |
| `pitch_angle` | Plain text explaining the commercial angle |
| `is_active` | Defaults to true |
| `created_at`, `updated_at` | Server-managed timestamps |

Offers are deactivated rather than hard-deleted. An inactive offer remains visible to admins
for history but cannot be used by a future campaign.

Initial catalogue:

1. Starter Website
2. Business Website
3. Custom Website
4. FikaTu Notification Platform

Starter Website is seeded at **KES 40,000**. Business Website and Custom Website remain
unpriced until the team supplies their guidance. The model permits blank price guidance for
discovery-first offers; no other pricing is invented in the seed.

Currency accepts any uppercase three-letter code. The editor offers KES, USD, EUR, GBP, ZAR,
UGX and TZS without restricting the API to that display list.

## Templates

A template stores:

| Field | Rule |
|---|---|
| `id` | UUID |
| `offer_id` | Required reference to an offer |
| `channel` | `email` or `sms` in this sprint |
| `name` | Required, up to 120 characters |
| `variant` | Required short label, normalised uppercase; `A` and `B` are the initial examples |
| `body` | Required plain text |
| `variables` | Declared variable names used by the body |
| `is_active` | Defaults to true |
| `created_at`, `updated_at` | Server-managed timestamps |

The combination of offer, channel and variant is unique. Templates are deactivated rather
than hard-deleted.

Templates in this table belong to the Sales Engine. They are not FikaTu notification templates.
Sprint 6 will map approved Sales Engine output into the FikaTu event payload.

### Variable contract

Variables use `{{variable_name}}`. Sprint 4 validates declarations and syntax; Sprint 5 renders
them.

Allowed lead variables:

- `business_name`
- `sector`
- `area`
- `website_status`
- `has_website`

Allowed offer variables:

- `offer_name`
- `price_range`
- `pitch_angle`

Required campaign-purpose variable:

- `opt_out`

Every active template must include `{{opt_out}}`. Unknown or malformed variables are rejected
with a specific error naming the problem. A template cannot include phone numbers, email
addresses or other raw contact values in its body.

The original CSV's five-line opening-message pattern is the copy-quality reference, not a hard
database constraint. Anne owns the approved copy pack.

## API contract

All endpoints require authentication.

### Offers

- `GET /api/v1/offers` — active offers; admins may request inactive rows.
- `POST /api/v1/offers` — admin only.
- `PATCH /api/v1/offers/{id}` — admin only; supports edits and deactivation.

### Templates

- `GET /api/v1/templates?offer_id=&channel=&include_inactive=` — active templates whose parent
  offer is active; admins may request inactive rows.
- `POST /api/v1/templates` — admin only.
- `PATCH /api/v1/templates/{id}` — admin only; supports edits and deactivation.

There is no delete endpoint in Sprint 4.

Expected failures:

| Case | Response |
|---|---|
| Missing or invalid session | `401` |
| Sales user attempts a write | `403` |
| Unknown offer/template | `404` |
| Duplicate offer slug or template variant | `409` with the conflicting field |
| Invalid price range, channel, variable or required field | `422` with a readable reason |

## UI

Add a **Catalog** section to the authenticated navigation:

- **Offers** — responsive cards on mobile and desktop.
- **Templates** — filterable offer/channel list with responsive cards.

Admins get create/edit/deactivate controls. Sales users see active catalogue data without write
controls.

The template editor shows:

- offer and channel;
- name and variant;
- plain-text body;
- detected variables;
- allowed-variable reference;
- validation errors before save;
- active/inactive state.

The UI follows the current Wadi system and uses cards for mobile lists. No horizontal-scrolling
list is required.

## Copy pack

Anne prepares:

- no-website variants A and B for SMS;
- no-website variants A and B for email;
- one social-only variation;
- approved price phrasing and a direct question;
- channel-appropriate opt-out wording;
- factual claims limited to information recorded on the lead.

Each variant stays under the channel limit and includes `{{opt_out}}`.

## Seed data

Provide an idempotent catalogue seed command separate from demo lead seeding. It installs the
four offers, Starter Website at KES 40,000, and the implemented safe starter SMS/email
templates only when their keys do not already exist. It never rewrites an edited record.

The shipped seed contains one SMS A and one email A template. The full A/B, social-only, price
phrasing, channel-length and final opt-out copy pack remains an accepted carry-forward into
Sprint 5 before a real campaign.

## Work split

| Person | Piece |
|---|---|
| Sharon | Models, `0005` migration, repositories/services, APIs, validation and tests |
| Herman | Catalog navigation, responsive offer/template screens and admin/sales states |
| Anne | Offer copy guidance, template variants and opt-out language |
| Mark | Architecture/security review, migration review and integration checks |

Mark remains reviewer rather than owner of the entire backend.

## Acceptance criteria

- Admin can create, edit and deactivate an offer through the UI and API.
- Admin can create, edit and deactivate an email or SMS template.
- Sales can read active offers/templates but receives `403` on every write.
- Inactive records remain readable by admins and are excluded from Sales results.
- Duplicate slugs and duplicate offer/channel/variant combinations are rejected clearly.
- Invalid price ranges and malformed template variables are rejected.
- Every active template includes `{{opt_out}}`.
- The four initial offers and approved starter templates can be installed idempotently.
- A record edited through the UI is never overwritten by rerunning the catalogue seed.
- Mobile lists use cards with no horizontal page overflow.
- Existing lead, import, compliance and authentication behaviour remains unchanged.

## Closeout reconciliation

- The original desktop-table expectation is superseded by responsive cards on all screen sizes.
- Template query filtering now uses the implemented `include_inactive` parameter.
- Raw phone numbers and email addresses are rejected in template bodies.
- Sales template results exclude active templates whose parent offer is inactive.
- Automated UI coverage now exercises Admin create/deactivate and Sales read-only workflows.
- The complete limitation register and future ownership are in the
  [Sprint 4 exit review](../homework/sprint-4/status.md).

## Demo

From a clean clone:

1. Sign in as an admin.
2. Open Catalog → Offers and view the four offers.
3. Create one temporary offer and deactivate it.
4. Open Catalog → Templates, create an SMS template with a known variable and
   `{{opt_out}}`.
5. Confirm an unknown variable is rejected.
6. Sign in as Sales and confirm active records are readable and write controls are absent.
7. Confirm a direct Sales write request returns `403`.
8. Repeat the mobile card check at 390px and desktop table check at 1440px.

## Out of scope

- campaigns, segments, drafts or rendered messages;
- approval queues or sending;
- FikaTu templates, payloads or delivery;
- AI-authored copy;
- template version history;
- WhatsApp delivery;
- analytics by offer or variant;
- public catalogue pages, billing, quotations or e-commerce.

Sprint 5 snapshots each rendered draft, so later template edits cannot alter historical
outreach.

## Confirmed decisions

1. **Permissions:** `admin` manages the catalogue; `sales` has read-only access to active
   offers and templates.
2. **Prices:** Starter Website is KES 40,000. Business and Custom website guidance remains
   open.
3. **Discovery-first offers:** both price fields may be blank when the approved copy avoids
   making a price claim.
4. **Currency:** the API accepts uppercase three-letter currency codes; KES remains the
   default.
5. **Navigation:** Sales users see Catalog in read-only mode.

## Manual acceptance

Use [the Sprint 4 test guide](../homework/sprint-4/README.md). Campaigns, drafts, sending and
FikaTu remain outside this sprint.
