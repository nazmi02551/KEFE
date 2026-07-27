# KEFE Current Project Checkpoint

**Updated:** 2026-07-27  
**Repository:** `nazmi02551/KEFE`  
**Default branch:** `main`  
**Latest verified implementation commit:** `acc85c89aa3ef2be7d76d6f5ce02f2e5293783ab`

This file is the **single canonical durable engineering handoff point** for continuing KEFE development when a chat session, local environment or tool run is interrupted. Before starting new work, verify this file against `main`, open pull requests and recent CI runs.

## 1. Product authority

The repository implementation is governed by the approved KEFE documentation ecosystem. The current authority baseline is:

- KEFE Master Product Document v1.2.0 Approved Canonical
- KEFE Documentation Governance v1.3.2 Approved
- KEFE Product Bible v1.4.0 Working Baseline
- KEFE Engineering Blueprint v0.5.0 Implementation Contract Baseline
- KEFE Technical Contract Pack v1.0.0
- KEFE Documentation Ecosystem audit/package v3.2 (validation PASS)

The v3.2 audit records **0 open product decisions** and **0 planned official documents**. This does not authorize implementation to improvise product behavior: each delivery slice must translate the applicable canonical decisions into a reviewed ADR, API/schema contract and acceptance tests before or with code. Older handoff notes and superseded document versions are not decision authorities.

The editable DOCX and generated PDF package are synchronized only at meaningful milestone boundaries, following the documentation governance rules.

Binding product rules relevant to the executable path include:

- Canonical Golden Path: `Launch → Explore → Case → Weigh → Commit → Reveal → Perspective → My KEFE Progress → Share`.
- First-session path includes the short promise, Demo DILEMMA, optional post-Reveal Account Offer and the same downstream Perspective/Progress/Share value path.
- Commit First: community/result layers are unavailable before the user's confirmed decision.
- Commit First is not Blind First; context and sources must remain available without result leakage.
- CaseVersion pinning and published-version immutability.
- Provider-neutral ports/adapters and configuration-driven infrastructure.
- Reason Capture is optional and private-by-default in the current executable scope.
- There is no raw comment wall. Perspective is a bounded, quality-oriented post-Commit experience with curated fallback when AI is unavailable.

## 2. Completed executable milestones

### Backend and contracts

- FastAPI modular monolith walking skeleton.
- PostgreSQL migrations and provider-neutral persistence adapter.
- Linearizable Commit boundary with row locking and idempotency.
- Transactional outbox and durable at-least-once outbox worker.
- Real guest identity boundary; `X-Actor-Id` shortcut removed.
- Hashed, revocable guest bearer sessions.
- Guest admission guard with rate-limit and device-integrity ports.
- Public bounded `GET /v1/cases` Explore read model.
- Generated OpenAPI contract and drift gate.
- Typed question engine with `SINGLE_CHOICE` and `CONFIDENCE` validation.
- Required-question semantics stored in PostgreSQL.
- Private structured Reason Capture with schema-driven tags and optional short text.
- Reason moderation lifecycle: tags-only `NOT_REQUIRED`, free text `PENDING`, private visibility only.
- Reasons become immutable at Commit.
- Actor-owned, Commit-gated `GET /v1/weigh-sessions/{session_id}/perspectives` read model.
- CaseVersion-pinned PostgreSQL curated Perspective cards in four bounded semantic slots.
- Deterministic `DEGRADED_CURATED` fallback with provenance and methodology metadata.
- Current private/pending reasons are excluded from Perspective; view events contain no card/reason text.
- Contract manifest, ADRs, error registry and schema snapshots.

### Mobile

- Flutter, Riverpod and GoRouter foundation.
- Light/Dark/System theme support.
- Secure platform credential storage.
- Offline decision drafts pinned to CaseVersion.
- Explore screen and canonical `/case/:caseId` deep-link route.
- First-use onboarding through first Reveal.
- Typed question registry and Confidence capture.
- Schema-driven private Reason Capture with bounded tags and optional short text.
- Private reason persisted with the pinned offline decision draft and synchronized to the same WeighSession before Commit.
- Four-phase recovery boundary: `editing → syncPending → commitPending → committedAwaitingReveal`.
- Pre-Commit response/reason synchronization can safely retry before Commit.
- Once Commit may have been sent, retries use only the same Commit idempotency key and never replay mutable answers/reasons.
- Turkish/English semantic copy and accessibility-oriented controls.

### Most recent merged product slices

- PR #17 — first-use onboarding through first Reveal.
- PR #18 — typed question engine and Confidence capture.
- PR #20 — private-by-default structured Reason Capture backend.
- PR #22 — mobile private Reason Capture and offline-safe pre-Commit synchronization.
- PR #25 — Commit-gated bounded Perspective backend and curated fallback.

## 3. Current executable path

Mobile consumer path today:

`Onboarding → Explore → Case → Typed Weigh → Optional Private Reason → Commit → Trusted Reveal`

Backend capability now continues through:

`Trusted Reveal → Commit-gated Curated Perspective`

The reason step is optional and CaseVersion/schema-driven. Blank input never blocks Commit and causes no reason API call. Results remain hidden until Commit. Reason data is not exposed to other users in the current product surface; optional short text may enter server-side safety moderation. The mobile client does not yet render the Perspective endpoint.

The active demo remains a low-risk DILEMMA. Its current reason/question configuration is a development fixture, not a product-wide default.

## 4. Canonical decision status and implementation guardrails

There are no open product decisions in the current official documentation set. The former checkpoint list of open questions was based on superseded document versions and must not be used to delay, reverse or silently reinterpret approved decisions.

Some canonical decisions are not yet fully expressed in this executable slice. Navigation, user-facing Commit terminology, Quick Weigh behavior, identity/account conversion, retention, sampling/methodology, civic review/publication, expert verification, KEFE+, social visibility and Perspective ranking must be introduced only through small reviewed slices that cite the current authority documents and update the relevant ADRs/contracts/tests.

Implementation guardrails for the next slice:

- Do not expose a community result or Perspective before Commit.
- Do not expose current private or `PENDING` reasons to another user.
- Do not add a raw feed, popularity-only ranking or unlabeled AI-authored text.
- Keep human reasons and AI summaries separate in the data model and UI.
- Preserve a deterministic curated fallback when AI or clustering is unavailable.
- Carry provenance, moderation state and sample/methodology metadata through the read model.

## 5. Recommended next delivery sequence

Continue in small reviewed vertical slices:

1. **Mobile Perspective consumption**
   - before coding, lock placement, navigation and UI state transitions in ADR-0010; do not infer the final visual treatment
   - consume the session-scoped endpoint only after successful Commit/Reveal
   - render at most four ordered roles: near, opposing, Bridge and alternative context
   - distinguish curated fallback and methodology/provenance without alarmist degradation copy
   - implement `LOADING`, `READY`, `CLUSTER_PENDING`, `DEGRADED_CURATED`, `REASON_PENDING_MODERATION` and `ERROR_RETRYABLE`
   - preserve safe retry without replaying Commit, answers or reasons
   - exclude reactions, reporting, public authoring, local ranking and AI-generated summaries

2. **Context + Sources read layer**
   - progressive context blocks and source metadata
   - `VERIFIED / CLAIMED / DISPUTED / UNKNOWN` semantics
   - no result leakage before Commit
   - preserve CaseVersion pinning and source/version auditability

3. **Account Offer + My KEFE Progress foundation**
   - preserve optional, transparent guest continuation and the canonical first-session boundary
   - make identity/retention behavior explicit in contracts before implementation
   - connect committed activity to the approved progress model without premature gamification

4. **Content/Admin foundation**
   - Case/Issue/Question authoring contracts
   - publication workflow and audit trail
   - taxonomy/configuration management

5. **Observability and deployment baseline**
   - request/event correlation
   - SLO/error/latency metrics
   - secrets and environment contract
   - development/staging deployment runbook

6. **Milestone documentation synchronization**
   - patch the Engineering Blueprint and relevant specialist documents with executable decisions accumulated through the milestone
   - regenerate DOCX/PDF package from editable sources
   - visually verify renders, update manifest and archive prior versions

## 6. Continuation protocol

At the beginning of every new work session:

1. Read **only this checkpoint as the canonical engineering handoff**: `docs/status/CURRENT.md` from `main`.
2. Check open PRs and recent merged PRs.
3. Check the latest CI status before branching.
4. Resolve the next slice against the current official document versions; do not resurrect superseded open-decision lists.
5. Lock slice-specific product/API behavior in an ADR and machine-readable contract before implementation.
6. Create one feature branch for one coherent vertical slice.
7. Keep architecture/provider boundaries intact.
8. Add or update tests and machine-readable contracts in the same PR.
9. Merge only after all relevant CI jobs pass.
10. Update this checkpoint after every meaningful merged milestone.
11. Treat older handoff files as redirects to this file, not independent state sources.

## 7. Recovery prompt for a new chat

Use the following message if continuation must move to another conversation:

> Continue KEFE development from repository `nazmi02551/KEFE`. First read `docs/status/CURRENT.md` on `main`, inspect open PRs, recent commits and CI, and verify the checkpoint is current. Use the current official KEFE documentation versions recorded there; do not revive superseded open-decision lists. Preserve Commit First, CaseVersion pinning and provider-neutral ports/adapters. Lock the next slice in an ADR and machine-readable contract before coding, keep the change coherent and small, and merge only with green CI. Keep DOCX/PDF synchronization obligations in the milestone checklist.

## 8. Reliability rule

Chat history is not the source of truth. GitHub `main`, current approved product documents, machine-readable contracts, ADRs and **this checkpoint file** are the durable recovery sources. There must be only one live project checkpoint; legacy handoff paths must redirect here rather than duplicate state.
