# ADR-0010 — Mobile Perspective consumption after Reveal

**Status:** Accepted  
**Date:** 2026-07-27

## Context

ADR-0009 establishes the actor-owned, Commit-gated, CaseVersion-pinned Perspective endpoint and its bounded four-slot model. The mobile client already executes `Typed Weigh → Optional Private Reason → Commit → Trusted Reveal`, including offline-safe Commit recovery. It does not yet consume Perspective.

The mobile slice must extend the approved Golden Path to `Reveal → Perspective` without creating a second Commit path, leaking private reasons, introducing a raw social feed, or silently deciding the final global navigation/visual system.

## Decision

### Placement and navigation

- Perspective is a post-Reveal continuation of the active Weigh journey.
- The first mobile implementation renders Perspective **below the successful Reveal in the same Case journey**. It does not create a new primary navigation destination.
- After a successful Reveal, the client automatically starts one Perspective read for that committed session.
- A Perspective transport failure never hides or invalidates the already successful Reveal.
- Retrying Perspective calls only `GET /v1/weigh-sessions/{session_id}/perspectives`; it must not replay answers, private reason writes or Commit.
- Direct navigation to a standalone Perspective screen is out of scope for this slice. This keeps placement reversible while satisfying the canonical Golden Path.

### Client state model

The client owns transport/presentation state separately from the server response mode:

- `IDLE` — Reveal has not succeeded; Perspective is not requested.
- `LOADING` — the post-Reveal Perspective request is in flight.
- `READY` — API methodology mode is `READY`.
- `CLUSTER_PENDING` — API methodology mode is `CLUSTER_PENDING`.
- `DEGRADED_CURATED` — API methodology mode is `DEGRADED_CURATED`.
- `ERROR_RETRYABLE` — the read failed in a retryable transport/dependency condition; Reveal remains usable.

`REASON_PENDING_MODERATION` is an independent viewer-specific flag derived from the authenticated user's own reason write result. It may coexist with any successful Perspective mode and must not imply that the private reason is visible to other users.

### Card rendering contract

- Render zero to four cards in the API order.
- Recognized slots are `NEAR`, `OPPOSING`, `BRIDGE`, `ALTERNATIVE_CONTEXT`.
- The client does not locally re-rank cards.
- Each card exposes its semantic role and body plus a restrained provenance label.
- `CURATED` content is described as curated/editorial perspective, not as another participant's opinion.
- No author profile, reaction count, popularity score, report action, public authoring affordance or AI summary is added.
- Unknown future slots/source kinds are handled safely without crashing and are not promoted above known semantics.

### Methodology and fallback communication

- Successful Perspective states show methodology/provenance metadata in a secondary disclosure area.
- `DEGRADED_CURATED` is presented neutrally as a curated fallback, not as an alarming failure state.
- `CLUSTER_PENDING` may show available cards while explaining that broader perspective processing is still in progress.
- An empty card list is valid and does not fall back to private reasons.

### Privacy and recovery

- The client never derives Perspective content from locally stored private reason text/tags.
- A local private reason with server moderation state `PENDING` only controls the viewer-specific `REASON_PENDING_MODERATION` notice.
- Perspective retry is independent of the four-phase decision recovery state machine. Once Reveal succeeds, no mutable decision command is replayed to obtain Perspective.

## Consequences

- The executable mobile path becomes `Commit → Reveal → Perspective` while preserving Commit First and private Reason Capture.
- Perspective can fail independently without making a committed decision appear lost.
- The implementation remains compatible with future provider-neutral clustering and future approved source kinds.
- Final visual styling, primary navigation architecture, reactions, reporting, social authoring and AI summaries remain outside this ADR.
