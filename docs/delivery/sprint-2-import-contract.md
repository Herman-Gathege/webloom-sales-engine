# Sprint 2 — CSV import contract

**Status:** implemented for Sprint 2, extended by the 2026-10-21 compliance foundation and the
2026-10-27 Sprint 3 solidification.
This document and `frontend/src/api/types.ts` move together — the same rule
[the Sprint 1 contract](sprint-1-lead-contract.md) set for the Lead shape. The compliance
boundary and operating workflow are in [`docs/compliance/`](../compliance/README.md).

The screen is `frontend/src/routes/LeadImport.tsx`; its types are in
`frontend/src/api/types.ts`.

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

**Sprint 2 baseline:** this endpoint had no authentication yet. Sprint 3 now requires a valid
`admin` or `sales` session for every lead endpoint; this statement is retained to describe the
original contract accurately.

## What the file must contain

The research list keeps its 16 existing columns and may add the optional compliance columns
listed below. Extra columns are ignored, so a later list can carry more.

The required columns are `Business`, `Sector`, `Area`, `Phone`, `WhatsApp capable`,
`Website status` and `Source`. A file missing any of them is refused whole with a `400` that
names them.

Optional provenance columns are `Email`, `Contact name`, `Contact type`, `Source URL`,
`Collection date`, `Collection method`, and `Intended purpose`. Their absence never refuses an
otherwise valid lead; it leaves all channels in `needs_review`. `Date added` is the fallback
for collection date and the written `Source` is the fallback for collection method.

`Opening message` and the remaining unused columns are still not stored.

## What each row becomes

| Column | Becomes | Rule |
|---|---|---|
| `Business` | `business_name` | Trimmed and repeated whitespace collapsed. Empty is a refusal. |
| `Phone` | `phone` | `0NNN NNNNNN` → `+254…`; `020 NNNNNNN` → `+25420…`; an existing `+254…` is kept. Anything else is a refusal — this is the de-duplication key, so it is never guessed at. |
| `WhatsApp capable` | `whatsapp_capable` | `Yes` → true, `Call only` → false. Any other value is reported and worked out from the number instead. |
| `Website status` | `website_status` | The raw string, verbatim, exactly as Sprint 1's contract promises. |
| `Website status` | `has_website` | `no website` / `New listing` / `Facebook page only` / `Instagram only` → false; `has a website` / `http` / `www.` → true; anything else is reported and left false. |
| `Source` | `source` plus provenance `source_name` | `Google Maps listing` → `source=google_maps` while the supplied text is preserved as `source_name`. An unknown value is slugified and reported. Empty is a refusal. |
| `Sector` | `sector` | Trimmed and whitespace-collapsed. There is no controlled vocabulary this sprint — Sprint 1's contract defers it — so no sector value is reported or rewritten. |
| `Area` | `area` | Trimmed and whitespace-collapsed; empty becomes `null`. |
| `Email` | `email` | Lower-cased when valid; malformed values are left blank with a warning. |
| `Contact name` | provenance `contact_name` | Optional named person, where research identified one. |
| `Contact type` | provenance `contact_type` | `generic_business`, `named_individual`, or `unknown`. |
| `Source URL` | provenance `source_url` | An `http` or `https` reference to the researched listing. |
| `Collection date` | provenance `collection_date` | ISO `YYYY-MM-DD`; falls back to `Date added`. |
| `Collection method` | provenance `collection_method` | How the source was researched; falls back to written `Source`. |
| `Intended purpose` | provenance `intended_purpose` | Why the contact was collected; empty stays unknown. |

Every imported lead is `status: "new"`, gets an `import_batches` row and row-numbered
provenance, starts `needs_review` independently for email, SMS, and WhatsApp, and is
immediately passed through the automatic compliance evaluator. It gets the same two timeline
entries a seeded lead gets: `lead.created` ("Imported from the Google Maps list") and
`lead.researched` with the research string.

**A landline is never WhatsApp-capable.** `020 NNNNNNN` in the list is `+2542…` once
normalised (and `041`, `043` and the other fixed-line ranges behave the same way), so
`whatsapp_capable` is false for those rows whatever the column says — and a column that
disagrees is reported rather than believed.

## The response

`200`, always, whenever the file could be read — even if every row was refused.

```json
{
  "filename": "webloom-lead-list.csv",
  "batch_id": "3f7b0ee2-c3c1-4a02-a8a5-c773f9c24e29",
  "row_count": 52,
  "created": 50,
  "accepted": 50,
  "rejected": 2,
  "matched": 1,
  "duplicates": 1,
  "eligible": 0,
  "needs_review": 48,
  "blocked": 1,
  "invalid": 3,
  "provenance_incomplete": 4,
  "requiring_review": 48,
  "rejected_rows": [
    {
      "row": 7,
      "business_name": "Mwangaza Hardware",
      "code": "duplicate_phone",
      "reason": "This phone number is already on row 3 of the file."
    }
  ],
  "review_rows": [
    {
      "row": 4,
      "business_name": "Synthetic Review Business",
      "compliance_status": "needs_review",
      "reason_codes": ["human_review_required:email"],
      "explanation": "Needs review: email requires a human decision before outreach."
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
- `created` equals `accepted`; it is explicit for screens that distinguish a new lead from an
  existing match.
- `matched` counts rows whose normalised phone already exists. They are not overwritten and
  also appear in `duplicates` for compatibility.
- `duplicates` remains the count of all `duplicate_phone` refusals, whether the match was in
  the upload or the system.
- `eligible`, `needs_review`, `blocked`, and `invalid` are calculated from the saved
  compliance snapshots after automatic evaluation. `blocked` and `invalid` also include
  suppressed/validation rows refused before a lead was saved.
- `review_rows` explains every saved non-eligible lead by CSV row.
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
| `suppressed_contact` | an all-marketing restriction already names the phone or email | This contact has opted out of marketing and is excluded from future imports. |

A row with more than one problem reports the same one every time: business name, then phone,
then source.

### Warnings

| `code` | `field` | `message` |
|---|---|---|
| `whatsapp_value_unrecognised` | `whatsapp_capable` | Not a value we recognise, so it was taken from the phone number instead. |
| `landline_marked_whatsapp` | `whatsapp_capable` | A landline cannot receive WhatsApp, so it is marked not WhatsApp-capable. |
| `website_status_unclassified` | `website_status` | Website status kept as written; has_website left false. |
| `source_unrecognised` | `source` | Source not recognised; stored as a lowercase slug of the value. |
| `email_invalid` | `email` | Email was not understood, so it was left blank and needs review. |
| `source_url_invalid` | `source_url` | Source URL was not an `http(s)` address, so it was left blank. |
| `collection_date_invalid` | `collection_date` | Collection date was not an ISO date, so it was left blank. |
| `contact_type_unrecognised` | `contact_type` | Contact type was not recognised, so it was recorded as unknown. |
| `contact_name_too_long` | `contact_name` | Contact name was longer than 255 characters, so it was left blank. |

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
Two leads can never share a phone number. If a lead is deleted and the same all-marketing
contact is imported later, the row is refused as `suppressed_contact`; channel-specific
suppression rows survive through their contact fingerprints.

## Calling it from the screen

```ts
const body = new FormData();
body.append("file", csvFile);                  // the File from the <input type="file">

const response = await fetch("/api/v1/leads/import", {
  method: "POST",
  body,
  headers: { Authorization: `Bearer ${sessionToken}` },
});
const summary = await response.json();         // the shape above
```

For the download, post the same `body` to `/api/v1/leads/import?format=csv` and save the
response blob. `row_count` is the number to show as "52 rows read"; `accepted` and `rejected`
are the headline, and `rejected_rows` is the list a person works through.

## Decisions and remaining open items

The original importer shipped before these were settled. The current status is recorded here
without erasing that history:

1. **Resolved 2026-10-21 — basis and `source_url`.** Imports capture traceable source fields
   when supplied. They never infer consent or eligibility; every channel starts in
   `needs_review` until a human records the applicable basis and evidence.
2. **`reviews_count` and `social_presence`.** Derivable from `Website status` — for example
   `3,713 reviews - no website listed` — but there is no column for either.
3. **`Opening message`.** A finished, ready-to-send draft on every row, and the quality bar for
   the first template in Sprint 4. No column, and it is not stored.
4. **Resolved 2026-10-21 — independent channel eligibility.** Email, SMS, and WhatsApp now
   have separate review records. Landline contacts cannot be approved for WhatsApp solely from
   the research column; review and eventual dispatch must also check technical availability.

The importer originally added no columns and no migration; that historical statement was
superseded by the compliance migration on 2026-10-21. Sprint 3 now supplies the authentication
required by the endpoint and limits lead access to `admin` and `sales`.
