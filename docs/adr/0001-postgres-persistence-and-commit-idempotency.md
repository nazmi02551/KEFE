# ADR-0001 — PostgreSQL persistence and commit idempotency lifecycle

**Status:** Accepted  
**Date:** 2026-07-27

## Context

The M0 business slice proved `Case → Weigh → Commit → Reveal` behind a provider-neutral `DecisionRepository` port using an in-memory adapter. The first durable adapter must preserve the same application rules while adding PostgreSQL persistence and a transactional outbox.

The initial SQL contract used a generic non-null `idempotency_key` on `weigh_session`, while the API contract applies `Idempotency-Key` specifically to the commit command. Session creation and decision commit are distinct lifecycle actions and must not share one ambiguous field.

## Decision

- PostgreSQL is the initial durable system of record behind a repository adapter.
- Domain and application modules remain independent of SQLAlchemy, psycopg and Alembic.
- Persistence backend selection is configuration-driven (`memory` or `postgres`).
- Commit idempotency is represented as nullable `commit_idempotency_key` until a commit succeeds.
- Session state persistence and its corresponding `weigh.started` / `weigh.committed` outbox event are written in the same database transaction.
- Reveal remains protected by the Commit First invariant regardless of adapter.
- The machine-readable SQL contract must receive a compatible patch reflecting the explicit commit-idempotency field before it is treated as the next schema contract version.

## Consequences

- PostgreSQL can replace the memory adapter without rewriting the decision service.
- The outbox cannot observe a committed state without its matching event, or vice versa, for writes performed through `save_session_with_event`.
- A later concurrency hardening step is still required to make simultaneous competing commit requests resolve under a row lock / compare-and-set rule at the database boundary.
- API command idempotency remains semantically separate from entity identity and session creation.
