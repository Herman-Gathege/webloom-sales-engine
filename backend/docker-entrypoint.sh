#!/bin/sh
set -eu

# `pg_isready` can pass against the temporary PostgreSQL that initdb runs, so
# the API container can start before the real server accepts connections. Retry
# instead of trusting the healthcheck alone: migrating is idempotent, so a
# migration that fails against a not-yet-ready database is safe to attempt again.
echo "==> Running database migrations"
attempt=1
until alembic upgrade head; do
  if [ "$attempt" -ge 30 ]; then
    echo "!! PostgreSQL was not ready after $attempt attempts. Giving up." >&2
    exit 1
  fi
  echo "    Database not ready yet (attempt $attempt); retrying in 2s"
  attempt=$((attempt + 1))
  sleep 2
done

echo "==> Seeding sample leads"
python -m app.seed

echo "==> Starting: $*"
exec "$@"
