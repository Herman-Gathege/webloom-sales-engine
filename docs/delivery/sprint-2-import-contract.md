# Sprint 2 — CSV import contract

**Status:** agreed for Sprint 2, and the shape the upload screen is built against. When that
screen lands, this document and its types move together in the same pull request — the same
rule [the Sprint 1 contract](sprint-1-lead-contract.md) set for the Lead shape.

The importer takes the researched list as it is, saves every good row, and hands back one
reason for every row it refuses. It imports the good rows even when other rows are refused,
because a row we cannot use must never cost us the rows beside it.

## The endpoint

`POST /api/v1/leads/import` — `multipart/form-data`, one part named `file` carrying the CSV.

| The file | |
|---|---|
| Encoding | UTF-8. A byte-order mark is tolerated; anything else is a `400`. |
| Format | Comma-separated, one header row. |
| Size | Up to 5 MB. Over that is a `413`. |
| Content type | Ignored — browsers send whatever they like for a `.csv`, so the bytes are what count. |

There is **no auth yet**, so contact details are not yet hidden from anyone who can reach the
API. Authentication and roles are Sprint 3; that is a known gap, not an oversight.

## What the file must contain

The research list with the 16 columns it already has, in the same order. Extra columns are
ignored, so a later list can carry more.

The columns read are `Business`, `Sector`, `Area`, `Phone`, `WhatsApp capable`,
`Website status` and `Source`. A file missing any of them is refused whole with a `400` that
names them.

`Date added`, `Opening message` and the last seven columns are not stored. Two of those are
deliberate open questions, listed at the end.

## What each row becomes

| Column | Becomes | Rule |
|---|---|---|
| `Business` | `business_name` | As written. Empty is a refusal. |
| `Phone` | `phone` | `0NNN NNNNNN` → `+254…`; `020 NNNNNNN` → `+25420…`; an existing `+254…` is kept. Anything else is a refusal — this is the de-duplication key, so it is never guessed at. |
| `WhatsApp capable` | `whatsapp_capable` | `Yes` → true, `Call only` → false. Any other value is reported and worked out from the number instead. |
| `Website status` | `website_status` | The raw string, verbatim, exactly as Sprint 1's contract promises. |
| `Website status` | `has_website` | `no website` / `New listing` / `Facebook page only` / `Instagram only` → false; `has a website` / `http` / `www.` → true; anything else is reported and left false. |
| `Source` | `source` | `Google Maps listing` → `google_maps`. An unknown value is turned into a lowercase slug and reported. Empty is a refusal. |
| `Sector` | `sector` | As written. There is no controlled vocabulary this sprint — Sprint 1's contract defers it — so no sector value is ever reported or rewritten. |
| `Area` | `area` | As written; empty becomes `null`. |

Every imported lead is `status: "new"`, and gets the same two timeline entries a seeded lead
gets: `lead.created` ("Imported from the Google Maps list") and `lead.researched` with the
research string.

**A landline is never WhatsApp-capable.** `020 NNNNNNN` in the list is `+2542…` once
normalised (and `041`, `043` and the other fixed-line ranges behave the same way), so
`whatsapp_capable` is false for those rows whatever the column says — and a column that
disagrees is reported rather than believed.

## The response

`200`, always, whenever the file could be read — even if every row was refused.

```json
{
  "filename": "webloom-lead-list.csv",
  "row_count": 52,
  "accepted": 50,
  "rejected": 2,
  "rejected_rows": [
    {
      "row": 7,
      "business_name": "Mwangaza Hardware",
      "code": "duplicate_phone",
      "reason": "This phone number is already on row 3 of the file."
    }
  ],
  "warnings": [
    {
      "row": 12,
      "field": "website_status",
      "value": "does not say",
      "code": "website_status_unclassified",
      "message": "Website status kept as written; has_website left false."
    }
  ]
}
```

- `row_count == accepted + rejected`, always. Every row in the file is either a lead or a
  refusal with a reason.
- `row` is the **physical line in the file**, with the header as line 1 — the number the
  person sees in Excel beside the row they have to fix.
- `warnings` never reduce `accepted`: a value we could not classify is kept as written and
  reported.
- **No phone number appears anywhere in the report.** The row number is enough to find it, and
  it keeps the report safe to paste into a group chat.

### Refusals

| `code` | When | `reason` a person reads |
|---|---|---|
| `blank_business_name` | `Business` is empty | The business name is empty. |
| `missing_phone` | `Phone` is empty | No phone number, so this lead cannot be contacted. |
| `unparseable_phone` | `Phone` is not a shape we know | The phone number is not in a format we can read (expected 0NNN NNNNNN or 020 NNNNNNN). |
| `duplicate_phone` | the number is already on an earlier row of the file | This phone number is already on row N of the file. |
| `duplicate_phone` | the number is already in the system | This phone number is already in the system. |
| `blank_source` | `Source` is empty | No source recorded, so we cannot say where this lead came from. |

A row with more than one problem reports the same one every time: business name, then phone,
then source.

### Warnings

| `code` | `field` | `message` |
|---|---|---|
| `whatsapp_value_unrecognised` | `whatsapp_capable` | Not a value we recognise, so it was taken from the phone number instead. |
| `landline_marked_whatsapp` | `whatsapp_capable` | A landline cannot receive WhatsApp, so it is marked not WhatsApp-capable. |
| `website_status_unclassified` | `website_status` | Website status kept as written; has_website left false. |
| `source_unrecognised` | `source` | Source not recognised; stored as a lowercase slug of the value. |

Every refusal and warning sentence above is written in one place in
`backend/app/services/lead_import.py`, so Anne can replace the wording without touching a rule.

## Downloading the refusals

The same request with `?format=csv` answers `text/csv` instead of JSON — the downloadable
error report scope §6.6 asks for, with no storage behind it:

```text
row,business_name,code,reason
7,Mwangaza Hardware,duplicate_phone,This phone number is already on row 3 of the file.
```

It is a `POST` that carries the file again, so the report describes that import. Two
consequences worth knowing in the screen: the same file must be sent in both calls, and asking
for the report a second time over the same file will refuse the rows that the first call
imported — because by then their numbers are in the system.

## Status codes

| Code | When |
|---|---|
| `200` | The file was read. Includes "all 52 rows were refused". |
| `400` | Not UTF-8, or no header row, or a column we read is missing (named in `detail`). |
| `413` | Bigger than 5 MB. |
| `422` | FastAPI refused the request itself: no `file` part, or `format` is neither `json` nor `csv`. |

## Importing the same file twice

It is safe, and it is how the guardrail is proven: the second import answers
`accepted: 0, rejected: 52`, every row `duplicate_phone`, and the lead count does not move.
Two leads can never share a phone number.

## Calling it from the screen

```ts
const body = new FormData();
body.append("file", csvFile);                  // the File from the <input type="file">

const response = await fetch("/api/v1/leads/import", { method: "POST", body });
const summary = await response.json();         // the shape above
```

For the download, post the same `body` to `/api/v1/leads/import?format=csv` and save the
response blob. `row_count` is the number to show as "52 rows read"; `accepted` and `rejected`
are the headline, and `rejected_rows` is the list a person works through.

## Open, and deliberately not decided here

The importer stores the raw `Website status` string, so nothing in the data is lost while these
wait. They are raised in the importer's pull request, and the real 52-row list is not imported
into the shared database until the team answers:

1. **`consent_basis` and `source_url`.** AGENTS.md non-negotiable 5 wants the basis on which we
   hold each contact recorded per lead, and Sprint 1's contract flags both fields as a decision
   to settle *before* real rows arrive. The list has neither column; the basis is the same for
   all 52 rows, and the source listing's URL was not captured.
2. **`reviews_count` and `social_presence`.** Derivable from `Website status` — for example
   `3,713 reviews - no website listed` — but there is no column for either.
3. **`Opening message`.** A finished, ready-to-send draft on every row, and the quality bar for
   the first template in Sprint 4. No column, and it is not stored.
4. **SMS eligibility for landlines.** `whatsapp_capable: false` is how a landline is marked
   call-only today. A fixed line cannot receive SMS either, and Sprint 6 needs a channel-
   eligibility field that says so; this sprint does not add one.

Not in this sprint either: filters and search on the lead list (Herman's card), any record of
import batches, role-gated contact details, and any change to the database schema — the
importer adds no columns and no migration.
