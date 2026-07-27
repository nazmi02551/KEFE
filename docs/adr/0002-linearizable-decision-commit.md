# ADR-0002 — Linearizable decision commit boundary

**Status:** Accepted  
**Date:** 2026-07-27

## Context

The first PostgreSQL adapter persisted a commit and its outbox event in one transaction, but two requests could still read the same DRAFT session before either write completed. A competing response update could also hold a stale DRAFT copy while another request committed the same session.

KEFE's Commit First methodology requires the server-confirmed commit to behave as a single irreversible transition. Network retries must be safe and competing commands must not create multiple logical decisions or duplicate `weigh.committed` lifecycle events.

## Decision

- The durable commit boundary is linearized by locking the target `weigh_session` row with `SELECT ... FOR UPDATE` inside the repository transaction.
- Draft response mutations use the same row lock and are accepted only while the locked session is still `DRAFT`.
- The same commit `Idempotency-Key` replays the already-confirmed commit without creating another event.
- A different key racing the successful commit returns `WEIGH_SESSION_ALREADY_COMMITTED`.
- A commit idempotency key is unique per actor when present; reuse for another commit returns `IDEMPOTENCY_KEY_REUSED`.
- `weigh.started` and `weigh.committed` lifecycle events have a database uniqueness guard in addition to transactional application logic.
- Session state and the matching `weigh.committed` outbox row are written in the same transaction.
- Published CaseVersion immutability remains a domain invariant; a session whose pinned version is no longer the active published version is blocked before commit.

## Consequences

- Commit retries are safe under concurrent requests.
- Competing commit requests have one observable winner.
- A stale response write cannot revert a committed session to DRAFT.
- PostgreSQL details stay inside the infrastructure adapter; the application service still depends on the repository port.
- Outbox delivery remains at-least-once at the transport boundary; consumers must remain idempotent. This ADR guarantees uniqueness of the decision lifecycle event in the source database, not exactly-once delivery across distributed systems.
