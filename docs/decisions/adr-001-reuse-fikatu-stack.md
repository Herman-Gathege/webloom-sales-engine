# ADR-001 — Reuse the FikaTu stack and layering

**Date:** 2026-10-08
**Status:** Accepted
**Deciders:** Mark Mwenesi, Herman Gathege

## Context

The Sales Engine is a new application, but its team, conventions, and integration partner
already exist. FikaTu is a FastAPI, PostgreSQL, Redis, and Celery service with a React
frontend, built in this same team and reviewed by the same lead. The Sales Engine has to
call FikaTu and will be maintained by the same four people.

A new stack would buy novelty and cost the team its accumulated conventions, reuse, and
review speed.

## Decision

Build the Sales Engine on the same stack and the same backend layering as FikaTu:
Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, Celery, PostgreSQL, Redis, and a
React 19 + Vite + TypeScript frontend with Tailwind and shadcn/ui. Structure backend code as
`api/v1` → `schemas` → `services` → `repositories` → `models`, with provider-style external
integrations isolated under `integrations/`.

## Consequences

We accept a shared mental model over framework preference: one reviewer can review both
systems, patterns and fixes transfer, and infrastructure is familiar.

We give up the chance to adopt a stack we might have preferred for a greenfield project, and
we inherit any weaknesses of the FikaTu stack. Because both applications share conventions,
a change in one may create pressure to change the other; that pressure is handled by a
separate decision each time, not silently.

## Revisit if

- The Sales Engine needs something the FikaTu stack handles badly — a data-heavy analytics
  workload, real-time collaboration, or a queueing pattern Celery cannot express well.
- Maintaining two applications on identical conventions starts costing more than it saves,
  for example if the teams diverge.
