# KEFE Current Project Checkpoint

**Updated:** 2026-07-27  
**Repository:** `nazmi02551/KEFE`  
**Default branch:** `main`  
**Latest verified implementation commit:** `62228637b57ad29ec0cf25b388baac7b29ceef82`

This file is the **single canonical durable handoff point** for continuing KEFE development when a chat session, local environment or tool run is interrupted. Before starting new work, verify this file against `main`, open pull requests and recent CI runs.

## 1. Product authority

The product remains governed by the approved KEFE documentation ecosystem. The active product baseline is:

- KEFE Master Product Document v1.1 Approved Canonical
- KEFE Documentation Governance v1.2 Approved
- KEFE Product Bible v1.3 Working Baseline
- KEFE Engineering Blueprint v0.3 Architecture Baseline

The editable DOCX and generated PDF package must be synchronized at meaningful milestone boundaries. The repository implementation must not silently redefine product decisions that remain open in the approved documents.

Binding product rules currently implemented:

- `Discover → Context → Weigh → Commit → Reveal → Perspective → Reflect → Share`
- Commit First: community/result layers are unavailable before the user's confirmed decision.
- Commit First is not Blind First.
- CaseVersion pinning and published-version immutability.
- Provider-neutral ports/adapters and configuration-driven infrastructure.
- No final 3-vs-4-tab primary navigation decision has been encoded.
- No final branded Commit CTA has been encoded; the technical action remains `COMMIT`.
- Reason Capture is private-by-default until an explicit later product/moderation policy enables cross-user visibility.

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

## 3. Current executable path

Consumer path today:

`Onboarding → Explore → Case → Typed Weigh → Private Reason → Commit → Trusted Reveal`

The private reason step is optional and CaseVersion/schema-driven. Results remain hidden until Commit. Reason data is not exposed to other users in the current product surface; optional short text may enter server-side safety moderation.

The active demo remains a low-risk DILEMMA. Its current reason/question configuration is a development fixture, not a product-wide default.

## 4. Known open product decisions

Do not close these implicitly in code without updating the approved product decision process:

- Final primary navigation: three or four destinations.
- Final user-facing Commit CTA.
- Quick Weigh Reveal timing.
- Final North Star window: WAU or MAU.
- Guest retention duration beyond current technical baseline.
- MVP CALL breadth.
- Country launch sequence.
- Values release phase and scientific validation.
- Atlas confidence/default publication thresholds.
- Raw versus Trusted consumer presentation.
- Balanced Sample methodology.
- Civic P2/P3 review and delayed publication policy.
- Expert verification operating model.
- KEFE+ launch timing.
- Social reason visibility, moderation and ranking boundaries.

## 5. Recommended next delivery sequence

The next implementation work should remain in small reviewed slices:

1. **Reveal Perspective layer**
   - expose only moderation-approved human reasons after Commit
   - begin with a safe opposing-perspective read model, not a classic comment feed
   - carry reason provenance, moderation state and methodology/sample metadata
   - avoid popularity-only ranking; preserve bridge/quality direction without inventing a final algorithm prematurely
   - keep AI summaries separate and explicitly labeled when introduced later

2. **Context + Sources read layer**
   - progressive context blocks and source metadata
   - VERIFIED / CLAIMED / DISPUTED / UNKNOWN semantics
   - no result leakage before Commit
   - preserve CaseVersion pinning and source/version auditability

3. **Content/Admin foundation**
   - Case/Issue/Question authoring contracts
   - publication workflow and audit trail
   - taxonomy/configuration management

4. **Observability and deployment baseline**
   - request/event correlation
   - SLO/error/latency metrics
   - secrets and environment contract
   - development/staging deployment runbook

5. **Milestone documentation synchronization**
   - patch Engineering Blueprint and relevant specialist documents with the executable decisions accumulated through this milestone
   - regenerate DOCX/PDF package from editable sources
   - visually verify renders, update manifest and archive prior versions

## 6. Continuation protocol

At the beginning of every new work session:

1. Read **only this checkpoint as the canonical engineering handoff**: `docs/status/CURRENT.md` from `main`.
2. Check open PRs and recent merged PRs.
3. Check the latest CI status before branching.
4. Create one feature branch for one coherent slice.
5. Keep architecture/provider boundaries intact.
6. Add or update tests and machine-readable contracts in the same PR.
7. Merge only after all relevant CI jobs pass.
8. Update this checkpoint after every meaningful merged milestone.
9. Treat older handoff files as redirects to this file, not independent state sources.

## 7. Recovery prompt for a new chat

Use the following message if continuation must move to another conversation:

> Continue KEFE development from repository `nazmi02551/KEFE`. First read `docs/status/CURRENT.md` on `main`, inspect open PRs, recent commits and CI, and verify the checkpoint is current. Preserve Commit First, CaseVersion pinning, provider-neutral ports/adapters and all open product decisions. Continue with the next recommended coherent slice; do not silently lock unresolved product decisions. Keep DOCX/PDF synchronization obligations in the milestone checklist.

## 8. Reliability rule

Chat history is not the source of truth. GitHub `main`, approved product documents, machine-readable contracts, ADRs and **this checkpoint file** are the durable recovery sources. There must be only one live project checkpoint; legacy handoff paths must redirect here rather than duplicate state.
