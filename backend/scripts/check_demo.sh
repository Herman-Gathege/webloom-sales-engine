#!/usr/bin/env bash
#
# End-to-end check of the Lead slice: migration -> seed -> API -> importer.
#
# Run from the backend directory:  bash scripts/check_demo.sh
# It drops and recreates the schema of the database in DATABASE_URL, so it
# refuses to run against anything that does not look like a development or test
# database.

set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-.venv/bin/python}"
ALEMBIC="${ALEMBIC:-.venv/bin/alembic}"
PORT="${PORT:-8099}"
BASE_URL="http://127.0.0.1:${PORT}"

failures=0
pass() { printf 'PASS  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; failures=$((failures + 1)); }

if [[ "${ENVIRONMENT:-development}" == "production" || "${ENVIRONMENT:-development}" == "prod" ]]; then
  echo "Refusing to run: ENVIRONMENT is ${ENVIRONMENT}." >&2
  exit 1
fi

DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://postgres:postgres@localhost:5432/webloom_sales_engine}"
PSQL_URL="${DATABASE_URL/postgresql+psycopg/postgresql}"
DB_NAME="${PSQL_URL##*/}"

case "$DB_NAME" in
  *_test | *_dev | *demo*) ;;
  *) echo "Refusing to run: database '$DB_NAME' is not a _test, _dev or demo database." >&2; exit 1 ;;
esac
echo "Checking against database: $DB_NAME"

SERVER_PID=""
cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

if psql "$PSQL_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" >/dev/null 2>&1 &&
  "$ALEMBIC" upgrade head >/dev/null 2>&1; then
  pass "migration runs on a clean database (alembic upgrade head)"
else
  fail "migration on a clean database"
  exit 1
fi

first_run="$("$PYTHON" -m app.seed)"
second_run="$("$PYTHON" -m app.seed)"
if grep -q "0 leads created" <<<"$second_run"; then
  pass "seed is repeatable (second run created nothing)"
else
  fail "seed repeatability: $second_run"
fi
echo "      ${first_run##*$'\n'}"

case "$PSQL_URL" in
  *@*) ;;
  *) fail "DATABASE_URL is not a URL the script can parse"; exit 1 ;;
esac

"$PYTHON" -m uvicorn app.main:app --port "$PORT" --log-level warning >/tmp/check_demo_uvicorn.log 2>&1 &
SERVER_PID=$!

for _ in $(seq 1 30); do
  curl -sf "${BASE_URL}/health" >/dev/null 2>&1 && break
  sleep 0.5
done

if curl -sf "${BASE_URL}/health" >/dev/null 2>&1; then
  pass "server answers GET /health"
else
  fail "server did not start; see /tmp/check_demo_uvicorn.log"
  exit 1
fi

list="$(curl -sf "${BASE_URL}/api/v1/leads")"
if grep -q '"items"' <<<"$list" && grep -q '"total"' <<<"$list"; then
  pass "GET /api/v1/leads returns items and a total"
else
  fail "GET /api/v1/leads: $list"
fi

lead_id="$("$PYTHON" -c 'import json,sys; print(json.load(sys.stdin)["items"][0]["id"])' <<<"$list")"
detail="$(curl -sf "${BASE_URL}/api/v1/leads/${lead_id}")"
if grep -q '"activity"' <<<"$detail"; then
  pass "GET /api/v1/leads/{id} returns the lead with its activity"
else
  fail "GET /api/v1/leads/{id}: $detail"
fi

missing_status="$(curl -s -o /tmp/check_demo_missing.json -w '%{http_code}' \
  "${BASE_URL}/api/v1/leads/11111111-1111-4111-8111-111111111111")"
malformed_status="$(curl -s -o /tmp/check_demo_malformed.json -w '%{http_code}' \
  "${BASE_URL}/api/v1/leads/not-a-uuid")"
if [[ "$missing_status" == "404" && "$(cat /tmp/check_demo_missing.json)" == '{"detail":"Lead not found"}' ]]; then
  pass "an unknown lead is 404 with the contract body"
else
  fail "unknown lead: HTTP $missing_status body $(cat /tmp/check_demo_missing.json)"
fi
if [[ "$malformed_status" == "404" ]]; then
  pass "a malformed id is 404, not 422"
else
  fail "malformed id: HTTP $malformed_status (expected 404)"
fi

# The importer: a synthetic list in, a report out, and the good rows in the list.
import_json="$(curl -sf -F "file=@tests/fixtures/import_mixed.csv" "${BASE_URL}/api/v1/leads/import")"
counts="$("$PYTHON" -c 'import json,sys; b=json.load(sys.stdin); print(b["row_count"], b["accepted"], b["rejected"])' <<<"$import_json")"
if [[ "$counts" == "7 3 4" ]]; then
  pass "POST /api/v1/leads/import accounts for every row (7 rows: 3 accepted, 4 refused)"
else
  fail "import counts: got '$counts', expected '7 3 4'"
fi

# The report is a download of the refusals from the call that asks for it, and this
# is the same file a second time: the three rows imported above are already in the
# database, so their numbers are now refused too. Every one of the seven rows is
# refused here, and the report is expected to say so — one line each.
refused_csv="$(curl -sf -F "file=@tests/fixtures/import_mixed.csv" \
  "${BASE_URL}/api/v1/leads/import?format=csv")"
if grep -q "^row,business_name,code,reason" <<<"$refused_csv" &&
  [[ "$(grep -c . <<<"$refused_csv")" == "8" ]]; then
  pass "?format=csv downloads every refused row as a report (header plus seven)"
else
  fail "refused-rows download: $refused_csv"
fi

reimport="$(curl -sf -F "file=@tests/fixtures/import_mixed.csv" "${BASE_URL}/api/v1/leads/import")"
if grep -q '"accepted":0,"rejected":7' <<<"$reimport"; then
  pass "importing the same file twice creates no second copy (0 accepted, 7 refused)"
else
  fail "second import of the same file: $reimport"
fi

not_utf8_status="$(curl -s -o /dev/null -w '%{http_code}' \
  -F "file=@tests/fixtures/import_not_utf8.csv" "${BASE_URL}/api/v1/leads/import")"
if [[ "$not_utf8_status" == "400" ]]; then
  pass "a file that is not UTF-8 is refused with a 400"
else
  fail "non-UTF-8 upload: HTTP $not_utf8_status (expected 400)"
fi

if [[ "$failures" -eq 0 ]]; then
  echo "All checks passed."
else
  echo "$failures check(s) failed."
  exit 1
fi
