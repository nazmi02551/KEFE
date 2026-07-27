# ADR-0009 — Commit-gated bounded Perspective read model

**Status:** Accepted  
**Date:** 2026-07-27

## Context

The approved Golden Path places Perspective after Commit and Reveal. KEFE must help a user encounter strong nearby, opposing and bridging views without creating a raw comment wall, leaking a private reason, or making an AI provider part of the product truth boundary.

ADR-0007 and ADR-0008 intentionally keep current Reason Capture records private. Free text may be `PENDING`; tags-only reasons are `NOT_REQUIRED`; neither state changes the record's `PRIVATE` visibility. Therefore the first Perspective slice cannot source cards from current captured reasons.

The existing HTTP flow is actor-scoped and CaseVersion-pinned through `/v1/weigh-sessions/{session_id}`. Perspective must preserve the same entitlement boundary and remain useful when clustering or another AI capability is unavailable.

## Decision

### Access and version boundary

- The first endpoint is `GET /v1/weigh-sessions/{session_id}/perspectives`.
- Bearer identity is required. The session must belong to the authenticated actor and be `COMMITTED`.
- A missing or differently owned session returns the existing non-enumerating `WEIGH_SESSION_NOT_FOUND` error.
- A draft or otherwise uncommitted session returns `RESULT_COMMIT_REQUIRED` with HTTP 403.
- Perspective content is resolved against the session's pinned `case_version_id`, never a later current CaseVersion.

### Bounded card model

- A response contains zero to four ordered cards.
- Each card has exactly one semantic slot: `NEAR`, `OPPOSING`, `BRIDGE` or `ALTERNATIVE_CONTEXT`.
- A response cannot repeat a slot.
- Card order follows that slot order and is not based on likes, engagement or popularity.
- Each card carries stable identity, text, source kind, provenance label and moderation state.
- Human-authored and AI-authored content remain distinct source kinds. AI-authored text is not part of this first implementation.

### Eligibility and privacy

- The first executable source is published editorial/curated fallback content pinned to the CaseVersion.
- Curated cards use source kind `CURATED` and moderation state `NOT_REQUIRED`.
- A future human-reason card is eligible only after a separate policy makes it cross-user visible and its moderation state is `ALLOWED`.
- Current `PRIVATE` reasons, including tags-only `NOT_REQUIRED` and free-text `PENDING` records, are never eligible and must not be queried into the Perspective read model.
- No raw reason feed, author profile, reaction count or popularity score is returned.

### Availability and methodology

- The first response mode is `DEGRADED_CURATED`, making the fallback explicit while no clustering result is available.
- The contract reserves `READY` and `CLUSTER_PENDING` for later provider-neutral clustering work.
- `LOADING` and `ERROR_RETRYABLE` are client transport states, not stored API response modes.
- `REASON_PENDING_MODERATION` is a viewer-specific client state derived separately from the user's own reason lifecycle; it does not expose that reason to Perspective consumers.
- Every response includes methodology metadata: mode, sample kind, sample size, generated timestamp and a human-readable provenance note.
- Empty curated content is a valid `DEGRADED_CURATED` response with zero cards; it is not replaced by private reasons.

### Architecture boundary

- The Decision application service owns Commit entitlement and CaseVersion pinning.
- The repository port exposes a CaseVersion-keyed Perspective snapshot read. Storage/adapters remain replaceable.
- Any future clustering implementation sits behind a provider-neutral port. A provider outage must fall back to curated content without changing access or privacy rules.
- A successful read emits `perspective.viewed` through the existing event boundary without putting card text or reason text in the event payload.

## Consequences

- Commit First remains enforceable with the same actor/session boundary as Reveal.
- The initial vertical slice can deliver Perspective value without an AI dependency or a public social surface.
- Current private Reason Capture data cannot leak through accidental moderation-state interpretation.
- CaseVersion-pinned editorial cards require an explicit persistence contract and deterministic ordering.
- Later clustering, moderation eligibility, reactions, reporting, public reason authoring and AI summaries require separate reviewed slices.

## Explicitly out of scope

- Raw comment/reason feeds.
- Cross-user visibility for existing private reasons.
- Reactions, reporting, persuasion metrics or ranking algorithms.
- AI-generated summaries or provider selection.
- Final mobile visual treatment beyond consuming the locked states and card roles.
