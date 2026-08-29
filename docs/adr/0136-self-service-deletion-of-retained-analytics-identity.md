# ADR-0136 — Self-service deletion of retained analytics identity

**Status:** Accepted implementation boundary  
**Date:** 2026-08-29  
**Issue:** #383  
**Parent:** PR #381 / ADR-0108 / ADR-0135  
**Capabilities:** CAP-085, CAP-115 foundation hygiene

## Context

ADR-0069 and ADR-0135 introduced privacy-bounded internal analytics events and
session activation journeys. Both stores retain a nullable `actor_id` so a
server-authoritative event can be linked while the actor is active.

The accepted self-service deletion implementation in ADR-0108 predates these
tables. It anonymizes retained outbox payloads, but it cannot claim that no
reusable profile reference remains while the two newer analytics columns still
contain the deleted actor UUID.

## Decision

### 1. Remove identity, preserve governed facts

Self-service deletion sets `actor_id` to null in:

- `analytics.analytics_event`;
- `analytics.activation_journey`.

The event and journey rows remain. Their session, CaseVersion, stage, source
event and time lineage is unchanged. This is anonymization of a direct identity
link, not deletion or reinterpretation of an analytics fact.

### 2. Keep the deletion transaction atomic

PostgreSQL performs both updates in the existing actor deletion transaction,
before private product data is removed and the append-only receipt is created.
The in-memory composition uses the same shared analytics store and performs the
same operation under its deletion lock.

### 3. Repair replay and historical rows

Receipt replay first repeats the idempotent analytics anonymization and then
returns the original receipt. It never rewrites, replaces or duplicates that
receipt.

Migration `20260829_0040` removes actor references for rows belonging to actors
already in state `DELETED` or already covered by an append-only deletion
receipt. The downgrade cannot reconstruct deliberately removed identity and is
therefore an intentional no-op.

### 4. Keep the boundary executable

The two retained analytics actor columns form an exact catalog inventory.
Memory and PostgreSQL tests must show that rows and non-identity lineage remain
present while actor references become null. A future retained analytics actor
column is not covered automatically; it must update this contract and its
verification.

### 5. No reporting or inference expansion

Analytics rows are not added to the self-service export. This decision defines
no Meaningful Weigh, WAU, activation rate, funnel, cohort or user profile. It
permits no personality, ideology, psychometric, bias, normative or causal
inference.

## Consequences

- CAP-085 deletion remains truthful after the F5 analytics foundation.
- Historical and replayed deletions converge without mutating receipts.
- Reproducible analytics lineage remains available without a direct actor UUID.
- Aggregate privacy thresholds and KPI semantics remain separate blocked
  decisions.
