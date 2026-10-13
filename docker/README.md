# Docker — Epic 1

This directory holds the container wiring for the first slice. One command starts the
database and the API from a clean clone:

```bash
docker compose up --build
```

## What runs

| Service | Image | Job |
|---|---|---|
| `db` | `postgres:17` | PostgreSQL. On first boot it creates `webloom_sales_engine` and `webloom_sales_engine_test`. |
| `api` | built from `backend/Dockerfile` | Runs `alembic upgrade head`, seeds the sample leads, then starts FastAPI. |
| `api-test` | same backend image, `test` profile | Runs the pytest suite inside the container. |

The API container listens on port 8000 internally and is published on host port **8001**.
Port 8000 is deliberately not used: another project owns it on at least one team machine,
and a bad port silently leaves the frontend on sample data.

## Commands

```bash
docker compose up --build       # start db + api
docker compose run --rm api-test   # run the backend tests in a container
docker compose exec db psql -U postgres -d webloom_sales_engine   # inspect the app db
docker compose down             # stop containers, keep the data volume
docker compose down -v          # stop and delete the data volume
```

## Watch-outs

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

## Decisions to agree before continuing

1. Keep the API on host port 8001 and leave PostgreSQL internal unless a tool genuinely needs
   host access.
2. Keep one local image with runtime and test dependencies for now, and split it when a real
   deploy exists.
3. Add Nginx and the built frontend to Compose in the block that makes the demo a single
   end-to-end command. It was deliberately out of scope for this card.
