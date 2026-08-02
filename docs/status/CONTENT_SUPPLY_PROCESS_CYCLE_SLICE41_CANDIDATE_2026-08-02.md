# Content-Supply Process Cycle — Slice 41 Candidate

- Date: 2026-08-02
- Issue: #206
- Branch: `feature/content-supply-process-cycle-slice41`
- Base: PR #205 / Slice 40 exact head
- Status: Candidate — exact-head CI pending

## Candidate capability

This slice introduces a provider-neutral finite process cycle that can be invoked by an external scheduler or process manager. One invocation performs, in order and within explicit budgets:

1. source acquisition occurrence planning;
2. pending source dispatch execution;
3. exact ingestion pipeline execution.

The cycle records a durable heartbeat/history in `ingestion.content_supply_cycle` with aggregate operational counters only.

## Locked behavior

- no internal daemon, sleep, polling or cron parser;
- exact ordered pipeline code/version targets;
- deterministic plan hash;
- bounded planning, dispatch and ingestion budgets;
- heartbeat before and after delegated units and before terminal completion;
- exact cycle owner and expiring heartbeat;
- stale `RUNNING` cycles recover only to `ABANDONED`;
- delegated dispatch/run state remains owned by existing Slice 37–40 aggregates;
- terminal `DEGRADED` records delegated non-success without autonomous retry;
- unexpected supervisor errors are bounded to a generic failure code;
- one-shot CLI emits privacy-safe allowlist JSON and deterministic exit codes;
- default production adapter, schedule and runtime registries remain empty.

## Candidate evidence included

- memory phase-order, budget, idle, degraded, supervisor-failure, lease-loss and observer tests;
- CLI parsing, output allowlist and exit-code tests;
- PostgreSQL owner heartbeat/completion, stale abandonment and concurrent recovery tests;
- reversible migration `20260802_0023`;
- executable architecture fitness gate.

## Explicit non-claims

This candidate does not prove or introduce:

- a continuously running process;
- OS/Kubernetes/systemd supervision;
- a configured external provider or network capture;
- provider rate-limit or terms compliance;
- deployed metrics, alerts, SLOs or rollback readiness;
- operator usability;
- automatic Proposal review/projection/publication;
- Admin UI/HTTP, Case Builder, Flow Composer or phone-facing behavior.

Do not mark Slice 41 PASS until API CI, MVP Beta Gates and Global Readiness all succeed on the same runtime SHA.
