# ADR-0076 — Durable Source Acquisition Cadence and Dispatch Supervision

**Status:** Accepted for Slice 40 implementation  
**Date:** 2026-08-02  
**Issue:** #204  
**Parent runtime:** PR #203 / Slice 39  
**Capabilities:** CAP-054, CAP-055, CAP-065  
**Foundation wave:** F1 durable cadence and dispatch supervision

## Context

KEFE now has a provider-neutral source acquisition boundary and a lease-supervised ingestion worker. The application still lacks a durable cadence ledger. A naïve process loop that sleeps and directly calls acquisition would lose due work on crashes, drift intervals based on execution time and allow multiple replicas to capture the same occurrence concurrently.

The scheduling boundary must be durable and provider-neutral before a real adapter or deployment process is adopted. It must not claim operating-system supervision or introduce cron/timezone semantics that have not been designed.

## Decision

KEFE will add two synchronous one-shot services over a durable schedule and dispatch ledger:

1. `plan_due_once(now)` records at most one due occurrence.
2. `execute_pending_once(worker_ref, ttl, now)` owns and executes at most one pending occurrence.

A future daemon or platform scheduler may call these operations, but no continuous loop is included in Slice 40.

### Schedule model

- Schedule configuration is immutable after creation.
- The deterministic schedule key covers exact adapter code, external locator, exact pipeline code/version, configuration and optional taxonomy/methodology/locale/jurisdiction pins, interval, initial due time and maximum dispatch claim attempts.
- Cadence is UTC fixed interval only.
- Interval is bounded between 60 seconds and 30 days.
- Schedule lifecycle is `ACTIVE`, `PAUSED`, `RETIRED`.
- Allowed transitions are `ACTIVE → PAUSED|RETIRED` and `PAUSED → ACTIVE|RETIRED`; `RETIRED` is terminal.
- Pausing does not discard backlog or rewrite the next due time.

### Planning semantics

- A dispatch occurrence is uniquely identified by `(schedule_id, due_at)`.
- `plan_due_once` selects the oldest `ACTIVE` schedule with `next_due_at <= now`.
- PostgreSQL uses `FOR UPDATE SKIP LOCKED` so multiple planner replicas cannot create the same occurrence.
- Planning and advancing the schedule occur in one transaction.
- `next_due_at` advances from the previous due time by exactly one interval, never from planner execution time. Late ticks therefore do not drift cadence.
- One invocation plans at most one occurrence; repeated ticks deterministically catch up backlog.
- Planning never invokes an adapter, acquisition service or ingestion worker.

### Dispatch ownership

Dispatch state is one of:

- `PENDING`
- `RUNNING`
- `SUCCEEDED`
- `RETRYABLE_FAILURE`
- `FINAL_FAILURE`
- `BLOCKED`

`execute_pending_once`:

- recovers stale `RUNNING` dispatches before selection;
- selects the oldest `PENDING` occurrence with PostgreSQL `FOR UPDATE SKIP LOCKED`;
- increments a bounded claim attempt counter;
- assigns exact worker identity and an expiring lease window;
- executes only the exact schedule command stored with the occurrence's schedule.

Heartbeat requires exact dispatch ID and worker identity. An expired, terminal or foreign dispatch cannot authorize writes.

### Stale recovery and attempt exhaustion

- Each schedule pins `max_dispatch_attempts` between 1 and 10.
- A stale `RUNNING` dispatch with attempts remaining returns to `PENDING` and clears ownership fields.
- A stale dispatch at its maximum attempt becomes `FINAL_FAILURE` with bounded code `SOURCE_DISPATCH_ATTEMPTS_EXHAUSTED`.
- Stale recovery never creates or deletes SourceArtifacts or IngestionRuns.

### Acquisition admission guards

Slice 39 `SourceAcquisitionService.acquire(...)` gains internal optional callbacks:

- `before_artifact_persist`
- `before_run_admission`

The dispatch executor heartbeats:

1. immediately before adapter capture;
2. immediately before SourceArtifact persistence;
3. immediately before IngestionRun admission;
4. immediately before dispatch completion.

If ownership is lost at either persistence callback, the expired owner performs no following write. If a SourceArtifact was already persisted before ownership is lost at run admission, it remains canonical and replay completes admission through Slice 39 idempotency.

If acquisition completes but the process crashes before dispatch completion, stale recovery requeues the dispatch; replay returns the same SourceArtifact/IngestionRun identities and safely completes the ledger.

### Completion semantics

- `ADMITTED` maps to dispatch `SUCCEEDED` and stores only SourceArtifact/IngestionRun IDs.
- `RETRYABLE_FAILURE`, `FINAL_FAILURE` and `BLOCKED` map to the corresponding terminal dispatch state and bounded error code.
- Slice 40 does not automatically retry a completed acquisition failure. New cadence occurrences continue independently; retry/backoff policy is a separate decision.
- Dispatch results and observers never contain source body, provider response, Proposal payload, private reason, credentials or exception text.
- Observer failure is non-authoritative.

## Explicit exclusions

No cron expression, local-time timezone/DST cadence, continuous daemon loop, OS process manager, deployment manifest, real provider adapter, network request, scraping, AI call, automatic schedule creation, automatic retry/backoff for completed acquisition failures, ingestion worker invocation, Proposal review/projection, authoring transition, Admin HTTP/UI, Case Builder, Flow Composer or phone behavior is included.

## Evidence required

Slice 40 is not PASS until one exact runtime SHA proves:

- reversible migration and one database head;
- immutable schedule configuration and lifecycle transitions;
- fixed-interval no-drift planning and one unique occurrence per due time;
- concurrent PostgreSQL planners and executors do not claim the same work;
- dispatch heartbeat/owner enforcement;
- stale recovery to PENDING and bounded attempt exhaustion to FINAL_FAILURE;
- heartbeat at both Slice 39 persistence boundaries;
- lease loss prevents unauthorized dispatch completion and following artifact/run writes;
- crash after successful acquisition replays the same identities and completes dispatch;
- privacy-safe results and empty production schedule/provider configuration;
- memory/PostgreSQL parity, architecture fitness, API CI, MVP Beta Gates and Global Readiness success.

Automated evidence does not establish a running daemon, OS process supervision, external provider operation, provider terms compliance, deployed SLO, operator usability or production rollback readiness.
