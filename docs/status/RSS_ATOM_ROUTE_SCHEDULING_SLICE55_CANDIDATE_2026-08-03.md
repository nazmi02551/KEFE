# RSS/Atom Route Scheduling Slice 55 Candidate — 2026-08-03

## Candidate scope

Slice 55 adds a narrow route-bound schedule creation and reconciliation service over the existing generic source scheduler.

Callers provide only:

- route code;
- external feed locator;
- first due time;
- recurrence interval;
- maximum dispatch attempts.

The service resolves the immutable route, derives the exact acquisition command and delegates schedule creation to the existing generic scheduler. Adapter, pipeline, configuration hash, locale and jurisdiction cannot be overridden by callers.

Reconciliation resolves the route by its unique adapter code and fails closed if any immutable schedule field drifts from the route-derived acquisition command.

## Preserved generic scheduler

No scheduler schema or state-machine replacement is introduced. The existing generic scheduler remains authoritative for:

- deterministic schedule keys;
- idempotent creation;
- due planning;
- dispatch claims and heartbeats;
- stale recovery and retry limits;
- pause, resume and retirement;
- memory and PostgreSQL persistence.

## Production boundary

Production composition constructs `RssAtomRouteScheduleService` from the existing empty route registry and generic scheduler. It creates:

- zero route schedules;
- zero route registry entries;
- zero concrete providers or feed URLs;
- zero live external captures.

No automatic review, materialization, projection, Case creation or publication is enabled.

## Candidate validation

Pending exact-head CI. Required evidence:

- RSS Atom Route Scheduling CI memory and PostgreSQL jobs;
- parent source scheduler, RSS/Atom route and ingestion-worker architecture gates;
- route-schedule idempotency and drift tests;
- full schedule-dispatch-to-FEED_ITEM vertical test;
- API CI;
- MVP Beta Gates;
- Global Readiness.

Do not call PASS or mark ready until every required workflow is green on one exact runtime SHA. Do not merge before the active parent stack.