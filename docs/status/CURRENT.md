# KEFE Current Project Checkpoint

**Updated:** 2026-07-28  
**Repository:** `nazmi02551/KEFE`  
**Default branch:** `main`  
**Latest verified implementation commit:** `9416d4366650c3078d92dbf0b5533e4d1a4cdf39`

This is the **single canonical durable engineering handoff**. Chat history is not a source of truth. At every continuation, read this file from `main`, inspect open PRs/recent CI, then proceed from the repository state.

## 1. Product authority

Current approved baseline:

- KEFE Master Product Document v1.2.0 Approved Canonical
- KEFE Documentation Governance v1.3.2 Approved
- KEFE Product Bible v1.4.0 Working Baseline
- KEFE Engineering Blueprint v0.5.0 Implementation Contract Baseline
- KEFE Technical Contract Pack v1.0.0
- KEFE Documentation Ecosystem package v3.2 — validation PASS

The audit records **0 open product decisions** and **0 planned official documents**. Implementation must still translate each coherent slice into ADRs, machine-readable contracts and tests. Editable DOCX and generated PDF files are synchronized only at declared milestone boundaries.

Binding rules:

- Golden Path: `Launch → Explore → Case → Context → Weigh → Commit → Reveal → Perspective → My KEFE Progress → Share`.
- Commit First is mandatory; it is not Blind First.
- Context and Sources may appear before Commit but cannot leak result/community/Perspective signals.
- Published CaseVersion is immutable and every decision is pinned to the version seen.
- Optional Reason Capture is private by default.
- Perspective is bounded, provenance-aware and has a deterministic curated fallback.
- Guest continuation is always available through the first value loop.
- Account Offer is optional, post-Reveal, dismissible and non-blocking.
- My KEFE Progress is actor-scoped and server-derived; no personality, ideology or psychometric inference is authorized in the current foundation.
- Content authoring is separate from consumer reads/writes; no public Admin authoring endpoint is authorized until a dedicated authentication/threat-model decision is approved.

## 2. Completed executable foundation

Backend/contracts:

- FastAPI modular monolith and PostgreSQL persistence.
- Linearizable, idempotent Commit with transactional outbox.
- Durable outbox worker and retry/dead-letter controls.
- Hashed, revocable guest bearer sessions and admission guard ports.
- Public Explore Case listing and canonical Case detail.
- Typed `SINGLE_CHOICE` and `CONFIDENCE` questions with requiredness.
- CaseVersion-pinned Context blocks, Sources, claim states and provenance.
- Private structured Reason Capture, moderation state and Commit immutability.
- Commit-gated bounded Perspective read model with curated fallback.
- Authenticated `GET /v1/me/progress` with memory/PostgreSQL adapters.
- Progress fields: committed weigh count, distinct Case/domain coverage, first/last Commit and recent completed Cases.
- Deterministic OpenAPI export/drift gate, contract fitness checks and PostgreSQL integration tests.
- M1 provider-neutral Content Authoring core: stable Case identity; versioned Issue/Question/Context/Source aggregate; `DRAFT → IN_REVIEW → APPROVED → PUBLISHED`; rejection/withdrawal rationale; append-only audit; registry-driven publication validation; immutable published CaseVersion; isolated correction revisions; atomic supersede behavior in the first in-memory adapter.
- Content Authoring currently has **no public HTTP/Admin endpoint** and **no PostgreSQL authoring adapter yet**; those are deliberate next slices, not hidden incompleteness.

Mobile:

- Flutter + Riverpod + GoRouter, system/light/dark themes.
- Secure credential storage and CaseVersion-pinned offline drafts.
- Explore and `/case/:caseId` deep links.
- First-use onboarding through first Reveal.
- Pre-Commit Context/Sources, typed Weigh and optional private Reason.
- Recovery phases: `editing → syncPending → commitPending → committedAwaitingReveal`.
- Commit retry always reuses the durable idempotency key.
- Post-Reveal Perspective with isolated retry.
- Post-Reveal My KEFE Progress with low-claim metrics.
- Optional Account Offer; no fake enrollment button while enrollment is unavailable.
- `Continue as guest` dismisses only the offer and never hides Progress.
- Turkish/English semantic copy and accessibility-oriented controls.

Most recent merged product/architecture slices:

- PR #27 — CaseVersion-pinned Context and Source layer.
- PR #29 — optional Account Offer and actor-scoped My KEFE Progress foundation.
- PR #31 — M1 Content Authoring and immutable publication core; merge commit `9416d4366650c3078d92dbf0b5533e4d1a4cdf39`.

## 3. Current executable path

`Onboarding → Explore → Case Summary → Context + Sources → Typed Weigh → Optional Private Reason → Commit → Trusted Reveal → Curated Perspective → My KEFE Progress → Optional Account Offer`

Failures in Context, Perspective or Progress are isolated from the trusted decision state. They cannot replay mutable answers, Reason or Commit. The current low-risk DILEMMA is a development fixture, not a product-wide default.

Content authoring now has an executable domain/application core but is intentionally not connected to a public Admin surface. Consumer reads continue to use only published immutable content.

## 4. Guardrails for upcoming work

- Never expose result or Perspective before Commit.
- Never expose another user’s private or `PENDING` reason.
- Do not add a raw comment feed or popularity-only ranking.
- Keep human reasons and AI summaries distinct.
- Preserve provenance, moderation and methodology metadata.
- Do not present activity counters as validated identity or psychological insight.
- Do not expose functional account conversion until enrollment, ownership transfer, recovery, retention and revocation work end to end.
- Do not silently lock final navigation or branded Commit terminology outside the approved documents.
- Never mutate a published CaseVersion in place; corrections create a new version.
- Do not expose authoring/Admin HTTP endpoints before a dedicated admin authentication, authorization and threat-model ADR.
- Do not embed a CMS vendor, SQL library, identity provider or AI provider into authoring domain rules.

## 5. Recommended next sequence

1. **Content/Admin persistence foundation**
   - PostgreSQL authoring repository and migrations
   - atomic publication + previous-version supersede + append-only audit in one transaction
   - persistence/integration tests proving drafts cannot leak into consumer reads

2. **Admin security boundary before any authoring HTTP surface**
   - authentication/authorization/threat-model ADR
   - role/capability model, audit identity and session controls
   - only then define authenticated Admin application endpoints

3. **Content configuration and review workflows**
   - taxonomy/format/modifier registry management
   - source verification and claim-status review
   - risk/Civic review-mode enforcement

4. **Observability and deployment baseline**
   - request/event correlation
   - SLO, error and latency metrics
   - secrets/environment contract
   - development/staging deployment runbook

5. **Account enrollment and ownership continuity**
   - explicit authentication/threat-model ADR first
   - guest-to-account transfer without copying decision history
   - recovery, retention, revocation and device-change behavior

6. **Share foundation**
   - privacy-safe cards and deep links
   - sensitive-content restrictions
   - no hidden profile attributes or individual decision leakage

7. **Milestone DOCX/PDF synchronization**
   - patch editable canonical sources
   - regenerate DOCX/PDF
   - visually verify every render
   - update manifest and archive superseded versions

PR #31 completes the first Content Authoring domain/application slice, **not the full Content/Admin milestone**. Therefore DOCX/PDF regeneration is still deferred until the declared Content/Admin milestone boundary is reached or a product-policy change requires an earlier document revision.

## 6. Continuation protocol

1. Read this file from `main`.
2. Inspect open PRs, recent merges and latest CI.
3. Resolve the next slice against the approved document versions above.
4. Create one branch for one coherent vertical slice.
5. Lock behavior in an ADR and machine-readable contract before implementation.
6. Preserve ports/adapters and configuration-driven boundaries.
7. Add tests/contracts in the same PR.
8. Merge only with all relevant CI green.
9. Update this checkpoint after every meaningful merged milestone.
10. Capture CI failure diagnostics as artifacts before speculative fixes.
11. Synchronize DOCX/PDF only at declared milestone boundaries.

## 7. New-chat recovery prompt

> Continue KEFE development from `nazmi02551/KEFE`. Read `docs/status/CURRENT.md` on `main` first, then inspect open PRs, recent commits and CI. Preserve Commit First, CaseVersion pinning, pre-Commit Context without result leakage, private Reason boundaries, optional guest continuation, low-claim My KEFE Progress, immutable published content and provider-neutral ports/adapters. Do not expose an Admin authoring endpoint before a dedicated auth/authorization/threat-model ADR. Lock the next coherent slice in an ADR and machine-readable contract before coding. Merge only with green CI and keep the milestone DOCX/PDF synchronization obligation.
