# KEFE — Current State & Handoff

**Purpose:** Durable engineering/product checkpoint so work can resume from the repository without depending on chat history.

**Last updated:** 2026-07-27
**Canonical implementation branch:** `main`
**Repository:** `nazmi02551/KEFE`

## 1. Product authority

Implementation must remain compatible with the approved KEFE documentation ecosystem. The current code is an executable slice of the broader product; it does not redefine open product decisions by accident.

Core invariants already treated as binding:

- Product category: Global Decision & Perspective Platform.
- Primary loop: Discover → Context → Weigh → Commit → Reveal → Perspective → Reflect → Share.
- Commit First: community/result layers are hidden until the user's first server-confirmed decision.
- Blind First is not the default; BLIND_FIRST is an optional experiment modifier.
- CaseVersion is immutable once published; decisions are pinned to the version seen by the user.
- Consumer results use explicit data layers; Trusted is the current M0 reveal layer.
- No guilt referenda, no voting on scientific/legal facts, no high-risk autonomous AI publishing.
- Architecture direction: Flutter + Next.js + FastAPI modular monolith + PostgreSQL + Redis + S3-compatible storage + transactional outbox.

## 2. Executable state on `main`

The regular walking skeleton is:

`Explore → Case → Weigh → Commit → Reveal`

The first-use path is:

`Welcome → First Case → Weigh → Commit → Reveal → Continue as Guest → Explore`

### Backend

Implemented:

- FastAPI modular-monolith foundation.
- Decision repository port with memory and PostgreSQL adapters.
- Alembic migrations and PostgreSQL integration CI.
- Linearizable commit boundary with row locking.
- Actor-scoped commit idempotency.
- Transactional outbox plus durable provider-neutral outbox worker.
- Guest identity boundary using opaque bearer credentials; raw tokens are not persisted server-side.
- Revocable guest sessions.
- Guest admission guard with rate-limiting/device-integrity ports.
- Public bounded `GET /v1/cases` Explore read model.
- Canonical Case read plus Weigh session, response, commit and reveal endpoints.
- Checked-in OpenAPI contract and drift gate.
- Machine-readable error/config/schema contracts and ADRs.

### Mobile

Implemented:

- Flutter client foundation.
- Riverpod application state.
- GoRouter route shell.
- Light/Dark/System theme support.
- Turkish/English semantic copy foundation.
- Secure guest credential storage adapter.
- Offline per-Case draft persistence.
- Commit idempotency key persisted before first commit attempt.
- Recovery phases: editing → commitPending → committedAwaitingReveal.
- Same-key uncertain-commit retry.
- Reveal-only retry after confirmed commit.
- Explore screen.
- Canonical `/case/:caseId` deep-link route.
- Explore → Case and direct deep-link widget coverage.
- Two-step first-use onboarding with no long tutorial.
- First real low-risk Case used to demonstrate product value.
- Onboarding completion persisted at the first Reveal boundary so restarts do not replay a completed tutorial.
- Explicit guest continuation from first Reveal into Explore.
- Direct Case deep links bypass onboarding rather than being trapped by the first-use gate.

## 3. Recent merged milestones

Most relevant merged PRs, newest first:

- PR #17 — First-use onboarding through first Reveal.
- PR #16 — Explore discovery and deep-linkable Case flow.
- PR #14 — Secure mobile session and uncertain commit recovery.
- PR #13 — Flutter M0 mobile foundation.
- PR #11 — Guest admission hardening and device-integrity port.
- PR #10 — Secure guest identity boundary.
- PR #9 — Durable provider-neutral outbox delivery worker.
- PR #8 — Commit concurrency hardening and contract sync.
- PR #7 — PostgreSQL persistence and transactional outbox baseline.
- PR #6 — First executable Case → Weigh → Commit → Reveal vertical slice.

Note: PR #15 and #16 represent the same Explore branch lineage; #16 is the latest canonical merge record for that slice.

## 4. CI baseline

A change is not considered complete until applicable gates are green.

Backend gates include:

- Ruff lint.
- contract sync check.
- generated OpenAPI export and checked-in drift gate.
- unit tests.
- PostgreSQL migrations + seed + integration tests.

Mobile gates include:

- dependency resolution.
- Dart formatting.
- Flutter analyze.
- widget tests.

PR #17 passed the complete Mobile CI gate before merge.

## 5. Documentation synchronization obligation

The executable repository has advanced beyond the last rendered office-document milestone.

At the next documentation-sync milestone, patch the relevant approved/working documents to include at least:

- PostgreSQL persistence adapter and Alembic baseline.
- linearizable commit concurrency/idempotency behavior.
- durable outbox worker semantics.
- real guest identity boundary and admission controls.
- Flutter/Riverpod/GoRouter mobile foundation.
- secure credential storage.
- offline per-Case drafts and uncertain-commit recovery.
- Explore read model and canonical `/case/:caseId` deep links.
- first-use onboarding through first Reveal and guest continuation.
- CI architecture/contract/OpenAPI fitness gates.

Do not regenerate DOCX/PDF after every small code commit. Regenerate and visually verify the document package at meaningful milestone boundaries to avoid churn and document drift.

## 6. Open product decisions that code must not accidentally close

Unless explicitly approved in the product documentation/decision log, keep these configurable or provisional:

- final 3-vs-4 tab primary navigation.
- final branded commit CTA wording; semantic action remains COMMIT.
- final Quick Weigh reveal timing.
- WAU vs MAU North Star denominator.
- long-term guest retention policy.
- final MVP CALL scope.
- country rollout ordering.
- Values activation/validation schedule.
- final Atlas trust thresholds and consumer Raw/Trusted presentation.
- advanced Civic/P2+/P3 review/delay rules.
- final KEFE+ launch timing.
- exact timing and UX of optional guest→account upgrade after first value demonstration.

## 7. Recommended next engineering sequence

Continue in thin vertical slices rather than broad scaffolding.

1. **Case experience depth**
   - Context/source surfaces behind explicit contracts;
   - progressive disclosure without leaking result/community data;
   - question-type expansion without hard-coding format behavior into screens;
   - preserve CaseVersion pinning and Commit First.
2. **Reason capture + Perspective**
   - short structured reason capture;
   - safe argument/perspective read model;
   - no classic engagement-first comment feed.
3. **M0 milestone documentation sync**
   - Engineering Blueprint and related authority docs;
   - DOCX → reviewed PDF render;
   - refreshed documentation package/manifest.

## 8. Recovery procedure for a new chat/session

Start by reading this file from `main`, then inspect:

1. open PRs;
2. most recent merged PRs;
3. latest CI status;
4. relevant ADR/contract files for the requested slice.

Do not reconstruct project state from old chat transcripts when repository state can answer it.

Suggested handoff prompt:

> Continue KEFE from `nazmi02551/KEFE`. Read `docs/project/CURRENT_STATE.md` from `main` first, then inspect open PRs and recent CI. Treat the approved KEFE documentation ecosystem as product authority. Continue the recommended next engineering slice without silently closing open product decisions.
