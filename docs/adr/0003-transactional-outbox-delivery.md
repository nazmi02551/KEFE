# ADR-0003 — Transactional outbox delivery and provider-neutral event transport

**Status:** Accepted  
**Date:** 2026-07-27

## Context

KEFE persists decision lifecycle events in the same PostgreSQL transaction as the state change. Those outbox rows still need reliable delivery to analytics, recommendation, integrity, notification, research and future queue/broker consumers.

A direct dependency on one broker would violate the controlled-replaceability rule, while publishing to an external broker inside the decision transaction would couple commit latency and availability to an auxiliary dependency.

## Decision

- PostgreSQL remains the source transactional outbox for domain events.
- Event publication is performed by a separate worker through two ports: `OutboxStore` and `EventTransport`.
- Transport/provider SDKs are infrastructure adapters and cannot be imported by domain/application modules.
- Delivery semantics are **at least once**. Consumers must be idempotent using `event_id` and their own processed-event guard where side effects are non-idempotent.
- Workers claim bounded batches using a lease with PostgreSQL `FOR UPDATE SKIP LOCKED` so multiple workers can operate concurrently without intentionally processing the same lease at the same time.
- Claims increment `attempts`; failed delivery uses bounded exponential backoff.
- Events reaching the configured attempt limit are dead-lettered instead of being retried forever.
- Expired leases are reclaimable after worker crashes.
- Core decision requests do not wait for event transport availability after the outbox row has committed.
- The initial transport is structured logging for local/development validation. Future managed queue/broker adapters must implement the same `EventTransport` contract.
- Transport/provider choice, batch size, lease, poll interval and retry policy are typed configuration; Commit First and transaction atomicity are not configurable.

## Consequences

- A broker outage does not make `Case → Weigh → Commit → Reveal` unavailable.
- Provider migration does not require changes to decision domain/application code.
- Exactly-once delivery is not claimed across distributed systems.
- Monitoring must include unpublished backlog, oldest event age, retries, dead-letter count and publish latency.
- Dead-letter replay requires an audited operational command before production readiness.
