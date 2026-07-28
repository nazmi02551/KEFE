# ADR-0024 — Flutter Flow-driven consumer rendering

**Status:** Accepted  
**Date:** 2026-07-28

## Context

The Flutter consumer already implements the usable decision experience components: Explore, Case title/summary, Context, typed Questions, private Reason Capture, Commit, Reveal, Perspective and Progress. Until ADR-0023, `DecisionFlowScreen` composed those parts in one fixed screen order.

ADR-0023/API v0.14.0 now provides an actor-scoped server-authoritative Flow runtime from the CaseVersion-pinned immutable `resolved_flow`. The mobile client must consume that runtime without introducing Flutter `case_type` branches or falling back to the historical fixed composition.

Offline draft/recovery is already a product property. Moving Flow authority to the server must not erase that behavior or cause an offline client to invent a different Step sequence.

## Decision

### Mobile runtime authority

For an active WeighSession, the Flutter client renders decision content from the latest server-derived `FlowRuntimeSnapshot` for that session.

The client may cache that snapshot for offline/recovery continuity, but may not alter Step identity, ordering, Primitive, Capability, transitions or server Step state.

A fixed `Context → Questions → Commit → Reveal` fallback is forbidden for Flow-driven sessions.

### Session loading

For a new session:

1. fetch Case content,
2. start WeighSession,
3. fetch `/v1/weigh-sessions/{session_id}/flow`,
4. render the returned Step sequence.

For a stored draft:

- a persisted FlowRuntimeSnapshot may be rendered while offline,
- when online the runtime is refreshed from the server,
- a legacy draft without a persisted Flow snapshot must fetch one before normal decision rendering,
- if that cannot be done offline, the client surfaces a recoverable Flow-unavailable state rather than assuming a default Flow.

### Step rendering v1

The screen iterates runtime Steps in server order.

`CONTEXT`
- READY/COMPLETED → render the existing `ContextSection`.
- BLOCKED → no Context content is fetched/rendered yet.

`DECISION`
- READY → render the existing typed Question cards, optional Reason Capture and Commit action.
- COMPLETED → do not render editable controls.
- UNSUPPORTED → render a neutral capability-pending card using the machine reason; do not fabricate a decision/retest UI.

`COLLECTIVE_RESULT`
- READY + Reveal loaded → render existing trusted Reveal card and Perspective section.
- BLOCKED → do not render result content.
- Flow state alone never contains result payload.

`REFLECTION` or unknown Primitive
- UNSUPPORTED → render a neutral capability-pending card.
- no case-specific screen is created.

### Commit refresh

After a successful Commit/reveal recovery path, Flutter refreshes Flow runtime from the server before presenting the post-Commit composition. The Reveal API remains the only source of result data.

### Offline persistence

`DecisionDraft` persists the FlowRuntimeSnapshot alongside Case/session/response/reason state.

This snapshot is continuity state, not independent product authority:
- server refresh replaces it when available,
- it is pinned to the same session/CaseVersion,
- it must never be re-used for a different session or CaseVersion.

### Partial execution

`execution_support=PARTIAL` does not force the client back to fixed rendering. Supported Steps render normally and unsupported reachable Steps render explicitly as capability pending.

For `PRINCIPLE_CONTEXT_RETEST`, the second Decision remains visibly unavailable until DecisionRevision exists; the client does not emulate it locally.

### Accessibility and copy

Existing accessible input/result components remain reused. Unsupported-state copy is neutral and must not imply user error, moral judgment or that KEFE has taken a position.

## Consequences

- The first tangible consumer milestone can reuse the mature Flutter components instead of rebuilding screens.
- Case composition becomes server/configuration driven while offline continuity remains safe.
- New Flow Templates can change Step composition without new case-specific Flutter controllers/screens when their Primitives are already supported.
- DecisionRevision can later unlock retest Steps through the same runtime contract.
