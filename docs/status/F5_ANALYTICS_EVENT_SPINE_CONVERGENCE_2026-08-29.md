# F5 Analytics Event Spine Convergence — 2026-08-29

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING

Issue: #378

Parent: PR #377 / `33c681cc00a73b2a405102336f6fe6a1fddd940c`

Source candidate: PR #179 / `ea041f18ccbf3bc10e5bec60f3bc07bb67301f99`

## Purpose

Selectively adopt the accepted ADR-0069 analytics event spine onto the current
canonical stack. PR #179 remains preserved as historical evidence, but its old
branch and migration number are not merged wholesale.

## Candidate boundary

- consumes only registered, server-authoritative transactional outbox events;
- projects allowlisted fields into typed analytics provenance;
- rejects nested private response, reason, personality, ideology,
  psychometric, bias and causal-inference payload keys;
- uses deterministic identity and memory/PostgreSQL uniqueness for replay;
- composes the internal analytics projection before the replaceable logging
  transport without importing a vendor SDK;
- extends the linear migration chain with
  `20260827_0037 -> 20260829_0038`;
- keeps unknown domain events outside analytics while still forwarding them to
  the existing external/logging transport.

## Explicit non-claims

This candidate records governed facts only. It does not calculate Meaningful
Weighs/WAU, activation or quality funnels, cohorts, demographic segments,
trust scores, Signal, Impact, research exports, experiments, billing or FinOps.
It does not prove deployed outbox operation, warehouse delivery, retention
enforcement, production observability, human review or capability lifecycle
promotion.

No mobile runtime changes are included. The normal CI Preview artifact remains
build evidence; this bounded backend convergence does not warrant an APK
handoff.

## Candidate repair

Initial remote head `8434682ca798ddff65ad441477660327b62b1a45`
passed API lint/unit, Mobile, MVP and Global gates, but the API PostgreSQL
downgrade drill proved that `analytics` is a shared pre-existing schema. The
candidate migration incorrectly attempted to drop that schema after dropping
its own table, which PostgreSQL rejected because `result_snapshot` and
`outbox_event` still depend on it.

The repair makes `0038` own only `analytics.analytics_event`: downgrade drops
that table and preserves the shared schema. No projection/runtime behavior is
changed. Exact-head CI must run again on the repaired SHA.
