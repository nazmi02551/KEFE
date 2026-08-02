# ADR-0078: Privacy-Safe Content-Supply Operational Health Snapshot

- Status: Accepted
- Date: 2026-08-02
- Decision owners: KEFE Product and Engineering
- Related: ADR-0073 through ADR-0077, Issues #180 and #209

## Context

Slices 37–41 provide durable work ownership, source scheduling, acquisition, exact ingestion execution and a bounded process-cycle journal. Operators still lack one compact read-only view that answers whether durable work is quiet, progressing, accumulating or stale.

A health view must not become another state machine, retry controller or content surface. It must not expose source locators, raw storage references, Proposal payloads, provider responses, credentials, user data or titles. It also must not imply production SLO compliance merely because local counters are below thresholds.

## Decision

Introduce `ContentSupplyHealthService.snapshot(policy, as_of)` over a dedicated read-only repository.

### Explicit policy

`ContentSupplyHealthPolicy` is immutable and contains bounded values for:

- pending source-dispatch attention threshold;
- queued ingestion-run attention threshold;
- unreviewed Proposal attention threshold;
- recent terminal non-success attention threshold;
- maximum cycle silence duration;
- recent-failure observation window.

Thresholds are local operational classification inputs, not SLOs.

### Snapshot facts

The repository returns aggregate counts captured at an explicit UTC `as_of`:

- active, paused and currently due source schedules;
- pending, running, stale-running and recent non-success source dispatches;
- queued and running ingestion runs, stale active run leases and recent failed runs;
- Proposals with no terminal human review decision;
- running and stale-running content-supply cycles;
- recent degraded, failed or abandoned cycles;
- latest terminal cycle state and completion time.

PostgreSQL reads use one repeatable-read transaction. Memory reads use the concrete in-memory repositories under their existing locks. Neither implementation mutates durable state.

### Signal classification

Signals are deterministic:

- `CRITICAL`: at least one stale source-dispatch owner, stale active ingestion lease or stale process cycle;
- `ATTENTION`: any configured backlog threshold is exceeded, any recent non-success count is above the configured threshold, the latest terminal cycle is degraded/failed/abandoned, or active schedules exist while terminal cycle evidence is absent/too old;
- `QUIET`: no active schedule and no queued/running/pending/review work;
- `NOMINAL`: none of the above.

Reason codes are a bounded allowlist and sorted deterministically. The service never repairs the detected condition.

### CLI

Add a one-shot CLI that accepts explicit policy values, prints only the snapshot allowlist as JSON and exits:

- `0`: `QUIET` or `NOMINAL`;
- `2`: `ATTENTION`;
- `3`: `CRITICAL`;
- `64`: invalid input.

No HTTP endpoint, dashboard or alert delivery is added.

## Consequences

### Positive

- Operators and external supervisors gain a safe machine-readable signal.
- Stale ownership is distinguished from ordinary backlog.
- Policy thresholds remain explicit and testable.
- Snapshot evaluation is decoupled from recovery and provider behavior.

### Trade-offs

- This is a snapshot, not a metrics time series.
- Local thresholds do not establish production SLOs.
- External alerting and dashboards remain separate adoption work.

## Non-goals

- recovery, heartbeat, claim, retry or backoff;
- schedule/run/review/projection/publication mutation;
- provider adapters or network access;
- public/Admin HTTP or phone UI;
- metrics backend, alert delivery, deployed SLO or rollback proof;
- Case Builder or Flow Composer.