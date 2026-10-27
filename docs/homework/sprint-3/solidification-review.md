# Sprint 3 solidification review

Use this alongside the auth review in [README.md](README.md). This pass checks the
CSV-to-outreach-boundary slice described in
[Sprint 3 solidification](../../delivery/sprint-3-solidification.md).

## Demo

1. Start from a clean checkout with `docker compose up --build`.
2. Sign in with a bootstrapped `admin` or `sales` account and complete the forced password
   change if prompted.
3. Import a synthetic CSV with one clean row, one malformed row, one duplicate inside the
   file, and one row with no useful source evidence.
4. Confirm created, matched, duplicate, rejected, eligible, needs-review, blocked, invalid,
   and provenance-incomplete counts match the records actually saved.
5. Follow the import links into the Lead Desk. Combine `compliance_status` with sector, area,
   batch, source, provenance, and outreach readiness; change sort and page through results.
6. Open a needs-review lead. Confirm the row and detail both explain why outreach is blocked.
7. Record a lawful basis and evidence for one technically available channel. Confirm the lead
   becomes eligible only for that channel.
8. Change the contact or provenance through a test fixture/API update, recheck outreach, and
   confirm the old decision is visible but stale and the gate refuses it.
9. Record an objection or all-marketing opt-out. Confirm the effective channel state becomes
   blocked and the outreach gate refuses it.
10. Try the individual and bulk outreach-check endpoints with allowed and blocked leads.

Never use real customer contact details in the demo.

## Checks

```bash
docker compose build api
docker compose run --rm api-test

cd frontend
npm run lint
npm test
npm run build
```

The reviewer should also inspect:

- `0004` upgrade, downgrade, and upgrade again against a disposable test database;
- filtered `total` values, not only visible rows;
- the absence of raw contact details in audit JSON and import reports;
- the honest statement that queueing, sending, FikaTu, and automatic inbound opt-out handling
  remain Sprint 5–6 work.

## Review questions

- Can any path make a `needs_review`, `blocked`, or `invalid` lead pass an outreach check?
- Can a channel-specific suppression incorrectly hide a different eligible channel?
- Does an unchanged lead reuse its evaluation without adding duplicate audit entries?
- Does a changed contact or source invalidate the prior approval without deleting history?
- Do source, compliance, and data-quality filters operate before count and pagination?
- Are the status names and operator explanations understandable without reading the code?
- Are any assignment or temperature controls shown even though those fields do not exist?

## Follow-up owned by later sprints

- Connect the readiness gate to campaign generation, queueing, approval, dispatch, retries,
  and follow-ups.
- Add the FikaTu integration without teaching it sales eligibility.
- Add inbound reply processing that records replies and routes explicit objections into the
  existing terminal suppression model.
- Obtain the business/legal decisions listed in the compliance notes before relying on
  outreach at scale.
