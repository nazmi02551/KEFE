# F5 Activation Journey Projection — 2026-08-29

Status: IMPLEMENTATION CANDIDATE / LOCAL AND EXACT-HEAD EVIDENCE PENDING

Issue: #380

Parent: PR #379 / `f8d164b3dbc87d7b57f3d34f4b952540d550ac9c`

## Purpose

Advance the CAP-115 reproducibility foundation without inventing the missing
CAP-114 Meaningful Weighs/WAU formula or aggregate privacy policy.

## Candidate boundary

- projects only three registered server-authoritative activation facts;
- keeps stage occurrence and source-event lineage independently;
- reconstructs deterministically under retry and out-of-order replay;
- backfills already-stored activation facts and aborts on provenance conflict;
- rejects actor or CaseVersion conflict atomically;
- persists event and journey together in memory and PostgreSQL;
- extends the migration chain with
  `20260829_0038 -> 20260829_0039`;
- adds no HTTP, admin or mobile surface.

## Explicit non-claims

This candidate does not define Meaningful Weighs/WAU, a weekly window,
numerator, denominator, funnel rate, success, abandonment, cohort or privacy
threshold. It does not create a user profile or copy response/private-reason
data. It does not prove deployed outbox operation, warehouse delivery,
retention enforcement, production observability, human review or lifecycle
promotion.

No mobile runtime change is included. Normal CI artifacts are build evidence;
this backend projection does not warrant an APK handoff.

## Local candidate evidence

- full API Ruff: PASS;
- activation journey + analytics focused package: 15 PASS;
- full API unit/behavior package: 568 PASS, 104 PostgreSQL-opt-in skip;
- activation journey contract: PASS;
- analytics event spine contract: PASS;
- contract-sync: PASS;
- production API runtime composition: PASS;
- canonical migration chain: 39 files, root `20260727_0001`, head
  `20260829_0039`;
- migration source SHA-256:
  `bf1339f70349bf9ed2fc0f5b9e80bf413085f5dca29997662d7767aa034b5ea1`;
- offline schema SHA-256:
  `cd83d16213fbf0ec1a1807b8966f3a39fb485713ed8955c12966e32400aa21ac`.

No local PostgreSQL service is configured in this environment. The new
service-backed atomicity/backfill test and downgrade/upgrade drill therefore
remain exact-head CI evidence, not a local PASS claim.
