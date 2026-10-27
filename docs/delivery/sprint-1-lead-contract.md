# Sprint 1 — Lead API contract

**Status:** agreed for Sprint 1 (the first Lego piece) and frozen for that sprint. The
frontend is already built against it, so Sharon can implement the backend in parallel
without either side waiting.

The frontend's copy of this contract in code is
[`frontend/src/api/types.ts`](../../frontend/src/api/types.ts). **This document is the
source of truth** — if a field changes, change both in the same pull request.

This is a small subset of the long-term data model in
[scope spec §6.4](../superpowers/specs/2026-10-08-webloom-sales-engine-scope.md). Later
sprints extend it. It is not the final schema, and it is not a design for campaigns,
sending, or replies.

## The Lead shape

Field names are `snake_case` and match the JSON exactly, so there is never a mapping
layer to get out of step.

| Field | Type | Notes |
|---|---|---|
| `id` | string (uuid) | Primary key. |
| `business_name` | string | e.g. `"Optica (I&M Bank Tower, Corner House, Sarova Stanley)"`. |
| `sector` | string or null | Free text in Sprint 1, e.g. `"Opticians and eyewear"`. Normalised into a controlled vocabulary in a later sprint — do not build that now. |
| `area` | string or null | Free text, e.g. `"CBD and Westlands, 3 branches"`. |
| `phone` | string or null | E.164, e.g. `"+254709709000"`. Also the de-duplication key: the importer normalises the source's two formats (`0NNN NNNNNN` mobile and `020 NNNNNNN` landline). Null when a lead has no phone yet. |
| `email` | string or null | Lower-cased contact email added by the Sprint 2 compliance foundation. Never a de-duplication key by itself. |
| `whatsapp_capable` | boolean | False for landlines. Per-lead, never per-campaign — the source list marks all six landlines `Call only`. |
| `website_status` | string or null | The raw research string, kept verbatim, e.g. `"3,713 reviews - no website listed"`. The source list has 37 distinct values and we are not normalising it yet. |
| `has_website` | boolean | The "you have nothing online" pitch depends on this, so it is a real column, not a string match at read time. |
| `source` | string | Where the lead came from, e.g. `"google_maps"`, `"referral"`. A plain string in Sprint 1. Never blank — the learning analysis compares sources, and today all 52 leads come from one source. |
| `status` | string enum | One of the eleven values below. Every seeded lead is `"new"`. |
| `created_at` | datetime | ISO 8601, UTC. |
| `updated_at` | datetime | ISO 8601, UTC. |

`status` is one of: `new`, `contacted`, `replied`, `qualified`, `handed_off`,
`proposal`, `won`, `lost`, `no_response`, `not_interested`, `opted_out`.

These are the funnel stages and end states from
[scope spec §5.1](../superpowers/specs/2026-10-08-webloom-sales-engine-scope.md). In
In this sprint nothing moves a lead off `new`, because nothing sends yet. The long-term rule that
status is *derived from evidence* rather than typed by hand is not implemented in this
sprint — say so rather than pretending otherwise.

## The Activity shape

Activity is the append-only history shown under a lead. Sprint 1 has it so the demo can end
on "see basic activity/history"; it grows into the full audit feed (`activity_events` in
the scope spec) in later sprints.

| Field | Type | Notes |
|---|---|---|
| `id` | string (uuid) | Primary key. |
| `lead_id` | string (uuid) | The lead this belongs to. |
| `type` | string | Stable machine name, e.g. `"lead.created"`. The UI only uses it to pick an icon. |
| `actor` | string | `"system"` in Sprint 1. Becomes a real user id once login exists, in Sprint 3. |
| `summary` | string | One line a human reads, e.g. `"Imported from the Google Maps list"`. The UI renders this string. |
| `details` | object or null | Structured, non-sensitive audit facts. Never contains raw contact details or message bodies. |
| `created_at` | datetime | ISO 8601, UTC. The timeline is ordered by this. |

## The endpoints

The dev server proxies `/api` to the FastAPI service (see `frontend/vite.config.ts`), so
the frontend's default base URL is `/api/v1`. Set `VITE_API_BASE_URL` to point elsewhere.

### `GET /api/v1/leads?limit=50&offset=0`

```json
{ "items": [ /* Lead[] */ ], "total": 52, "limit": 50, "offset": 0 }
```

- `total` is the count **before** pagination, so the UI can say "52 in the pipeline".
- `limit` defaults to 50 and is capped at 200.
- `offset` defaults to 0.
- Order by `created_at` descending, so the newest leads are first and the list is stable.

### `GET /api/v1/leads/{id}`

```json
{
  "/* every Lead field above */": "",
  "provenance": { "/* source, collection, purpose, contact context */": "" },
  "eligibility": [ /* three independent channel decisions */ ],
  "suppressions": [ /* terminal restrictions; no fingerprints or raw contacts */ ],
  "activity": [ /* Activity[] */ ]
}
```

`activity` is oldest first, so the timeline reads top to bottom. It is `[]` when nothing
has happened yet — never null. `provenance` may be null for an older lead. `eligibility`
always represents email, SMS, and WhatsApp separately; `suppressions` may be empty.

### Compliance review endpoints

`PUT /api/v1/leads/{id}/eligibility/{channel}` records a human decision for one of
`email`, `sms`, or `whatsapp`. `eligible` requires lawful basis, evidence summary/source,
intended purpose, contact context, reviewer, and rationale. It returns the full Lead Detail.

`POST /api/v1/leads/{id}/suppressions` records a terminal `all_marketing`, `email`, `sms`, or
`whatsapp` restriction and returns the full Lead Detail. There is intentionally no removal
endpoint. Exact semantics are in the [compliance implementation notes](../compliance/implementation-notes.md).

### Errors

An unknown `{id}` returns `404` with body `{ "detail": "Lead not found" }`. A malformed id
that is not a uuid also returns `404`, not `500`.

## The sample-data fallback

This is part of the contract, not a frontend quirk, because it is what lets the two sides
build in parallel:

- `VITE_USE_MOCK=1` skips the API entirely and always uses the bundled fixtures.
- Otherwise the frontend calls the real API with a 4-second timeout. If the API is
  unreachable, it falls back to fixtures and **says so on screen** ("Sample data …"), so a
  demo never silently lies about which one you are looking at.
- A reachable API that answers `404` is **not** hidden behind sample data. A missing lead
  is a real result and the UI reports it.

So `GET /api/v1/leads` returning the shape above is enough for the screen to switch from
"Sample data" to "Live data" with no frontend change.

## What is deliberately not in this contract

Each of these is a later sprint, not an oversight:

- **Authentication and roles.** No auth exists in Sprint 1, so there is no `owner_id` and no
  user id on activity.
- **A contacts table.** One phone per lead for now. `lead_contact_points` arrives when
  multi-channel contacts matter.
- **The CSV importer.** Sprint 1 seeds a synthetic fixture. The importer arrived in Sprint 2
  and has its own document: [the Sprint 2 import contract](sprint-2-import-contract.md).
- **Campaigns, templates, outreach, replies, qualification.** All deferred.

## Original provenance gap — resolved in Sprint 2

`AGENTS.md` non-negotiable 5 says every lead must record the basis on which we hold its
contact details. This contract has **no `consent_basis`**, and no `source_url`, so a
researcher cannot re-find the listing a lead came from.

That did not bite in Sprint 1 because every seeded lead was synthetic. It was resolved on
2026-10-21 with separate provenance and channel-eligibility records rather than putting
evidence directly on the Lead. The historical concern is retained here because import,
contact, and eligibility remain distinct concepts.
