# Docker — Sprint 1

This directory holds the container wiring for the first slice. One command starts the whole
slice — database, API and UI — from a clean clone:

```bash
docker compose up --build
```

## What runs

| Service | Image | Job |
|---|---|---|
| `db` | `postgres:17` | PostgreSQL. On first boot it creates `webloom_sales_engine` and `webloom_sales_engine_test`. |
| `api` | built from `backend/Dockerfile` | Runs `alembic upgrade head`, seeds the sample leads, then starts FastAPI. |
| `frontend` | built from `frontend/Dockerfile` | Builds the SPA with Node 22 and serves it with Nginx, which also proxies `/api` to the API. |
| `api-test` | same backend image, `test` profile | Runs the pytest suite inside the container. |

The composed system answers on two host ports:

| What | URL |
|---|---|
| The app (open this one) | <http://localhost:5174> |
| The API directly | <http://localhost:8001> |

Both are overridable: `FRONTEND_PORT` and `API_PORT`. Port 8000 is deliberately not used for
the API — another project owns it on at least one team machine, and a bad port silently leaves
the UI on sample data. 5173 is likewise skipped, because it is the Vite dev port and is taken
on at least one machine.

The UI talks to the API through the same origin: Nginx serves the app and proxies `/api` to
the `api` container, so there is no CORS to configure and no API hostname is baked into the
bundle.

## Commands

```bash
docker compose up --build       # start db + api + frontend; open http://localhost:5174
docker compose run --rm api-test   # run the backend tests in a container
docker compose exec db psql -U postgres -d webloom_sales_engine   # inspect the app db
docker compose down             # stop containers, keep the data volume
docker compose down -v          # stop and delete the data volume
```

To work on the frontend with hot reload instead of the built image, run the containers for the
backend only and use the dev server:

```bash
docker compose up -d db api     # backend only
cd frontend && npm install && npm run dev   # http://localhost:5173
```

## Watch-outs

- **The first `up --build` is slow, and the database is unhealthy for the first ~90 seconds.**
  That is PostgreSQL running `initdb` and the init scripts; `up` waits for it. Measured: about
  eight minutes for the first build on one machine, under a minute afterwards. `db`'s
  healthcheck has a 60s `start_period` and 30 retries precisely for this — with a tighter
  budget, `up` aborts on a clean clone before the API is ever started.
- **`down -v` deletes the seeded data.** The named volume outlives `down`; only `down -v`
  resets it.
- **The init SQL runs only on a fresh volume.** `docker/postgres/init/` is executed the
  first time PostgreSQL creates an empty data directory. After that, changing the file has
  no effect until `docker compose down -v`.
- **Inside Docker the database host is `db`, not `localhost`.** The compose file sets
  `DATABASE_URL` and `TEST_DATABASE_URL` accordingly; `backend/.env.example` is for running
  the backend by hand.
- **Migrations and seed run on every API start.** Both are idempotent, so restarts are safe,
  but they add a couple of seconds. The seed still refuses to run when
  `ENVIRONMENT=production`.
- **The API image ships `requirements-dev.txt`.** That is what lets `api-test` run without a
  separate test image. It is fine for local development and should be split into runtime and
  test images before any non-local deployment.
- **PostgreSQL has no host port.** That avoids colliding with a local PostgreSQL on 5432.
  Use `docker compose exec db psql` to inspect it.
- **The frontend image is a production build, so it does not hot-reload.** That is deliberate:
  the composed stack is what we demo. Use `npm run dev` while you are writing UI code.

## Decisions to agree before continuing

1. Keep the API on host port 8001 and leave PostgreSQL internal unless a tool genuinely needs
   host access.
2. Keep one local image with runtime and test dependencies for now, and split it when a real
   deploy exists.
3. Keep the built SPA in Compose rather than the Vite dev server, so "one command" means the
   same thing on every machine. *(Agreed in the Sprint 1 close-out.)*
