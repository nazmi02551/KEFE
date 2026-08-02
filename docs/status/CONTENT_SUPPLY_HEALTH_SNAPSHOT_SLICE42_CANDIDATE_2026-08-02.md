# Content-Supply Operational Health Snapshot — Slice 42 Candidate

- Date: 2026-08-02
- Issue: #209
- Branch: `feature/content-supply-health-snapshot-slice42`
- Base: PR #207 / Slice 41 exact head
- Status: Candidate — exact-head CI pending

## Candidate capability

This slice adds a provider-neutral, read-only, privacy-safe operational snapshot over durable content-supply state:

- source acquisition schedules and dispatches;
- ingestion runs and active run leases;
- unreviewed Proposal backlog;
- bounded content-supply process cycles.

The snapshot classifies local signals as `QUIET`, `NOMINAL`, `ATTENTION` or `CRITICAL` using explicit policy thresholds.

## Locked behavior

- `CRITICAL` is caused only by stale dispatch, stale ingestion lease or stale process-cycle ownership;
- `ATTENTION` is caused only by explicit backlog, recent non-success, latest-cycle or cycle-silence rules;
- reason codes are bounded, unique and sorted;
- thresholds are local operational policy, not production SLOs;
- PostgreSQL reads use a repeatable-read, read-only transaction;
- memory reads use the live repository instances under their existing locks;
- no recovery, retry, heartbeat, claim, review, projection or publication occurs;
- no raw locator, storage reference, payload, provider response, credential, user data, title or reviewer reference enters the snapshot;
- one-shot CLI emits allowlist JSON and deterministic exit codes;
- no HTTP, dashboard, alert delivery or phone surface is introduced.

## Candidate evidence included

- signal classification and reason-order tests;
- live in-memory aggregate parity test;
- CLI policy, UTC parsing, output allowlist and exit-code tests;
- PostgreSQL baseline-delta aggregate/read-only test;
- architecture fitness enforcing read-only ports and SQL;
- existing Slice 40 and Slice 41 exact gates remain in API CI.

## Explicit non-claims

This candidate does not prove or introduce:

- deployed metrics, alerts, dashboards or SLOs;
- production rollback readiness;
- a running process manager or daemon;
- provider credentials, rate-limit controls or provider compliance;
- real provider/network operation;
- automatic editorial decisions or publication;
- Admin UI/HTTP, Case Builder, Flow Composer or phone behavior.

Do not mark Slice 42 PASS until API CI, MVP Beta Gates and Global Readiness all succeed on the same runtime SHA.
