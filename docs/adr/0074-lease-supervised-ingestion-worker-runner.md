# ADR-0074 — Lease-Supervised Provider-Neutral Ingestion Worker Runner

**Status:** Accepted for Slice 38 implementation  
**Date:** 2026-08-02  
**Issue:** #200  
**Parent runtime:** PR #199 / Slice 37  
**Capabilities:** CAP-055, CAP-065  
**Foundation wave:** F1 executable worker runtime

## Context

KEFE now has durable provider-neutral `IngestionRun`, bounded stage attempts, atomic successful stage plus Proposal persistence, a human Proposal review queue and exclusive worker leases with stale recovery. The verified components are not yet connected by an executable worker service. A future scheduler or provider adapter must not call the raw orchestration service without exact pipeline resolution and lease admission around every durable stage outcome.

The next boundary must prove one safe unit of work without prematurely introducing a daemon, cron policy, external provider, AI dependency or autonomous editorial action.

## Decision

KEFE will add a synchronous one-shot `IngestionWorkerRunner.run_once(...)` service. One invocation claims at most one queued run and returns one privacy-safe structured result.

### Exact runtime plans

- A runtime plan is identified only by exact `(pipeline_code, pipeline_version)`.
- A plan contains an immutable ordered tuple of versioned stage definitions.
- Each stage definition pins `stage_code`, `stage_version`, `max_attempts` and `executor_kind`.
- Processor resolution uses the exact pipeline and stage identity. Title, provider, Case type, locale, payload shape or other heuristics may not select a processor.
- Duplicate plan identities, duplicate stage identities and empty plans fail at registry construction.

### Claim and resume

- Lease claim filtering is extended to exact pipeline code and version.
- The runner resolves the plan before claiming work.
- A claimed run must exactly match the resolved plan.
- Stage input hash is deterministic: the first stage receives `IngestionRun.input_content_hash`; every later stage receives the immediately preceding successful stage output hash.
- Existing successful stages are resumed rather than executed again.
- A prior retryable stage may execute its next bounded attempt through the existing orchestration service.
- Unknown or out-of-plan stage history fails closed as a blocked run; it is requeued only while the active lease still authorizes the runner.

### Lease supervision

- The runner heartbeats immediately before each processor invocation.
- `IngestionOrchestrationService.execute_stage(...)` gains an optional internal pre-persistence admission callback.
- The runner supplies a lease heartbeat callback as that admission guard.
- The callback executes after processor completion or failure classification but before any `StageExecution`, Proposal batch or run-state write.
- If the lease is expired, released, foreign or otherwise inactive, the callback raises and no stage outcome or Proposal is persisted.
- The expired owner does not release or requeue the lease; Slice 37 stale recovery remains the authority.

This does not make arbitrary external side effects transactional. Stage processors adopted later must remain bounded, replay-safe and compatible with lease TTL or be decomposed into smaller stages.

### Completion and failure

- After all planned stages are successful, the runner marks the run `SUCCEEDED` and releases the lease with `TERMINAL` disposition.
- Existing `RetryableStageError` semantics remain: a bounded retryable outcome leaves the run `FAILED_RETRYABLE`; the runner releases terminal ownership but does not automatically requeue it.
- Final and unexpected stage failures leave the run `FAILED_FINAL` and release terminal ownership.
- Retry scheduling and requeue policy remain separate future concerns.
- A crash after a successful stage but before final completion is recovered by lease expiry; the next runner resumes from persisted successful stages.

### Operational result and observer

Each invocation emits one `IngestionWorkerRunResult` with an outcome from:

- `IDLE`
- `SUCCEEDED`
- `RETRYABLE_FAILURE`
- `FINAL_FAILURE`
- `LEASE_LOST`
- `BLOCKED`

Allowed fields are bounded operational identifiers and timings: worker reference, exact pipeline identity, trace ID, optional run/lease/stage identifiers, completed stage count, stage attempt and duration. Raw source/provider responses, Proposal payloads, private reasons, credentials, exception text, user identity, ideology/personality/psychometric labels and causal claims are forbidden.

The observer is a provider-neutral port. The default application composition uses a no-op observer and an empty runtime registry until a separately contracted pipeline/provider is adopted.

## Explicit exclusions

No daemon loop, scheduler cadence, cron, process manager, deployment manifest, external SourceAdapter, network fetch, AI call, automatic run creation, automatic retry/requeue, Proposal review/projection, authoring lifecycle transition, Admin endpoint/UI, Case Builder, Flow Composer or phone-facing behavior is included.

## Evidence required

Slice 38 is not PASS until one exact runtime SHA proves:

- exact code+version claim filtering in memory and PostgreSQL;
- deterministic multi-stage chaining and resume without duplicate execution;
- lease heartbeat before processing and immediately before persistence;
- no durable stage/run/Proposal mutation after lease loss;
- retryable/final outcome and terminal release semantics;
- crash/reclaim resume from prior successful stage;
- observer payload allowlist and no sensitive/raw payload leakage;
- application composition with an empty production registry;
- architecture fitness, API CI, MVP Beta Gates and Global Readiness success.

Automated evidence does not establish an external provider, running scheduler, OS process supervision, deployed SLO, operator usability or production rollback readiness.
