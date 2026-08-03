# ADR-0091: Route-bound RSS/Atom schedule creation and deterministic reconciliation

- Status: Accepted
- Date: 2026-08-03
- Slice: 55

## Context

The generic source scheduler intentionally accepts adapter, pipeline, version, configuration and context fields so it can support many future source types. A caller that uses those generic parameters directly for RSS/Atom can accidentally schedule a registered route with a different pipeline, parser-derived configuration hash, locale or jurisdiction.

KEFE must bind scheduled RSS/Atom capture to the immutable route without replacing the proven generic schedule, lease, retry and dispatch state machine.

## Decision

Introduce a provider-neutral `RssAtomRouteScheduleService`.

1. Callers supply only route code, external locator, first due time, interval and maximum dispatch attempts.
2. The service resolves the exact `RssAtomRouteBundle` from `RssAtomRouteRegistry` and obtains the acquisition command from `route.acquisition_command(external_locator)`.
3. Adapter code, pipeline code/version, configuration hash, taxonomy/methodology context, locale and jurisdiction are copied only from that route-derived command.
4. The service delegates creation to `SourceAcquisitionSchedulerService`; it does not duplicate schedule persistence, planning, leasing, heartbeat, retry, pause/resume/retire or dispatch execution.
5. The returned schedule key must equal the existing canonical generic schedule key computed over the route-derived command and cadence.
6. Reconciliation resolves the route by the schedule's unique adapter code and compares every immutable acquisition-command field. Any drift fails closed with a bounded route-schedule error.
7. A missing route fails closed. There is no fallback to a generic adapter, preview fixture, alternate pipeline or caller-supplied configuration.
8. Production composition may construct the route scheduling service, but the production route registry remains empty; therefore no production route schedule can be created.
9. Human review remains mandatory. Dispatch can only reach review-required `FEED_ITEM` proposals.

## Persistence decision

No schema column is added solely for route code. The route registry already enforces adapter-code uniqueness, and the schedule persists the route-derived adapter, pipeline, configuration hash and context. The route can therefore be recovered by adapter code and reconciled against the persisted immutable schedule configuration.

## Execution path

`route code + feed URL + cadence → exact route command → generic schedule → due dispatch → PUBLIC capture → immutable evidence → SourceArtifact → exact ingestion run → worker → FEED_ITEM proposals`

## Consequences

The generic scheduler remains reusable and unchanged. RSS/Atom activation gains a narrow safe entry point and a deterministic reconciliation check. A future Admin UI can use this service without exposing arbitrary pipeline/configuration fields.

This ADR does not register a concrete provider/feed, approve provider terms, prove deployed egress/object storage, introduce a new scheduler state machine, automate review/publication or expose phone-facing feed behavior.