# F4/F5 Analytics Actor Deletion Anonymization — 2026-08-29

Status: IMPLEMENTATION CANDIDATE / LOCAL GREEN / EXACT-HEAD EVIDENCE PENDING

Issue: #383

Parent: PR #381 / `8874739e01085b7aaef442daca54be5e7994de8d`

Capabilities: CAP-085, CAP-115 foundation hygiene

## Purpose

Keep the accepted self-service deletion claim truthful after the analytics
event spine and activation journey introduced two retained nullable actor
references.

## Candidate boundary

- sets `analytics.analytics_event.actor_id` and
  `analytics.activation_journey.actor_id` to null;
- preserves event and journey rows, session and CaseVersion lineage, source
  event lineage, stage timestamps and governed classifications;
- performs PostgreSQL anonymization inside the existing deletion transaction;
- uses the shared in-memory analytics store under the deletion lock;
- repairs remaining references before returning an existing append-only
  receipt;
- backfills actors already marked `DELETED` or covered by an existing receipt
  through migration `20260829_0040`;
- treats future retained analytics actor columns as contract/catalog drift;
- adds no export, HTTP, admin, mobile or aggregate reporting surface.

## Local candidate evidence

- full API Ruff: PASS;
- privacy, analytics-event and activation-journey focused tests: 19 PASS;
- full API unit/behavior package: 569 PASS, 106 PostgreSQL-opt-in skip;
- privacy and analytics actor deletion contracts: PASS;
- analytics event spine and activation journey contracts: PASS;
- contract-sync and composed OpenAPI drift gate: PASS;
- canonical migration chain: 40 files, root `20260727_0001`, head
  `20260829_0040`;
- migration source SHA-256:
  `ce79a4f4481296fe8885321246508718ded4ab725af367c15a66c5690fa2a188`;
- offline schema SHA-256:
  `e54a9aa0ecabc64f15d365fd30b93ffda4bb5e92bb8b0949bdd8b5937b1481c3`.

No local PostgreSQL service is configured in this environment. Transaction,
restart, receipt-replay, exact actor-column catalog and 0039-to-0040 backfill
tests are committed but remain exact-head CI evidence rather than local PASS.

## Explicit non-claims

This candidate does not expand the privacy export or delete governed analytics
facts. It defines no Meaningful Weigh, WAU, funnel rate, cohort, profile,
personality, ideology, psychometric, bias, normative or causal inference. It
does not claim legal certification, production deployment, F4/F5 completion,
human review or lifecycle promotion.

No mobile runtime changes are included. Standard CI Android artifacts remain
build evidence; this backend privacy repair does not warrant an APK handoff.
