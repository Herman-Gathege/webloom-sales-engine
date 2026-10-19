# Herman — Sprint 2

> **Branch:** `sprint/2-lead-desk` · **Status:** done — merged in PR #20. Mark is next.
> The hand-off steps are in [the homework guide](../../README.md).
> The stretch piece — the import screen, with upload, progress and the refused-rows report —
> is on this branch too, in PR #21.

> **Where we are:** the shell you built shows eight invented leads from Sharon's API.
> **Your piece this sprint:** make that list answer a seller's questions.
> Nothing here needs you before Friday — start when you are back.

## Your mission

Let a seller narrow 52 businesses down to the ones worth a message.

## What to do

- Add filters to the Lead List: sector, area, website status, and status. Use the values that are
  actually in the data — do not invent categories.
- Add a search box that matches business name, phone, and area.
- Keep the filters in the URL, so a filtered list can be pasted into the group chat.
- Keep the current look. This is the same table with a row of controls above it — not a redesign.
- If the filters land early and you have a spare evening, the next piece is the import screen:
  upload a CSV, show progress, and offer the rejected-rows report. **Do not start it until
  Sharon's endpoint shape is merged** — otherwise you are guessing at what to call.

Do not try to finish the frontend, and do not rebuild the table.

## Done means

- Filtering by sector or website status changes the list, and it is obvious which filter is on.
- Search finds a business by name and by area.
- A filtered URL, pasted into a fresh tab, shows the same filtered list.
- The PR is small enough to review over a coffee.

## Bring back

- Your pull request.
- A screenshot of the list with two or three filters applied.
- The one thing the API does not give you yet, written as a request to Sharon.
