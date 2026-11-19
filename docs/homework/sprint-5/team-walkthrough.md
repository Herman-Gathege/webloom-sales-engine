# Sprint 5 — All-Team System Walkthrough

## 1. Purpose

Every team member runs Wadi end to end as an administrator and as a salesperson, then
follows one synthetic lead from import to a "Not sent" draft. The point is shared
understanding, not documentation.

## 2. Prerequisites and safe setup

```bash
docker compose up --build
```

Open `http://localhost:5174`. First run is slow (~8 min). Then create accounts:

```bash
BOOTSTRAP_ADMIN_PASSWORD='choose-a-temporary-password' \
  docker compose run --rm -e BOOTSTRAP_ADMIN_PASSWORD api python -m app.bootstrap
```

Seed the catalogue:

```bash
docker compose exec api python -m app.catalog_seed
```

Test commands to keep green:

```bash
docker compose run --rm api-test
cd frontend && npm run lint && npm run build && npm test
```

Rules: fictional records only. Never use real prospect data. Never send messages. Never
weaken compliance or auth. Never delete existing user data.

## 3. Part A — Administrator walkthrough

Sign in with an admin account. Change the temporary password when prompted.

- [ ] First login + forced password change (≥8 chars, not reused).
- [ ] Note navigation: Lead Desk, Campaigns, Catalogue (Offers/Templates), Users (admin only).
- [ ] Lead Desk: search, 13+ filters, pagination (25/page), "Add lead", CSV import link.
- [ ] Open a lead → contacts, provenance, compliance panel, activity timeline.
- [ ] Create one researched lead manually (Add lead dialog).
- [ ] Import `backend/tests/fixtures/campaign_readiness.csv` via `/leads/import`.
- [ ] Read accepted/refused/review counts and row-level reasons. Download refused rows.
- [ ] Use filters, search, pagination on the imported set.
- [ ] Inspect provenance + contact details on an imported lead.
- [ ] Open compliance panel: channel eligibility, suppression, exception review.
- [ ] Open catalogue: offers, prices, templates, variables.
- [ ] Edit or create catalogue info (admin only).
- [ ] Note what admin can do that sales cannot: catalogue writes, include inactive, users.

## 4. Part B — Salesperson walkthrough

Sign out, sign in with a sales account.

- [ ] Navigation shows no Users section; catalogue is read-only.
- [ ] Lead Desk + filters work; manual lead creation works; CSV import works.
- [ ] Lead details, provenance, activity visible; contact details visible.
- [ ] Compliance explanations readable; understand what makes a lead suitable per channel.
- [ ] Browse offers and templates (read-only).
- [ ] Select leads for a campaign (≤200).
- [ ] Preview eligibility; read skipped leads and reasons.
- [ ] Generate drafts; confirm they are labelled "Not sent".
- [ ] Archive and restore a campaign.
- [ ] Confirm sales cannot perform admin catalogue writes (API returns 403).

## 5. Part C — One synthetic lead through the whole workflow

Use a business from `campaign_readiness.csv` (e.g. "Synthetic Wadi Bakery").

```
Lead discovery
  ↓
CSV import
  ↓
Contact normalization + provenance
  ↓
Compliance evaluation
  ↓
Policy or human eligibility decision
  ↓
Outreach readiness check
  ↓
Offer + template selection
  ↓
Campaign lead selection
  ↓
Eligibility preview
  ↓
Draft generation
  ↓
Human review — future
  ↓
Fika Tu delivery — future
  ↓
Reply monitoring + handoff — future
```

Learn: Wadi automates evaluation, preview, generation. The salesperson decides channel fit.
Admin controls catalogue and users. Not yet implemented: approval, sending, replies.

Key rules: public visibility ≠ eligibility. Eligibility ≠ approval. A draft ≠ approved message.
A draft ≠ sent message. Suppression is terminal. Fika Tu is separate delivery infrastructure.
Wadi stops before approval and sending.

## 6. Expected outcomes and checks

- Both admin and sales experiences tested by everyone.
- At least one campaign previewed and one "Not sent" draft generated.
- Archive/restore exercised.
- No messages sent; no real data used.

## 7. Reflection (keep short)

Each person records: what worked, what failed, what was confusing, one improvement worth
considering, any blocker before moving forward.

## 8. Completion criteria

- [ ] Admin walkthrough completed.
- [ ] Sales walkthrough completed.
- [ ] Campaign workflow tested (preview + generate + archive/restore).
- [ ] Findings submitted.
- [ ] Blockers resolved or accepted.

Record status in [status.md](status.md). Do not mark anyone complete on their behalf.
