# ADR-0073 — Durable Ingestion Worker Claim, Lease and Stale Recovery

**Status:** Accepted for Slice 37 implementation  
**Date:** 2026-08-02  
**Issue:** #198  
**Parent runtime:** PR #197 / Slice 36  
**Capabilities:** CAP-055, CAP-065  
**Foundation wave:** F1 operational completion

## Context

The ingestion runtime now provides replay-safe runs, atomic successful stage output, durable Proposals and a human review queue. It still lacks an ownership boundary for production workers. Without a lease, two worker processes can select the same queued run, or a crashed worker can leave a run permanently `RUNNING` with no recoverable owner.

This boundary must remain provider-neutral. A lease authorizes worker admission to an `IngestionRun`; it does not encode source, AI provider, stage implementation or editorial authority.

## Decision

KEFE will introduce a durable `IngestionRunLease` history aggregate and a coordinator with five operations:

1. `claim_next`
   - first expires stale active leases and requeues corresponding still-`RUNNING` runs;
   - selects the oldest eligible `QUEUED` run by `(updated_at, run_id)`;
   - PostgreSQL uses row locking with `FOR UPDATE SKIP LOCKED`;
   - transitions the run to `RUNNING` and creates one `ACTIVE` lease atomically.

2. `heartbeat`
   - requires exact lease ID and worker identity;
   - requires an unexpired `ACTIVE` lease;
   - advances heartbeat and expiry using a bounded TTL.

3. `assert_active`
   - provides the admission check future provider-neutral worker entrypoints must call before executing work;
   - rejects expired, released, foreign or unknown leases.

4. `release`
   - `REQUEUE` is valid only while the run remains `RUNNING`, transitions it to `QUEUED` and records a released lease;
   - `TERMINAL` is valid only after the run is already `SUCCEEDED`, `FAILED_RETRYABLE`, `FAILED_FINAL` or `CANCELED`;
   - release never invents a terminal outcome.

5. `recover_expired`
   - marks due active leases `EXPIRED`;
   - requeues only associated runs still in `RUNNING`;
   - leaves already-terminal runs unchanged.

Lease history rows are immutable in identity and ownership but may transition from `ACTIVE` to `RELEASED` or `EXPIRED`. A partial unique index enforces at most one active lease per run.

## TTL and identity

- TTL is bounded from 5 seconds to 15 minutes.
- Worker reference must be nonblank and is an internal deployment identity, not an Admin or consumer identity.
- Lease ID and worker reference must both match for heartbeat, assertion and release.
- Lease IDs are admission capabilities, not user credentials and are not exposed through Admin HTTP in this slice.

## Failure and recovery semantics

- claim, run transition and lease insert are one transaction/critical section;
- concurrent claimers cannot receive the same run;
- an expired lease cannot be renewed or released as active;
- a recovered run receives a new lease ID on reclaim, preventing ABA reuse;
- raw ingestion domain services remain trusted internal primitives, but future production worker composition must use the lease coordinator admission check.

## Explicit exclusions

No scheduler loop, cron trigger, provider adapter, network fetch, AI call, stage processor implementation, Admin lease endpoint, queue assignment UI, automatic review/projection, authoring lifecycle transition, Case Builder, Flow Composer or phone behavior is included.

## Evidence required

Slice 37 is not PASS until the same exact runtime SHA proves:

- one active lease per run in memory and PostgreSQL;
- concurrent PostgreSQL claims return distinct runs or one `None`, never the same run;
- heartbeat extends only the correct active owner;
- stale recovery expires and requeues, followed by reclaim under a new lease ID;
- release disposition/state rules fail closed;
- migration upgrade/downgrade and architecture fitness;
- API CI, MVP Beta Gates and Global Readiness success.

Automated evidence does not establish a running scheduler, provider operation, worker process supervision, deployed SLO or operator usability.
