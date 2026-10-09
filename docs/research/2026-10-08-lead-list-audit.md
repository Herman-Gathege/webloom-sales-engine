# Lead List Audit — first webloom lead list

**Date:** 2026-10-08
**Analyst:** Herman Gathege (via Codex)
**Source file:** `data/webloom-lead-list.csv` (gitignored — contains real business contact details)
**Rows:** 52 (53 lines including header)

This audit exists to shape the CSV importer, the lead schema, and the first pilot campaign.
No contact details are reproduced here; only structure and counts.

## 1. Current columns

`Date added`, `Business`, `Sector`, `Area`, `Phone`, `WhatsApp capable`, `Website status`,
`Opening message`, `Source`, `First touch date`, `Channel`, `Reply received`, `Outcome`,
`Follow-up date`, `Owner`, `Notes`

## 2. Completeness

Populated: the first nine columns (header through `Source`) are complete for all 52 rows.

Empty for all 52 rows: `First touch date`, `Channel`, `Reply received`, `Outcome`,
`Follow-up date`, `Owner`, `Notes`.

**Read this as:** the list is a lead *inventory*, not a campaign. Nothing has been
contacted yet. That is good news — the pilot starts clean, and every outcome is ours to
record properly from the first touch.

## 3. Sector mix

| Sector (as written) | Leads |
|---|---|
| Hardware, electrical and security suppliers | 11 |
| Opticians and eyewear | 10 |
| Agrovets and agri-input suppliers | 9 |
| Clinics, dental and medical centres | 7 |
| Logistics, freight and removals | 4 |
| Veterinary clinics | 3 |
| Pharmacies and chemists | 3 |
| Property and professional services | 3 |
| Printing and branding | 2 |

Nine sectors over 52 leads is roughly six leads per sector. That is enough to *start*
learning sector-level conversion, not enough to conclude anything from a single campaign.
The importer should treat `Sector` as free text now and normalise it into a controlled
vocabulary in a later block.

## 4. Data quality findings

1. **Phone formats are consistent but split into two kinds.** 46 mobile numbers in
   `0NNN NNNNNN` format and 6 Nairobi landlines in `020 NNNNNNN` format. All six landlines
   are already correctly marked `Call only`, so the WhatsApp flag is trustworthy in this
   list. The importer must normalise to E.164 (`+254…`) and keep the original string.
2. **No duplicate phone numbers.** De-duplication on normalised phone is safe as the
   primary identity key for import, with business name as a secondary check.
3. **`Website status` is free text with 37 distinct values** (for example "3,713 reviews -
   no website listed", "23 reviews - Facebook page only"). This is genuinely useful
   research, but it cannot be filtered or reported on as-is. Split it into structured
   fields: `reviews_count` (integer), `has_website` (bool), `social_presence` (enum:
   `none` / `facebook_only` / `instagram_only` / `other`), and keep the raw string as a
   source note.
4. **Three leads already have a social presence** (one Facebook-only, one Instagram-only,
   plus one more with a partial presence). These need a different pitch from "you have
   nothing online" — the opening message for them should be about consolidating, not
   creating.
5. **All 52 leads come from one source: Google Maps listing.** The strategy puts weight on
   referrals and warm introductions converting far better than cold outreach, and today the
   engine has *zero* warm leads to compare against. The `Source` field must exist from day
   one so that the first referral lead is measured properly rather than mixed in.
6. **No link back to the source listing.** Without the Google Maps URL, a researcher cannot
   re-verify a lead's details later. Add a `source_url` field.
7. **No consent/provenance field.** The scope spec requires the basis on which we hold each
   contact. Public-listing acquisition should be recorded per lead, not assumed.
8. **No email column.** Only phone and WhatsApp are available. This confirms §11 of the
   scope spec: the first pilot should be SMS or WhatsApp, not email, unless we enrich the
   list.
9. **`Opening message` is a full, ready-to-send draft** averaging ~408 characters, with a
   consistent five-line structure (greeting + proof point + problem + offer + question).
   That structure is worth preserving as a template pattern: it is effectively the first
   message template, and its variables are business name, review count, and area.

## 5. Consequences for the build

| Finding | What it changes |
|---|---|
| Free-text sector and website status | The importer must accept free text and map it into structured columns, with an unmapped-value report |
| Landlines mixed with mobiles | Channel eligibility must be computed per lead, not per campaign |
| No email addresses | Pilot channel decision (scope §11 Q1) will be SMS/WhatsApp, not email |
| Social-only leads | Template variants are needed for the pilot, not a single template |
| No warm/referral leads yet | Anne should add a handful of referral leads before the pilot so the comparison has two sides |
| No source URL or consent basis | Two extra fields in the `leads` table from the first migration |
| Raw opening messages are high quality | Use them as the seed content for the first template and as the quality bar for generated drafts |

## 6. Recommended immediate actions

1. Add 5-10 referral or warm-introduction leads (Anne) so the pilot measures both sources.
2. Decide the pilot channel: SMS or WhatsApp, given there are no email addresses
   (Anne + Herman).
3. Extend the list with `source_url`, `reviews_count`, `has_website`, `social_presence`,
   and `consent_basis` before or during import (Herman).
4. Preserve `Opening message` verbatim in the import as the first draft, and use it to
   validate that the template renderer reproduces it (Sharon, in a later block).
