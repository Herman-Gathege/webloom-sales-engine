# Sharon — Epic 1

## Your mission

Make a real Lead travel from the database to the API.

## What to do

- Create the smallest Lead model that fits the fields we agreed.
- Write the migration and make sure it runs on a clean database, and can be reversed.
- Build the basic Lead API: list leads, and get one lead by id.
- Add a small amount of seed data — a handful of realistic sample leads, no real contacts.
- Add a tiny activity/history per lead — a couple of entries the UI renders on the detail screen.
- Add focused tests for the endpoints.
- Keep the response simple and frontend-friendly.

The exact field names and shapes are already agreed — build against
`docs/delivery/epic-1-lead-contract.md`, don't invent a different shape.

Do not build campaigns, messaging, qualification, or the whole data model. Just the Lead.

## Done means

- [ ] The database starts.
- [ ] The migration runs.
- [ ] Lead exists.
- [ ] The API returns leads, and one lead by id.
- [ ] Each lead has a little activity/history behind it.
- [ ] Tests pass.
- [ ] Herman has an example response he can connect to.

## Bring back

- Your pull request.
- The API endpoint.
- An example response.
- Anything Herman needs to connect the frontend.
