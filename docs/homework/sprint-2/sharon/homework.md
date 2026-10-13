# Sharon — Sprint 2

> **Where we are:** your Sprint 1 API is live and the app reads it. The eight leads it returns
> are invented. **Your piece this sprint:** make the real list go in.

## Your mission

Import the real 52-business list, and tell us exactly what it refused and why.

## What to do

- Add one importer endpoint that takes the list as it is — the 16 columns you already have —
  validates every row, and saves the good ones.
- Map the free-text `Sector` and `Website status` columns into structured fields. Where a value
  does not map, report it — do not guess and do not silently drop the row.
- Detect duplicate phone numbers and report them. Never create two leads with the same number.
- Flag landline-only rows as call-only.
- Return a summary a person can act on: how many rows were accepted, how many rejected, and one
  reason per rejected row. **Good rows import even when other rows are rejected.**
- Keep `reviews_count`, `social_presence` and `consent_basis` as a question for the group — they
  are in the real list but not in the database yet. Raise it in your PR rather than deciding it.

Do not build campaigns, messaging, qualification, or the whole data model. Just the importer.

## Done means

- The 52-row list imports, and the accepted + rejected counts add up to the rows in the file.
- Every rejected row has a reason a person can understand.
- Tests cover a duplicate, an unmappable sector, and a good row sitting next to a bad one.
- The endpoint is documented well enough for Herman to build the upload screen against it.

## Bring back

- Your pull request.
- The endpoint, plus one example request and response.
- The rejected-rows output for the real list.
- The exact shape Herman's screen should call — he is waiting on it.
