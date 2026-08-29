# ADR-0069 — Server-authoritative analytics event spine

**Status:** Accepted  
**Date:** 2026-08-01  
**Original issue:** #178  
**Canonical convergence:** #378 / parent PR #377  
**Parent program:** #177 / F1  
**Capabilities:** CAP-114, CAP-115, CAP-116, CAP-117, CAP-124

## Context

KEFE already has a transactional domain outbox and a documentation-level Analytics Event Dictionary, but no runtime boundary that converts authoritative domain events into durable, privacy-safe analytics events.

Without a common spine, later activation, quality, trust/safety, Signal, reporting, research, growth, commercial and FinOps features would be likely to:

- invent incompatible event names and payloads;
- trust client-declared state for server-authoritative facts;
- copy raw response or private-reason data into analytics;
- lose CaseVersion, session or contribution-class provenance;
- duplicate delivery after outbox retry;
- couple the domain to a third-party analytics provider.

## Decision

### 1. Separate bounded context

Analytics projection is a separate bounded context. It consumes declared domain/outbox events and stores governed analytical facts. It does not mutate domain aggregates, decide truth, qualify Signal, publish content or infer user personality/ideology.

### 2. Server-authoritative source

The first runtime slice projects only from the transactional domain outbox. There is no client analytics ingestion endpoint in this slice.

Supported source events are explicitly registered and versioned. Unknown source events are ignored rather than accepted generically.

Initial mappings:

- `weigh.started` → `activation.weigh_started` v1;
- `weigh.committed` → `activation.weigh_committed` v1;
- `result.revealed` → `activation.result_revealed` v1;
- `perspective.viewed` → `quality.perspective_viewed` v1;
- `exposure.recorded` → `quality.exposure_recorded` v1;
- `intervention.exposed` → `quality.intervention_exposed` v1;
- `decision.revised` → `quality.decision_revised` v1.

### 3. Registry and allowlists

Every analytics definition declares:

- source event name and source version;
- analytics event name and version;
- privacy and retention class;
- metric families;
- allowed payload fields;
- actor, CaseVersion and contribution-class extraction rules.

Only allowlisted fields are copied. Actor/session/CaseVersion/contribution provenance is stored in typed columns rather than left inside arbitrary payload JSON.

### 4. Privacy boundary

The projector rejects source payloads containing forbidden analytics fields, including raw responses, private reason text/tags, personality, ideology, psychometric, bias or causal-inference fields.

`has_reason` is an allowed boolean fact; reason text, tags and response bodies are not.

This slice does not create demographic segments, cohorts or user profiles.

### 5. Idempotency

The analytics event ID is deterministic over source event ID + analytics name + analytics version. Memory and PostgreSQL stores enforce one event per source-definition-version tuple.

Outbox retry may invoke the projector repeatedly, but cannot duplicate the analytics fact.

### 6. Provider neutrality

The domain and analytics modules do not import vendor SDKs. The outbox worker composes:

1. the internal analytics projection transport;
2. the existing replaceable external/logging transport.

A later broker, warehouse or analytics provider remains an adapter concern.

### 7. Contribution-class integrity

Where the source event carries contribution-class provenance, analytics stores the canonical code separately. The projector accepts only:

- `CORE_PRE_RESULT`;
- `EXPOSED`;
- `ADVOCACY_SUPPORT`.

Missing provenance remains null; it is never guessed from percentages or UI routes. Initial `weigh.committed` projection is explicitly `CORE_PRE_RESULT` because Commit occurs before collective exposure under the active runtime contract.

### 8. No metric claims yet

This spine records governed facts. It does not calculate Meaningful Weighs/WAU, funnels, trust scores, Signal or FinOps reports. Those are later projections with their own contracts.

## Consequences

- Later reporting and experimentation can reuse one event lineage.
- Privacy failures become dead-letter-visible outbox failures rather than silent leakage.
- Existing API/OpenAPI remains unchanged.
- PostgreSQL gains an isolated `analytics` schema.
- PR #68 ingestion remains outside this slice; adoption is handled in F2.
- CI proves code/contract behavior only, not deployed observability, statistical validity or business KPI correctness.
