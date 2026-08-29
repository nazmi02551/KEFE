# ADR-0135 — Reproducible session activation journey

**Status:** Accepted implementation boundary  
**Date:** 2026-08-29  
**Issue:** #380  
**Parent:** PR #379 / ADR-0069  
**Capability:** CAP-115

## Context

ADR-0069 establishes durable, server-authoritative analytics facts but
intentionally does not calculate a funnel or KPI. CAP-115 requires a
reproducible activation-funnel foundation.

The accepted CAP-114 north-star name and quality guardrails do not currently
provide an executable numerator, denominator, weekly window or aggregate
privacy threshold. Treating an observed event sequence as a successful funnel
or Meaningful Weigh would invent a product/methodology decision.

## Decision

### 1. Session-level observation, not a KPI

The analytics store maintains one internal activation journey per session. It
records independent observations for:

- `activation.weigh_started` v1;
- `activation.weigh_committed` v1;
- `activation.result_revealed` v1.

Each observation stores the authoritative event occurrence time and source
event ID. Missing observations remain null. The projection does not assign a
success, completion or abandonment label.

### 2. Deterministic reconstruction

The journey can be rebuilt from stored analytics events alone. Delivery order
does not change the result. If more than one source event observes the same
stage, the earliest `(occurred_at, source_event_id)` tuple is retained.

Raw response, private-reason text/tags or inferred traits are neither required
nor copied.

### 3. Provenance consistency

All observed stages in a journey must agree on `session_id` and
`case_version_id`. Non-null `actor_id` values must agree. A conflict fails
closed; the event and journey update are both rejected.

The projection never guesses actor or CaseVersion provenance from a route,
percentage or later collective result.

### 4. Atomic persistence

Memory and PostgreSQL adapters persist the governed analytics event and its
journey update as one operation. PostgreSQL serializes updates per session
inside the transaction. Retry of the same analytics event is idempotent.

Migration backfills any already-stored activation events using the same
earliest-observation rule. Conflicting actor or CaseVersion provenance aborts
the migration rather than silently choosing one value.

### 5. No reporting surface

This slice adds no public, mobile or admin endpoint. It emits no aggregate,
cohort, rate, ratio or user profile. A later reporting contract must define
privacy thresholds and the exact metric semantics before such data can leave
the internal projection boundary.

## Consequences

- Activation stage facts are reproducible and auditable without declaring a
  KPI.
- Out-of-order outbox delivery cannot corrupt journey state.
- Provenance conflict remains visible through the existing outbox failure and
  dead-letter behavior.
- CAP-114 Meaningful Weighs/WAU and aggregate funnel reporting remain separate
  decisions.
