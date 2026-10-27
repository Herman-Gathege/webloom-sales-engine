# Frontend

The React shell for Wadi. It has a login screen, the searchable Lead List, Lead Detail with
activity history and a practical compliance review card, the CSV import screen, and an
administrator-only user list.

## Signing in

Everything except `/login` needs a session. Tokens are stored in `localStorage` under
`wadi.token`; a 401 anywhere clears it and returns you to the login page. The four
development administrators are created by `python -m app.bootstrap` (see the backend README);
each must set its own password at first login, and the API refuses lead data until it does.

## Node version — read this first

**Use Node 22.** Vite 8 will not run on Node 21: it fails with a missing `rolldown`
native binding, which looks like a broken install but is just an unsupported version.
There is an `.nvmrc` here with the right version.

```bash
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh" && nvm use
```

## Run it

```bash
npm install
npm run dev      # http://localhost:5173
```

## Check it

```bash
npm run build    # typecheck + production build
npm run lint
npm test         # vitest, jsdom
```

## Where the data comes from

The backend exists, but until it answers this app also ships with synthetic sample leads
in `src/api/fixtures.ts` and shows a **"Sample data"** banner while it uses them.

It calls the real API first. The moment `GET /api/v1/leads` answers, the banner switches
to **"Live data"** and no frontend code changes. The dev server proxies `/api` to
`http://localhost:8001`, so there is no CORS to configure in development.

When the backend is running through the repo-root Docker Compose file, leave the proxy
target alone: the API is served on port 8001 by default. Override `VITE_API_PROXY_TARGET`
only if the API has been moved.

| Variable | Default | Meaning |
|---|---|---|
| `VITE_API_BASE_URL` | `/api/v1` | Where the API lives. |
| `VITE_USE_MOCK` | unset | Set to `1` to skip the API entirely and always use fixtures. |
| `VITE_API_PROXY_TARGET` | `http://localhost:8001` | Where the dev server proxies `/api`. |

The contract these fields follow is
[`docs/delivery/sprint-1-lead-contract.md`](../docs/delivery/sprint-1-lead-contract.md), and
`src/api/types.ts` is its TypeScript copy.

## Compliance controls

Lead Detail shows provenance, separate email/SMS/WhatsApp eligibility, terminal suppression
history, and forms for recording human reviews or opt-outs. Mutation controls are deliberately
disabled while sample fixtures are shown so a local demo cannot look like a persisted decision.
Read [`docs/compliance/outreach-sop.md`](../docs/compliance/outreach-sop.md) for the operator
workflow. Authentication and the `admin`/`sales` roles are in place; both roles can see contact
details because both work the lead desk.
