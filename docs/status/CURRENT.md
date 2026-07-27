# KEFE Current Project Checkpoint

**Updated:** 2026-07-27  
**Repository:** `nazmi02551/KEFE`  
**Default branch:** `main`  
**Latest verified implementation commit:** `5956fa69c451a49bf38463535548f7275db408a7`

This file is the durable handoff point for continuing KEFE development when a chat session, local environment or tool run is interrupted. Before starting new work, verify this file against `main`, open pull requests and recent CI runs.

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
- Durable Commit idempotency key and uncertain-Commit recovery.
- Explore screen and canonical `/case/:caseId` deep-link route.
- First-use onboarding through first Reveal.
- Typed question registry and Confidence capture.
- Turkish/English semantic copy and accessibility-oriented controls.

### Most recent merged product slices

- PR #16 — Explore discovery and deep-linkable Case flow.
- PR #17 — first-use onboarding through first Reveal.
- PR #18 — typed question engine and Confidence capture.
- PR #20 — private-by-default structured Reason Capture backend.

## 3. Current executable path

Consumer path today:

`Onboarding → Explore → Case → Typed Weigh → Commit → Trusted Reveal`

Backend capability now additionally supports:

`Typed Weigh → Private Reason → Commit`

The active demo remains a low-risk DILEMMA. Results remain hidden until Commit. Reason data is not exposed to other users in the current product surface.

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
- Social reason visibility and moderation boundaries.

## 5. Recommended next delivery sequence

The next implementation work should remain in small reviewed slices:

1. **Mobile Reason Capture**
   - render structured reason tags from the published CaseVersion policy
   - optional short-text input only when enabled by schema
   - persist reason draft safely with the existing decision draft
   - submit reason before Commit using the same pinned session
   - no public feed or cross-user reason visibility

2. **Reveal perspective layer**
   - strongest moderation-approved opposing reasons after Commit
   - sample/methodology metadata
   - no popularity-only ranking
   - preserve separation between human reasons and AI summaries

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
   - patch Engineering Blueprint and relevant specialist documents
   - regenerate DOCX/PDF package
   - update manifest and archive prior versions

## 6. Continuation protocol

At the beginning of every new work session:

1. Read this file from `main`.
2. Check open PRs and recent merged PRs.
3. Check the latest CI status before branching.
4. Create one feature branch for one coherent slice.
5. Keep architecture/provider boundaries intact.
6. Add or update tests and machine-readable contracts in the same PR.
7. Merge only after all relevant CI jobs pass.
8. Update this checkpoint after every meaningful merged milestone.

## 7. Recovery prompt for a new chat

Use the following message if continuation must move to another conversation:

> Continue KEFE development from repository `nazmi02551/KEFE`. First read `docs/status/CURRENT.md` on `main`, inspect open PRs, recent commits and CI, and verify the checkpoint is current. Preserve Commit First, CaseVersion pinning, provider-neutral ports/adapters and all open product decisions. Continue with the next recommended coherent slice; do not silently lock unresolved product decisions. Keep DOCX/PDF synchronization obligations in the milestone checklist.

## 8. Reliability rule

Chat history is not the source of truth. GitHub `main`, approved product documents, machine-readable contracts, ADRs and this checkpoint file are the durable recovery sources.
