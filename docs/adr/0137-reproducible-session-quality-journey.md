# ADR-0137 — Reproducible session quality journey

**Status:** Accepted implementation boundary  
**Date:** 2026-08-29  
**Issue:** #385  
**Parent:** PR #384 / ADR-0069  
**Capability:** CAP-116

## Context

ADR-0069 establishes durable, server-authoritative quality facts for commit,
Perspective, exposure, intervention and decision revision. It intentionally
does not define a quality score, Deep Weigh success, aggregate rate or causal
effect. CAP-116 still needs a reproducible foundation before any later metric
contract can be implemented safely.

PR #381 established an internal activation journey that records independent
observations without labeling a session successful or abandoned. The same
observation model can make the registered quality facts reconstructable
without inventing a quality methodology.

## Decision

### 1. Session-level observation, not quality judgment

The analytics store maintains one internal quality journey per session. It
records independent observations for:

- `activation.weigh_committed` v1;
- `quality.perspective_viewed` v1;
- `quality.exposure_recorded` v1;
- `quality.intervention_exposed` v1;
- `quality.decision_revised` v1.

Each observation stores only the authoritative event occurrence time and
source event ID. Missing observations remain null. The journey does not copy
event payload, count events, score quality or label the session.

### 2. Data minimization and provenance

The journey key is `session_id`. It may preserve a non-null `case_version_id`
already present on governed analytics events. All non-null CaseVersion values
in one journey must agree; a conflict fails closed.

The journey does not store `actor_id`. Actor identity, raw response,
private-reason text/tags, revision content, exposure metadata and inferred
traits are neither required nor copied. The existing analytics event remains
the source of any separately allowlisted payload fact such as `has_reason`.

### 3. Deterministic reconstruction

The journey can be rebuilt from stored analytics events alone. Delivery order
does not change the result. If more than one source event observes the same
stage, the earliest `(occurred_at, source_event_id)` tuple is retained.

### 4. Atomic persistence

Memory and PostgreSQL adapters persist the governed analytics event and all
supported journey updates as one operation. PostgreSQL serializes updates per
session inside the transaction. Retry of the same analytics event is
idempotent.

Migration `20260829_0041` backfills already-stored quality events with the same
earliest-observation rule. Conflicting non-null CaseVersion provenance aborts
the migration rather than silently selecting a value.

### 5. No reporting surface

This slice adds no public, mobile or admin endpoint. It emits no aggregate,
cohort, score, rate, threshold, recommendation, user profile or causal claim.
A later reporting contract must define exact metric semantics and privacy
thresholds before any aggregate leaves the internal analytics boundary.

## Consequences

- Registered quality observations become reproducible and auditable.
- Out-of-order outbox delivery cannot change the selected stage lineage.
- Quality methodology and aggregate privacy decisions remain explicit future
  authority boundaries.
- CAP-116 and F5 are not promoted by this implementation candidate.
