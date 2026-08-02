# ADR-0077: Bounded Content-Supply Process Cycle and Durable Heartbeat

- Status: Accepted
- Date: 2026-08-02
- Decision owners: KEFE Product and Engineering
- Related: ADR-0073, ADR-0074, ADR-0075, ADR-0076, Issues #180 and #206

## Context

Slices 37–40 established durable worker leases, exact resumable ingestion plans, provider-neutral source acquisition and durable source cadence/dispatch supervision. Those capabilities are individually safe, but production still lacks one finite application-level process cycle that coordinates them and leaves durable operational evidence.

Embedding an unbounded loop, cron parser or provider-specific daemon inside the domain would mix deployment concerns with runtime semantics and would make recovery, testing and operator evidence weaker. An external platform scheduler or process manager should be able to invoke a single bounded cycle repeatedly. The cycle must not bypass the existing dispatch and ingestion leases.

## Decision

Introduce a provider-neutral `ContentSupplyCycleService.run_once(...)` and a one-shot CLI entrypoint.

A cycle executes three ordered, independently bounded phases:

1. plan due source acquisition occurrences;
2. execute pending source acquisition dispatches;
3. execute exact registered ingestion pipeline targets.

Every loop is bounded by immutable command values. Each phase stops early when its delegated service reports `IDLE`. There is no internal sleep, polling, retry/backoff or daemon mode.

### Exact command

The command contains:

- `worker_ref`;
- `cycle_ttl_seconds`;
- `dispatch_ttl_seconds`;
- `ingestion_ttl_seconds`;
- `plan_budget`;
- `dispatch_budget`;
- an ordered tuple of exact `(pipeline_code, pipeline_version, max_runs)` targets.

Pipeline targets are explicit and duplicate exact identities are rejected. The command produces a deterministic `plan_hash`; no provider, locale, title, payload or Case-type inference is allowed.

### Durable cycle journal

Create `ingestion.content_supply_cycle` with states:

- `RUNNING`;
- `IDLE`;
- `SUCCEEDED`;
- `DEGRADED`;
- `FAILED`;
- `ABANDONED`.

A running cycle has exact worker ownership, heartbeat and expiry. Heartbeat updates aggregate counters and extends expiry. Terminal completion requires the same active owner. A stale `RUNNING` cycle is recovered only to `ABANDONED`; recovery never changes source dispatches or ingestion runs because those aggregates retain their own lease/recovery semantics.

The journal stores only aggregate operational counters, exact cycle identity, plan hash, timestamps and a bounded error code. It never stores source locators, raw storage references, provider payloads, Proposal payloads, credentials, user data or titles.

### Outcome rules

- `IDLE`: no occurrence planned, no dispatch executed and no ingestion run executed.
- `SUCCEEDED`: at least one delegated unit completed and no delegated non-success outcome occurred.
- `DEGRADED`: the finite cycle completed but any delegated operation returned retryable failure, final failure, blocked or lease-lost.
- `FAILED`: the supervisor itself encountered an unexpected failure and successfully recorded a terminal failure.
- `LEASE_LOST`: returned by the service when the expired/foreign cycle owner can no longer heartbeat or complete; the durable record remains recoverable as stale `RUNNING`.

Delegated outcomes are observed, not rewritten. The cycle never retries a failed dispatch, reviews a Proposal, projects a Proposal or publishes content.

### CLI

Add a one-shot CLI that accepts only explicit bounded arguments, invokes one cycle, prints the privacy-safe operational result as JSON and exits deterministically:

- `0`: `IDLE` or `SUCCEEDED`;
- `2`: `DEGRADED`;
- `3`: `FAILED` or `LEASE_LOST`;
- `64`: invalid CLI/configuration input.

No daemon flag or internal scheduling loop is provided.

## Consequences

### Positive

- External schedulers can invoke a finite, testable process unit.
- Crash evidence and stale process detection become durable.
- Existing work-level leases remain authoritative.
- Operational output is privacy-safe and provider-neutral.
- Multiple process replicas remain safe because delegated repositories already use exclusive claims.

### Trade-offs

- A deployment platform is still required to invoke the CLI repeatedly.
- This does not prove production SLOs, alerts, rollback or provider compliance.
- Aggregate counters do not replace full metrics/telemetry infrastructure.

## Non-goals

- continuous daemon loop;
- cron or timezone scheduling;
- OS/Kubernetes/systemd supervision manifests;
- provider adapters, network calls or credentials;
- autonomous retry/backoff;
- automatic review, projection or publication;
- Admin UI/HTTP operations;
- Case Builder or Flow Composer.