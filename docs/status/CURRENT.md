# KEFE Current Project Checkpoint

**Updated:** 2026-07-27  
**Repository:** `nazmi02551/KEFE`  
**Default branch:** `main`  
**Latest verified implementation commit:** `179ab69a4ba8e20970f16ecda1be20c20533b776`

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

- Canonical Golden Path: `Launch → Explore → Case → Context → Weigh → Commit → Reveal → Perspective → My KEFE Progress → Share`.
- First-session path includes the short promise, Demo DILEMMA, optional post-Reveal Account Offer and the same downstream Perspective/Progress/Share value path.
- Commit First: community/result layers are unavailable before the user's confirmed decision.
- Commit First is not Blind First; Context and Sources remain available before Commit without result leakage.
- CaseVersion pinning and published-version immutability.
- Claim status (`VERIFIED / CLAIMED / DISPUTED / UNKNOWN`) is distinct from source kind and provenance.
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
- Public `GET /v1/case-versions/{case_version_id}/context` read boundary.
- CaseVersion-pinned Context blocks, Sources, provenance links and progressive-disclosure metadata.
- Context leakage guardrails prevent results, Perspective, participant reasons, sample metrics and community signals from entering the pre-Commit response.
- Context claim states and source kinds are modeled separately.
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
- Automatic post-Reveal consumption of the actor-owned Perspective endpoint in the same Case journey; no new primary navigation destination.
- At most four API-ordered Perspective roles (`NEAR`, `OPPOSING`, `BRIDGE`, `ALTERNATIVE_CONTEXT`) with unknown slots filtered safely.
- Explicit Perspective UI states for loading, ready, cluster pending, curated fallback, retryable error and viewer-only reason moderation notice.
- Perspective-only retry; failures do not hide the trusted Reveal or replay responses, reasons, Commit or Reveal.
- Context appears after the Case summary and before Weigh.
- `ESSENTIAL` Context is visible by default; `DETAIL` blocks and Sources are explicitly expandable.
- Context failure is isolated from decision recovery and does not expose or trigger post-Commit data.
- Remote evidence is rendered as trusted structured fields; untrusted remote HTML is not embedded.

### Most recent merged product slices

- PR #20 — private-by-default structured Reason Capture backend.
- PR #22 — mobile private Reason Capture and offline-safe pre-Commit synchronization.
- PR #25 — Commit-gated bounded Perspective backend and curated fallback.
- PR #26 — mobile post-Reveal Perspective consumption with isolated safe retry.
- PR #27 — CaseVersion-pinned pre-Commit Context and Source read layer across backend, contracts and mobile.

## 3. Current executable path

Mobile consumer path today:

`Onboarding → Explore → Case Summary → Context + Sources → Typed Weigh → Optional Private Reason → Commit → Trusted Reveal → Curated Perspective`

Context is public, CaseVersion-pinned and available before Commit. It contains editorially ordered evidence blocks, claim states and source provenance, but no community/result/Perspective/participant-reason leakage. The reason step is optional and schema-driven. Blank reason input never blocks Commit. Results remain hidden until Commit. After a successful Reveal, the mobile client automatically requests and renders the bounded, actor-owned Perspective read model below Reveal.

The active demo remains a low-risk DILEMMA. Its current context, source, reason and question configuration is a development fixture, not a product-wide default.

## 4. Canonical decision status and implementation guardrails

There are no open product decisions in the current official documentation set. Superseded open-decision lists must not be used to delay, reverse or silently reinterpret approved decisions.

Some canonical decisions are not yet fully expressed in this executable slice. Navigation, user-facing Commit terminology, Quick Weigh behavior, identity/account conversion, retention, sampling/methodology, civic review/publication, expert verification, KEFE+, social visibility and production Perspective ranking must be introduced only through small reviewed slices that cite the current authority documents and update the relevant ADRs/contracts/tests.

Implementation guardrails for the next slice:

- Do not expose a community result or Perspective before Commit.
- Keep Context and Sources available before Commit without leaking post-Commit signals.
- Do not expose current private or `PENDING` reasons to another user.
- Do not add a raw feed, popularity-only ranking or unlabeled AI-authored text.
- Keep human reasons and AI summaries separate in the data model and UI.
- Preserve a deterministic curated fallback when AI or clustering is unavailable.
- Carry provenance, moderation state and sample/methodology metadata through applicable read models.
- Preserve optional guest continuation; do not force account creation to complete the first value loop.

## 5. Recommended next delivery sequence

Continue in small reviewed vertical slices:

1. **Account Offer + My KEFE Progress foundation**
   - lock the post-Reveal Account Offer placement and guest-continuation behavior in an ADR and machine-readable contract
   - make guest-to-account conversion, ownership continuity and retention behavior explicit before implementation
   - add the minimum approved My KEFE Progress read model without premature personality claims or gamification
   - preserve the already completed Reveal and Perspective path even when account conversion is skipped

2. **Content/Admin foundation**
   - Case/Issue/Question/Context/Source authoring contracts
   - publication workflow, CaseVersion immutability and audit trail
   - taxonomy/configuration management
   - source verification and claim-status review

3. **Observability and deployment baseline**
   - request/event correlation
   - SLO/error/latency metrics
   - secrets and environment contract
   - development/staging deployment runbook

4. **Milestone documentation synchronization**
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
12. Synchronize editable DOCX/PDF only at a declared milestone boundary, not after every small merge.

## 7. Recovery prompt for a new chat

Use the following message if continuation must move to another conversation:

> Continue KEFE development from repository `nazmi02551/KEFE`. First read `docs/status/CURRENT.md` on `main`, inspect open PRs, recent commits and CI, and verify the checkpoint is current. Use the current official KEFE documentation versions recorded there; do not revive superseded open-decision lists. Preserve Commit First, pre-Commit Context without result leakage, CaseVersion pinning and provider-neutral ports/adapters. Lock the next slice in an ADR and machine-readable contract before coding, keep the change coherent and small, and merge only with green CI. Keep DOCX/PDF synchronization obligations in the milestone checklist.

## 8. Reliability rule

Chat history is not the source of truth. GitHub `main`, current approved product documents, machine-readable contracts, ADRs and **this checkpoint file** are the durable recovery sources. There must be only one live project checkpoint; legacy handoff paths must redirect here rather than duplicate state.
