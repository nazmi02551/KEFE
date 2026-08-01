# KEFE Analytics Event Spine — Slice 31 Verification

**Date:** 2026-08-01  
**Issue:** #178  
**Parent program:** #177 / F1  
**Pull request:** #179  
**Capabilities:** CAP-114, CAP-115, CAP-116, CAP-117, CAP-124

## Verified runtime

`c6002ac344bc7d8fb473ef8035dbff43a8c4f0e1`

A later documentation-only commit on PR #179 does not redefine this verified runtime.

## Exact-SHA evidence

All required workflows completed successfully on the same runtime SHA:

- API CI #1010 / run `30717914102` — SUCCESS
- Mobile CI #795 / run `30717914107` — SUCCESS
- MVP Beta Gates #514 / run `30717914103` — SUCCESS
- Global Readiness #408 / run `30717914126` — SUCCESS

Verified gates include:

- Python lint and unit tests;
- contract synchronization and OpenAPI drift;
- analytics event spine architecture fitness;
- single-head Alembic migration;
- analytics PostgreSQL round-trip/idempotency;
- existing MVP, privacy, catalog and global PostgreSQL regressions;
- Flutter format, analyze and test suites;
- internal candidate build/upload gates.

## Contract-first records

- ADR-0069 `docs/adr/0069-server-authoritative-analytics-event-spine.md`
- executable contract `docs/contracts/analytics-event-spine-slice31.v1.json`
- platform sequencing `docs/roadmap/PLATFORM_FOUNDATION_COMPLETION.md`

## What is implemented

- a provider-neutral analytics bounded context;
- a versioned registry for declared authoritative domain/outbox events;
- deterministic UUIDv5 analytics identity by source event + analytics definition version;
- typed actor, session, CaseVersion and contribution-class provenance;
- recursive forbidden-field rejection and payload allowlists;
- explicit exclusion of raw responses, private reason text/tags and personality/ideology/psychometric/bias/causal-inference fields;
- idempotent in-memory and PostgreSQL stores;
- isolated `analytics.analytics_event` persistence;
- analytics projection composed into the transactional outbox worker before the existing replaceable logging transport;
- unknown domain events remain outside analytics projection and continue through the external transport;
- linear migration `20260730_0018 → 20260801_0019`.

Initial governed event mappings:

- `weigh.started` → `activation.weigh_started` v1;
- `weigh.committed` → `activation.weigh_committed` v1;
- `result.revealed` → `activation.result_revealed` v1;
- `perspective.viewed` → `quality.perspective_viewed` v1;
- `exposure.recorded` → `quality.exposure_recorded` v1;
- `intervention.exposed` → `quality.intervention_exposed` v1;
- `decision.revised` → `quality.decision_revised` v1.

## Explicit exclusions

This slice does not implement:

- a client analytics ingestion endpoint;
- a third-party analytics SDK;
- dashboards or KPI calculation;
- cohort or demographic segmentation;
- Meaningful Weighs/WAU calculation;
- Signal qualification;
- billing/entitlement;
- research export;
- production observability/SLO evidence.

CI does not prove human usability, statistical validity, production-provider delivery or business KPI correctness.

## Rejected candidates

The following heads are not PASS:

- `842c3a63ea7cdf8092e10e7440817d4fc946e7ad` — Mobile CI did not run for API/contract changes.
- `ac8646add51d17a65bf5a2a0ea6b6901e26a6598` — migration graph had multiple heads.
- `52f80a5e6b8da3075c5aeaaba1b3de4946b9b386` — diagnostic head confirmed the competing migration heads.

Only `c6002ac344bc7d8fb473ef8035dbff43a8c4f0e1` is the verified Slice 31 runtime.

## Phone artifact policy

The workflows built internal APK artifacts as regression evidence, but this slice changes no phone-visible product behavior. No new user-facing APK distribution is warranted for Slice 31.

## Continuation

PR #179 remains stacked on PR #173 and must not be merged before its parent chain. The next platform-foundation lane is F2: compatibility review and active-line adoption of provider-neutral ingestion plus explicit reviewed Candidate Case / Decision Problem / Question Draft projection into Content Authoring DRAFT.
