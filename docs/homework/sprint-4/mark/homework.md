# Mark — Sprint 4

## Start here

Open [workflow.html](../../../workflow.html), then read
[workflow-description.md](../../../workflow-description.md). Skim the
[full Wadi guide](../../../full-wadi-documentation.md) for architecture and gaps. Focus on where
the current boundary stops before campaign and send work.

## Your mission

Review the catalogue boundaries, migration and authorization before release.

## What to do

- Review the `0005` upgrade and downgrade.
- Confirm Sales cannot write through direct API calls.
- Check slug, currency, price and template constraints.
- Review the seed for idempotence and accidental overwrites.
- Identify only issues that would block Sprint 5.

## Done means

- [ ] Migration round-trips.
- [ ] API authorization is enforced.
- [ ] Constraints reject malformed data.
- [ ] Seed reruns preserve edits.
- [ ] Remaining risks are recorded.

## Bring back

A short approval or findings list with severity and evidence.
