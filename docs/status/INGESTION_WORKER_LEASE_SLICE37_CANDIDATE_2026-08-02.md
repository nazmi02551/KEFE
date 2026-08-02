# Durable Ingestion Worker Claim, Lease and Stale Recovery — Slice 37 Candidate

**Issue:** #198  
**Parent:** PR #197 / Slice 36  
**Capabilities:** CAP-055, CAP-065  
**Foundation wave:** F1 operational completion  
**Status:** candidate; exact-head CI pending

## Candidate boundary

This slice adds the durable worker-admission boundary missing from the provider-neutral ingestion runtime:

`QUEUED IngestionRun → exclusive ACTIVE lease → heartbeat/assertion → release or stale recovery`

Implemented candidate behavior:

- versioned `IngestionRunLease` model with `ACTIVE`, `RELEASED` and `EXPIRED` history states;
- one active lease per run, enforced in memory and by PostgreSQL partial unique index;
- deterministic oldest-first claim by `(updated_at, run_id)`;
- PostgreSQL `FOR UPDATE SKIP LOCKED` claim semantics;
- claim atomically transitions the selected run from `QUEUED` to `RUNNING` and inserts the lease;
- claim first recovers due leases;
- bounded TTL from 5 seconds to 15 minutes;
- heartbeat and active-admission assertion require both exact lease ID and worker reference;
- explicit release dispositions:
  - `REQUEUE` requires a still-`RUNNING` run and transitions it to `QUEUED`;
  - `TERMINAL` requires the orchestration runtime to have already produced a terminal run state;
- stale recovery records `EXPIRED`, requeues only still-`RUNNING` runs and permits reclaim with a new lease ID;
- durable PostgreSQL lease history and reversible migration `20260802_0021`;
- coordinator exposed through application composition for future worker entrypoints.

## Preserved boundaries

This slice does not add:

- a scheduler loop, cron trigger or process supervisor;
- a provider adapter, network fetch or AI call;
- a stage processor implementation;
- an Admin HTTP lease endpoint or queue assignment UI;
- automatic Proposal review or Editorial Projection;
- authoring approval/publication;
- Case Builder, Flow Composer or phone behavior.

The lease is a provider-neutral worker admission capability. It is not an Admin/consumer identity and does not grant editorial authority.

## Contract authority

- ADR-0073;
- `docs/contracts/ingestion-worker-lease-slice37.v1.json`;
- migration `services/api/migrations/versions/20260802_0021_ingestion_run_lease.py`.

## Evidence rule

Do not call Slice 37 PASS until the same exact runtime SHA succeeds in:

- API CI lint/unit/architecture/contract/OpenAPI jobs;
- PostgreSQL migration upgrade → downgrade to `20260802_0020` → upgrade head;
- memory and PostgreSQL claim/concurrency/heartbeat/recovery/release tests;
- MVP Beta Gates;
- Global Readiness.

Automated evidence does not establish a running scheduler, external provider operation, worker process supervision, deployed SLO or operator usability.
