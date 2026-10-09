# FikaTu Integration Notes for the Webloom Sales Engine

**Date:** 2026-10-08
**Purpose:** the exact surface the Sales Engine uses to send outreach and observe delivery,
verified against FikaTu's source code rather than its documentation.
**System under study:** FikaTu / notification platform — https://github.com/Herman-Gathege/notifications_pipeline_system

**Sources verified** (local clone at `/home/remington/Projects/2026-projects/notification-platform`):

| File | What it established |
|---|---|
| `backend/app/api/v1/router.py` | All routes live under `/api/v1` |
| `backend/app/api/v1/events.py` | Event publishing endpoint and token handling |
| `backend/app/api/v1/auth.py` | Token, login, validate, me, logout endpoints |
| `backend/app/api/v1/notifications.py` | Notification listing, fetch, retry |
| `backend/app/api/v1/templates.py` | Template CRUD and event-type listing |
| `backend/app/schemas/event.py` | `EventCreate` and `EventResponse` shapes |
| `backend/app/events/registry.py` | The five registered event types and their payload models |
| `backend/app/services/event_validation_service.py` | Behaviour for an unknown event type |
| `backend/app/services/event_service.py` | Event creation and per-channel notification fan-out |
| `backend/app/models/notification.py` | Notification fields and status values |
| `backend/app/workers/notification_worker.py` | Recipient resolution, delivery, final status |
| `backend/app/providers/base.py` | The provider interface |
| `backend/app/providers/whatsapp/whatsapp_provider.py` | Empty file — no WhatsApp implementation |
| `docker-compose.yml`, `.env.example` | Services, ports, environment variable names |
| `AGENTS.md`, `README.md`, `docs/*` | House conventions and stated intent |

---

## Integration contract

Base URL: `http://<host>:<NGINX_PORT>/api/v1` in the composed deployment, or
`http://localhost:<BACKEND_PORT>` against the API service directly. Interactive docs are at
`/docs`.

### 1. Get an application token

```bash
curl -X POST http://localhost/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "<API_KEY>", "secret": "<SECRET>"}'
```

Response:

```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

Source: `backend/app/api/v1/auth.py` (`POST /auth/token`).

### 2. Publish an event

```bash
curl -X POST http://localhost/api/v1/events \
  -H "Authorization: Bearer <APPLICATION_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
        "event_type": "<registered event type>",
        "payload": { "...": "..." },
        "channels": ["sms"]
      }'
```

Response `201`:

```json
{
  "id": "<uuid>",
  "application_id": "<uuid>",
  "event_type": "<type>",
  "payload": { "...": "validated payload" },
  "status": "received",
  "is_processed": false,
  "created_at": "2026-10-08T00:00:00Z"
}
```

Field notes, from `backend/app/schemas/event.py`:

- `event_type` — required `str`; must exist in the event registry (see below).
- `payload` — required free-form `dict`, then validated against the event type's model.
- `channels` — required `list[str]`. The API loops over it and creates one notification row
  per channel. `email`, `sms`, and `whatsapp` are the channel strings used elsewhere in the
  code; there is no enum constraint on the field itself.
- `application_id` — optional `str`. Only needed when publishing with a user token rather
  than an application token; with an application token the ID comes from the token.

Source: `backend/app/api/v1/events.py`, `backend/app/services/event_service.py`.

### 3. Read notification status

```bash
curl http://localhost/api/v1/notifications -H "Authorization: Bearer <TOKEN>"
curl http://localhost/api/v1/notifications/<notification_id> -H "Authorization: Bearer <TOKEN>"
curl -X POST http://localhost/api/v1/notifications/<notification_id>/retry \
  -H "Authorization: Bearer <TOKEN>"
```

Source: `backend/app/api/v1/notifications.py`.

### 4. Templates

`GET /templates/event-types`, `POST /templates`, `GET /templates`,
`PATCH /templates/{id}`, `DELETE /templates/{id}`.
Source: `backend/app/api/v1/templates.py`.

---

## Authentication

Two token types, both JWTs issued by the same service:

- **Application token** — `POST /api/v1/auth/token` with `api_key` and `secret`. This is what
  the Sales Engine uses for publishing events. Lifetime is governed by
  `ACCESS_TOKEN_EXPIRE_MINUTES`.
- **User token** — `POST /api/v1/auth/login` with email and password, used by the human
  dashboard. Related endpoints: `POST /api/v1/auth/register`, `POST /api/v1/auth/validate`,
  `GET /api/v1/auth/me`, `POST /api/v1/auth/logout`.

**How the Sales Engine gets its key and secret:** register once as an application
(`POST /api/v1/applications`, authenticated with a user token), then store the returned
`api_key` and `secret` in the Sales Engine's environment. That is roadmap story R1.5.
Neither value is ever committed.

---

## Event types and how to add a new one

FikaTu's registry (`backend/app/events/registry.py`) holds exactly five types:
`payment.success`, `user.registered`, `password.reset`, `otp.requested`, `greetings`.

Each is a Pydantic model with typed, partly required fields, validated in
`EventValidationService.validate`. Two consequences the Sales Engine must design around:

1. **An unregistered event type is rejected** with `422 Unsupported event type '<type>'.`
   There is no generic pass-through event type to reuse.
2. **The validated payload replaces what you sent.** `validate` returns
   `schema.model_validate(payload).model_dump()`, so any field not declared on the model is
   silently dropped before the event is stored. Every field the Sales Engine relies on must
   exist on the model.

Adding an event type is a change in the **FikaTu** repository:

1. Add a `BaseModel` subclass in `backend/app/events/registry.py` declaring every field the
   Sales Engine sends — at minimum the recipient phone or email, the message body, and a
   correlation reference back to the outreach.
2. Register it in the `EVENT_REGISTRY` dict in the same file.
3. Add a template for it (see below).
4. Ship it through FikaTu's own review process.

This is a cross-repository dependency: the Sales Engine's send block cannot complete before a
corresponding FikaTu change ships. Sequence it deliberately — see "Gaps".

## Templates

Templates are managed through `/api/v1/templates` and matched by the worker when rendering.
`GET /api/v1/templates/event-types` lists the event types a template can attach to, so a
newly registered event type becomes available there automatically.

The worker resolves variables against the validated payload (`_derive_variables` in
`backend/app/workers/notification_worker.py`) and treats a template containing unresolved
placeholders as a failure rather than sending it. The Sales Engine should rely on FikaTu for
final rendering and treat an unresolved placeholder as a hard failure, not a cosmetic one.

## Channels and providers

| Channel | Provider | Implemented? | Evidence |
|---|---|---|---|
| `email` | Resend | Yes | `backend/app/providers/email/resend_provider.py`; `RESEND_*` vars in `.env.example` |
| `email` | SMTP | Yes | `backend/app/providers/smtp_provider.py`; `SENDGRID_*` vars present but unused |
| `sms` | Africa's Talking | Yes, verified end to end | `backend/app/providers/sms/sms_provider.py`; README states the sandbox pipeline is verified |
| `whatsapp` | none | **No** | `backend/app/providers/whatsapp/whatsapp_provider.py` is a **0-byte file**. `WHATSAPP_PROVIDER` and `META_ACCESS_TOKEN` exist in `.env.example`, so the intent is there and the implementation is not |

Every provider implements `NotificationProvider.send(*, recipient, body, subject)` and returns
`{success, provider_message_id, status, status_code, error}` (`backend/app/providers/base.py`).

**Consequence for the pilot:** email and SMS are real today; WhatsApp is not, even though the
channel string is accepted by the API and a `whatsapp` column exists in reporting. A campaign
sent with `channels: ["whatsapp"]` would create notification rows that cannot deliver.

## Delivery status and retries

Status lives on the `Notification` row (`backend/app/models/notification.py`), alongside
`provider`, `processing_time_ms`, and `failure_reason`.

Observed values: `queued` (the default at row creation), then, set by the worker, `delivered`
on success or `dead_letter` on failure. `failed` also appears in the worker's early-exit
paths. The worker writes a single final status; intermediate `sent` states were not observed.

`recipient` is resolved by the worker from the payload, not from the request:
`payload_data["email"]` for the email channel, `payload_data["phone"]` for `sms` and
`whatsapp`. This is a hard constraint on any Sales Engine payload model.

Retry is available explicitly through `POST /api/v1/notifications/{id}/retry`. No Celery
`autoretry`, `max_retries`, or `acks_late` configuration was found in the worker or the queue
module, so treat automatic retry as **not established** and plan an explicit retry policy on
the Sales Engine side, or confirm with Mark before depending on it.

## Inbound message support

**There is none.** A search across `backend/app` for `webhook`, `inbound`, `incoming`,
`receive`, and `callback` returned only an unrelated default status string. There is no
endpoint, model, or worker for received messages, and nothing that would surface a WhatsApp
or SMS reply back into FikaTu.

The Sales Engine therefore treats reply detection as its own problem:

- **Pilot approach:** a human records the reply in the Sales Engine UI against the lead and
  the outreach (story R8.1). Honest and workable at pilot scale.
- **Later:** a WhatsApp Business API webhook (or an SMS gateway callback) received by the
  Sales Engine, or by a future FikaTu inbound module, would automate it. That is a separate
  scope decision, listed in the delivery plan as explicitly deferred.

## Running FikaTu locally

```bash
docker compose up --build
```

Services declared in `docker-compose.yml`: `notification-postgres` (PostgreSQL 17),
`notification-redis` (Redis 7), `notification-api`, `notification-worker`,
`notification-frontend`, `notification-nginx`. Nginx fronts everything on `${NGINX_PORT}:80`;
Swagger is at `/docs`.

Environment variable names needed for an integration (names only — values live in the local
`.env`, which is gitignored): `NGINX_PORT`, `BACKEND_PORT`, `FRONTEND_PORT`, `POSTGRES_*`,
`REDIS_*`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `SECRET_KEY`,
`ACCESS_TOKEN_EXPIRE_MINUTES`, `EMAIL_PROVIDER`, `SMS_PROVIDER`, `WHATSAPP_PROVIDER`,
`RESEND_*`, `AFRICASTALKING_*`, `META_ACCESS_TOKEN`, `INITIAL_ADMIN_EMAIL`,
`INITIAL_ADMIN_PASSWORD`.

Tests run inside the running API container:

```bash
docker compose exec notification-api python -m pytest tests/ -v
```

## Gaps the Sales Engine must plan around

1. **No matching event type exists.** Every send needs a new registered event type in FikaTu
   (`EVENT_REGISTRY`) with a payload model declaring the recipient field and the message body.
   Until it ships, the Sales Engine cannot send at all.
   *Workaround:* land the FikaTu event type before the Sales Engine's send block, as a dated
   dependency owned by Mark.
2. **WhatsApp cannot deliver.** The provider file is empty.
   *Workaround:* run the pilot on email or SMS; treat WhatsApp as a later milestone with its
   own scope decision.
3. **No inbound reply capture.** Confirmed absent.
   *Workaround:* manual reply recording in the Sales Engine UI for the pilot.
4. **Payload fields are silently dropped if undeclared.** The validated payload replaces the
   submitted one.
   *Workaround:* declare every field the Sales Engine needs on the registry model, and add a
   FikaTu test asserting the round trip preserves them.
5. **Missing variables fail a send.** The worker rejects templates with unresolved
   placeholders.
   *Workaround:* validate required variables at draft generation time in the Sales Engine so a
   bad render never reaches FikaTu.
6. **The recipient comes from `email` or `phone` keys in the payload.** A differently named
   field means an empty recipient.
   *Workaround:* fix those field names in the registry model and mirror them in the Sales
   Engine's payload builder.
7. **Status is one final value per notification, with no event timeline.**
   *Workaround:* the Sales Engine keeps its own outreach timeline and polls FikaTu for the
   latest status; it never tries to reconstruct history from FikaTu.
8. **Automatic retry is not established.** Retry exists only as an explicit API call.
   *Workaround:* idempotent sends (story R7.3) plus an explicit Sales Engine retry policy.
9. **Cross-repository release dependency.** A FikaTu change is required mid-project.
   *Workaround:* plan it as a dated dependency rather than discovering it mid-project.

## Recommended Sales Engine usage

**One event type, one template per channel, one notification per send.**

Register an event type such as `sales.outreach.send` with a payload model along these lines
(field names must match what the worker reads for the recipient):

```json
{
  "business_name": "Optica",
  "phone": "+254709709000",
  "email": "",
  "message": "Good morning Optica team. ...",
  "campaign_ref": "<sales-engine-campaign-id>",
  "outreach_ref": "<sales-engine-outreach-id>",
  "opt_out_text": "Reply STOP to opt out."
}
```

The Sales Engine then:

1. Publishes with `channels: ["sms"]` or `["email"]`, matching the outreach channel.
2. Stores the returned event `id` and the notification `id` against the outreach record.
3. Polls `GET /api/v1/notifications/{id}` on a schedule and writes the status into its own
   outreach timeline.
4. On failure, reads `failure_reason` and either retries once through
   `POST /api/v1/notifications/{id}/retry` or marks the outreach failed, depending on the
   failure class.

Internal notifications to the team (handoff assignment, due follow-ups) reuse the same
mechanism with a separate event type, which is a narrower change than the first one.

## Uncertainties

- Whether `channels` accepts arbitrary strings or is validated further downstream. No enum
  constraint was found, and an unknown channel would create a notification row no provider
  resolves.
- The exact retry semantics of the worker's early-exit paths, and whether Celery retry
  configuration exists outside the files searched.
- Whether provider selection is driven by the `EMAIL_PROVIDER`/`SMS_PROVIDER` settings or by
  a `provider` row in the database. The worker uses `ProviderRepository`, which suggests the
  database, but this was not confirmed end to end.
- Notification status values are uneven across code paths (`queued`, `delivered`, `failed`,
  `dead_letter`). Confirm the definitive set before the Sales Engine writes status-mapping
  logic.
