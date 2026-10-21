# Sprint 2 — the importer: what was built, and why it looks like this

**Written:** 2026-10-15 · **Owner:** Sharon · **Part of:** [Sprint 2](../homework/sprint-2/README.md)

This is the working note behind the importer. The shape a screen calls is in
[the import contract](sprint-2-import-contract.md) — that document is for Herman. This one is for
everyone else: what the piece does, the decisions inside it and the reasons for them, what was
checked and how, and what is still open. Read the contract instead if you only want to call it.

**Status:** built and verified, on two branches, open for review. Sprint 2 as a whole is not
finished — CI, the Lead List filters and Anne's seller's pass are other cards.

> **2026-10-21 compliance update.** The original importer described below deliberately shipped
> without batches or schema changes. Current code adds `import_batches`, lead provenance,
> optional provenance columns, independent channel review records, and terminal suppression.
> The historical explanation is retained to show why the first slice was intentionally small;
> the current contract is [the import contract](sprint-2-import-contract.md) and the
> [compliance implementation notes](../compliance/implementation-notes.md).

## What it does

One endpoint, `POST /api/v1/leads/import`, takes the researched list as it comes out of the
spreadsheet and turns it into leads:

```text
52-row CSV → read (UTF-8, 16 columns)
           → map each row (phone, landline, website status, source)
           → refuse the rows we cannot use, one reason each
           → de-duplicate on the phone number, inside the file and against the database
           → save every good row in one transaction, with the same two timeline entries a
             seeded lead gets
           → answer with accepted / rejected counts, the reasons, and the values we could not
             classify
```

The rule that matters most: **a row we cannot use never costs us the rows beside it.** Good rows
import while bad rows are refused, and the counts always add up to the rows in the file.

## The decisions inside it, and why

**A file upload, not rows of JSON.** The download-and-import path is "upload the CSV", so the
server reads the CSV. It keeps the knowledge of those 16 columns in one place instead of also
teaching the browser to parse them. The cost is one pinned dependency, `python-multipart`.

**The refusals come back in the response, and are not stored.** Scope §6.4 has an
`import_batches` table for CSV provenance, and it is the right long-term home — but its
`uploaded_by` field needs a users table, which is Sprint 3. The scope also requires a
*downloadable* error report, and `?format=csv` gives one from the same request with no storage
behind it. When the screen needs to look up an old import, that is the moment for the table.

**No schema change and no migration.** Sprint 1's Lead shape is frozen and two systems read it.
The list carries three things it has no column for — `reviews_count`, `social_presence`,
`consent_basis` — plus a finished `Opening message` on every row, and Sprint 1's contract says
the `consent_basis` decision has to be made by the team before real rows arrive. Rather than
decide a team question inside an importer, the raw strings are kept verbatim, nothing is lost,
and the question goes in the pull request. `test_migration.py` passing untouched is the proof
that the frozen shape did not move.

**`Sector` is stored exactly as written, and is never reported.** It is free text in the
contract, and the contract defers any controlled vocabulary to a later sprint. With no
vocabulary to check a value against there is no such thing as an unmapped sector — so a
whitelist of "known" sectors was deliberately *not* built, because that is the vocabulary under
another name, and it would report a perfectly good new sector as a problem.

**Unrecognised values import and are reported.** A `Website status` we cannot classify, a
`Source` nobody has seen, or a `WhatsApp capable` value that is not `Yes` or `Call only` are all
kept as written and listed in `warnings`. The alternative — refusing rows we do not fully
understand — would throw away real businesses over a spreadsheet cell.

**A landline is never WhatsApp-capable, whatever the column says.** The contract pins
`whatsapp_capable` to false for landlines, so the number wins over the cell, and a cell that
disagrees is reported rather than believed. The rule is by Kenyan area code (the first digit
after `+254` is 2–6), not just the `020` shape the list happens to use, so `041` and friends
behave the same way.

**Phone is the de-duplication key, so it is never guessed at.** `0NNN NNNNNN` and `020 NNNNNNN`
become E.164; anything else is refused with a reason. A repeat inside the file refuses the later
row and names the earlier one. A number already in the database is refused too, which is what
makes importing the same file twice a clean no-op rather than a mess of half-duplicates.

**Refusals are checked in a fixed order and the reasons carry stable codes.** A row with three
problems always reports the same one, so two imports of the same file produce the same report.
The code is for a screen to group or filter; the sentence beside it is for a person, and every
sentence lives in one table in `backend/app/services/lead_import.py` so Anne can rewrite the
wording without going near a rule.

**No phone number ever appears in the report.** The row number is enough to find the row in
Excel, and it keeps the report safe to paste into a group chat — which is where the pilot's
rejected rows are going to be discussed.

**Imported leads look like seeded leads.** Each gets `lead.created` and `lead.researched`, the
same two entries `app/seed/sample_data.py` writes, so the timeline is not a different shape
depending on how a lead arrived. Their timestamps are one second apart with the file's first row
newest, so the Lead List reads in the order the researcher wrote and an import is reproducible.

## How it is put together

| Where | What lives there |
|---|---|
| `backend/app/api/v1/leads.py` | the route: size cap, parse, delegate. No rules. |
| `backend/app/services/lead_import.py` | every rule — reading, mapping, validating, de-duplicating, saving, and the wording of every refusal and warning. 446 lines: 57 of docstring and 35 of comment, plus the wording tables. |
| `backend/app/schemas/lead_import.py` | the response models: `ImportSummary`, `RefusedRowRead`, `RowWarningRead`. |
| `backend/app/repositories/lead_repository.py` | two additions: one batch phone lookup (52 rows must not be 52 queries) and `commit()`. |
| `backend/tests/fixtures/` | six synthetic CSVs and a README against the trap below. |

The mapper helpers are plain functions at the top of the service module, so the tests call them
directly without a database or an HTTP request.

## What was verified, and how

| Claim | Evidence |
|---|---|
| The whole backend still works | 118 tests pass against PostgreSQL 17 and Python 3.12; ruff clean |
| The importer is covered | 84 of those tests are the importer's: 61 mapper/unit, 13 against the database, 10 through the endpoint |
| The real list imports | the actual `data/webloom-lead-list.csv`: **52 rows, 52 accepted, 0 refused, 0 warnings** |
| It maps what it claims | after that import: 9 sectors, 6 leads marked not-WhatsApp-capable (the six landlines), 52 phones in E.164 and none left local, 104 activity entries, every lead `source: google_maps`, every one `status: new` |
| A number cannot be imported twice | the same file again: **0 accepted, 52 refused, every one `duplicate_phone`**, lead count unchanged |
| Someone else can run it | `bash scripts/check_demo.sh` — 11 checks, including import → report → re-import |

The real list was imported into a throwaway container for that check and the container was
deleted afterwards. **The 52 real rows are not in any shared database**, and per the plan they
should not be until the team answers the open questions below.

## What is deliberately not here

Filters, search and pagination on the Lead List (Herman's card) · any record of import batches ·
authentication and role-gated contact details, so today anyone who can reach the API sees every
phone number (Sprint 3) · duplicating, editing or deleting a lead · sending, campaigns and the
other eleven screens. The importer adds no columns and no migration.

The final sentence records the original slice only. The compliance follow-up now adds the
tables and optional fields described above; sending and role gating remain out of scope.

## Open, and for the team to answer

These are in the pull request rather than decided in code, because they change a table two
systems read:

1. **`consent_basis` and `source_url`.** AGENTS.md non-negotiable 5 wants the basis on which we
   hold each contact recorded per lead. The list has no column for either, the basis is the same
   for all 52 rows, and the source listing's URL was never captured. Sprint 1's contract says
   this must be settled before real rows arrive — so it is the gate on importing the real list
   anywhere shared.
2. **`reviews_count` and `social_presence`.** Parseable from `Website status`
   (`3,713 reviews - no website listed`), no column to put them in.
3. **`Opening message`.** A finished, ready-to-send draft on every row, and the quality bar for
   Sprint 4's first template. Not stored.
4. **SMS eligibility for landlines.** `whatsapp_capable: false` is how call-only is marked
   today, and a fixed line cannot receive SMS either. Sprint 6 needs a field that says so.
5. **How many approvals this needs.** The importer touches no schema, so `how-we-work.md` asks
   for one, not the two Mark's card assumes — worth saying out loud before review starts.

## Traps worth remembering

**No test may read `data/`.** It is gitignored, so a test that reads the real list passes on the
machine that has the file and fails in CI. Every importer test uses the synthetic fixtures in
`backend/tests/fixtures/`, and that directory's README says so at the top.

**The CSV endpoint is an import, not a report.** Asking for `?format=csv` runs the import again,
so the report describes *that* call. This caught us once: the demo script's first version
checked the download after already importing the same file, so every row came back as a
duplicate and the expected line count was wrong. The check now expects that, and says why.

**One writer per file is not a formality.** This piece was built with assistant help, and two of
the agents involved edited files that were not theirs: one rewrote the service's mapping rules —
reinstating the sector whitelist that had already been ruled out, and letting a landline be
marked WhatsApp-capable because the spreadsheet said so — and one never delivered its documents
at all. What caught it was a single failing test on a warning code nobody had agreed to. The
rule that saved the work is the plain one: the coordinator reads every diff, and a fresh test
run is the arbiter, not a report of one.

## Where the work sits

Two branches, in order, so each can be reviewed on its own:

| Branch | What it carries | Tests |
|---|---|---|
| `feat/lead-importer-core` | the engine, the repository lookup, the fixtures, the 61 + 13 tests | 108 pass |
| `feat/lead-importer-endpoint` | the route, the response models, the 10 endpoint tests, this document, the contract, the demo step | 118 pass |

The second is branched off the first; open its pull request against the first branch and retarget
it to `main` once the first merges.
