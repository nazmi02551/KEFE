# F5 Quality Journey Projection — 2026-08-29

Status: IMPLEMENTATION CANDIDATE / LOCAL EVIDENCE COMPLETE / EXACT-HEAD EVIDENCE PENDING

Issue: #385

Parent: PR #384 / `4af3b1ca12000195b4deb9466e3b01b07a4afb3c`

## Purpose

Advance the CAP-116 reproducibility foundation without inventing a quality
score, Deep Weigh success definition, aggregate rate or causal interpretation.

## Candidate boundary

- projects only five registered server-authoritative quality observations;
- keeps each stage occurrence and source-event lineage independently;
- stores no actor identity and copies no analytics event payload;
- preserves only an optional, non-conflicting CaseVersion reference;
- reconstructs deterministically under retry and out-of-order replay;
- persists the event, activation journey and quality journey atomically when
  one commit event affects both projections;
- backfills already-stored quality facts and aborts on non-null CaseVersion
  conflict;
- extends the migration chain with
  `20260829_0040 -> 20260829_0041`;
- adds no HTTP, admin or mobile surface.

## Explicit non-claims

This candidate does not define or calculate a quality score, source ranking,
Perspective ranking, Deep Weigh success, Meaningful Weighs/WAU, quality rate,
cohort, trust score, causal effect or aggregate privacy threshold. It does not
create a user profile or copy response/private-reason data. It does not prove
deployed outbox operation, warehouse delivery, retention enforcement,
production observability, human review, CAP-116 lifecycle promotion or F5
completion.

No mobile runtime change is included. Normal CI artifacts are build evidence;
this backend projection does not warrant an APK handoff.

## Local candidate evidence

- full API Ruff: PASS;
- quality/activation/event-spine focused package: 21 PASS;
- full API unit/behavior package: 575 PASS, 109 PostgreSQL-opt-in skip;
- quality journey contract: PASS;
- analytics event spine contract: PASS;
- activation journey contract: PASS;
- retained analytics actor deletion contract: PASS;
- privacy export/deletion contract: PASS;
- contract-sync: PASS;
- production API runtime composition: PASS;
- canonical migration chain: 41 files, root `20260727_0001`, head
  `20260829_0041`;
- migration source SHA-256:
  `61cb90e91ce83a95dffe890012801df9b775df912dfe0fe95aa4f808724e2f14`;
- offline schema SHA-256:
  `631108bf9e80920fe0da686edf7c61ee9f91bfe5bb886259117eb1d4fece9287`.

No local PostgreSQL service is configured in this environment. The new
service-backed atomicity, dual-projection rollback and migration backfill tests
therefore remain exact-head CI evidence, not a local PASS claim.
