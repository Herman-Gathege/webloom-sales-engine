#!/bin/sh
set -eu

echo "==> Running database migrations"
alembic upgrade head

echo "==> Seeding sample leads"
python -m app.seed

echo "==> Starting: $*"
exec "$@"
