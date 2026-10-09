# Anne — Epic 1

> **Status: ready to pick up, and the data is real now.** The screens exist and Sharon's API
> is merged, so the app can show actual rows from the database instead of invented ones. The
> businesses are still synthetic — nothing here is a real contact. Work on branch
> `docs/epic-1-seller-review`.

## Your mission

Be the salesperson for a day, and make the first slice make sense to them.

## What to do

- Run the app and use it as a seller, not as a developer: open the list, spot a lead, open
  it. Ask Mark if you cannot start it — do not spend your evening debugging Docker.
- Write the simplest seller journey for this slice, in your own words. Three or four steps.
- List what the **Lead List** has to show, and what the **Lead Detail** has to show. The few
  things that matter, not everything.
- Give 3–5 concrete recommendations: what is confusing, what is missing, what is noise.
- Land one realistic "good lead" in `backend/app/seed/sample_data.py`, so the demo opens on a
  lead a seller would recognise. Synthetic name and phone number only — never a real contact.

Keep it practical. No big spec, no long report, no architecture unless you want to.

## Done means

- [ ] The seller journey is written down and clear.
- [ ] You have listed what the Lead List must show.
- [ ] You have listed what the Lead Detail must show.
- [ ] You have 3–5 concrete recommendations.
- [ ] Your example lead is in the seed data and shows up in the app.

## Bring back

- Your pull request on `docs/epic-1-seller-review`.
- Short notes on the journey and the screens.
- Your example lead.
- Your feedback on the first UI.
