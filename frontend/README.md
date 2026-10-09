# Frontend

The React shell for the Sales Engine. Epic 1 has two screens: the Lead List and the
Lead Detail (with the lead's activity history).

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

Sharon's Lead API is not built yet, so the app ships with synthetic sample leads in
`src/api/fixtures.ts` and shows a **"Sample data"** banner while it uses them.

It calls the real API first. The moment `GET /api/v1/leads` answers, the banner switches
to **"Live data"** and no frontend code changes. The dev server proxies `/api` to
`http://localhost:8000`, so there is no CORS to configure in development.

| Variable | Default | Meaning |
|---|---|---|
| `VITE_API_BASE_URL` | `/api/v1` | Where the API lives. |
| `VITE_USE_MOCK` | unset | Set to `1` to skip the API entirely and always use fixtures. |
| `VITE_API_PROXY_TARGET` | `http://localhost:8000` | Where the dev server proxies `/api`. |

The contract these fields follow is
[`docs/delivery/epic-1-lead-contract.md`](../docs/delivery/epic-1-lead-contract.md), and
`src/api/types.ts` is its TypeScript copy.
