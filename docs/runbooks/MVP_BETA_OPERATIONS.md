# KEFE MVP Beta Operations Runbook

Status: MVP repository-owned release evidence
Date: 2026-07-30
Authority: ADR-0036 / Issue #93

## 1. Purpose

This runbook separates automated repository proof from real deployment and human beta evidence. Passing CI does not by itself authorize a public/store release.

## 2. Critical-path invariants

The core path is `Explore → Case → Weigh → Commit → Reveal`.

During any provider degradation:

- existing guest identity and already-started local draft continuity remain available where possible;
- a possibly successful Commit is never silently retried with a different idempotency key;
- Reveal never opens before a server-authoritative Commit;
- account conversion, Community Reason, Share, Consensus and optional enrichment may degrade without fabricating success;
- preview fixtures are never used as a production fallback.

## 3. Kill-switch / degraded capability matrix

| Capability | Failure response | Core path impact |
| --- | --- | --- |
| OTP delivery | Return `AUTH_OTP_DELIVERY_UNAVAILABLE`; keep guest continuation | None |
| Community Reason | Hide/retry contribution surface; do not publish pending text | None |
| Share | Retryable Share error; no token fabricated | None |
| Consensus WE | Retryable/empty WE surface; never replace Collective Result | None |
| AI enrichment | Curated/default non-AI content only | None |
| Push | No push; in-app journey remains source of truth | None |
| Remote media | Text/context fallback | None |
| Privacy export/delete | Fail closed and retry; never claim deletion without receipt | Account settings only |

Operational switches are configuration/deployment controls. A production deployment must document the concrete switch mechanism (feature flag, routing/config change, or deployment rollback) before beta gate approval.

## 4. Rollback procedure

1. Stop promotion and preserve the failing release SHA/artifacts.
2. Determine whether the incident affects data integrity, Commit idempotency, identity merge, privacy deletion, or only an optional capability.
3. For data-integrity/privacy issues, disable the affected write path before rolling application binaries.
4. Roll back to the last CI-verified release candidate; do not roll back the database across destructive migrations unless a reviewed migration plan explicitly supports it.
5. Run health + identity + one full Golden Path smoke against the rollback target.
6. Verify no queued/outbox work from the failed release can violate the restored contract.
7. Record incident, affected CaseVersions/actors if applicable, and remediation before re-enabling promotion.

## 5. Migration safety

- Alembic must have one linear `head` for the release candidate.
- Migrations are forward-reviewed; destructive rollback is not assumed safe.
- Account merge preserves historical committed sessions with explicit `merged_from_actor_id` lineage.
- Privacy deletion receipts are retained as policy/audit evidence but may not recreate deleted product data.

## 6. Beta smoke after deployment

Required real-environment checks:

1. guest onboarding and first DILEMMA;
2. response edit → Commit → Reveal;
3. uncertain network around Commit and same-key recovery;
4. Perspective and My KEFE history;
5. optional Account Offer and real OTP deliverability;
6. Share open → receiver `Ben de tartayım` → Commit First still enforced;
7. Community Reason tag-only visibility and text moderation hold;
8. privacy export and deletion on a disposable actor;
9. Light/Dark/System + Turkish/English-ready smoke;
10. observability and rollback path verified.

## 7. Gates CI cannot approve

- production OTP provider credentials, routing and deliverability;
- human phone usability checklist;
- current Apple/Google store compliance review;
- editorial CQB acceptance of the launch catalog;
- measured production availability/latency/load SLOs.

Until these have evidence, the maximum honest status is `MVP_CODE_COMPLETE / BETA_GATE_PENDING`.
