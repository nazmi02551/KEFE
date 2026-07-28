# ADR-0023 — Generic consumer Flow runtime from CaseVersion-pinned Flow

**Status:** Accepted  
**Date:** 2026-07-28

## Context

ADR-0019 defines KEFE as a case-agnostic engine composed through `Primitive → Capability → FlowTemplateVersion → CaseVersion`. ADR-0022 makes every newly published CaseVersion self-contained by pinning the effective Content Configuration provenance and an immutable `resolved_flow` snapshot.

The consumer application still renders the historical fixed composition `Context → Questions → Commit → Reveal`. The next runtime layer must interpret the pinned Flow without introducing case-specific controllers or looking up live Content Configuration.

The current Decision domain supports one editable pre-Commit decision and one immutable Commit per WeighSession. A Flow such as `PRINCIPLE_CONTEXT_RETEST` contains more than one Decision Step and therefore needs the later DecisionRevision/Intervention model. The first generic runtime must expose that capability boundary honestly rather than pretending the existing single-Commit session can execute a retest.

## Decision

### Runtime authority

Flow execution reads only:

- the actor-owned WeighSession,
- the CaseVersion pinned by that session,
- the CaseVersion's immutable `resolved_flow`.

Live Content Configuration is never consulted to reinterpret an existing CaseVersion.

### Runtime API

An authenticated read endpoint is introduced:

`GET /v1/weigh-sessions/{session_id}/flow`

It returns a server-derived Flow runtime snapshot containing:

- session and CaseVersion identity,
- template code/version and entry Step,
- execution support (`FULL` or `PARTIAL`),
- Step order/graph references,
- each Step's Primitive and Capabilities,
- each Step state (`READY`, `COMPLETED`, `BLOCKED`, `UNSUPPORTED`),
- an optional machine-readable reason code.

The endpoint is actor-scoped and cannot expose another actor's session.

### Primitive semantics in runtime v1

The executor is Primitive-driven, not Base-Format or Case-Type driven.

`CONTEXT`
- informational/non-blocking in runtime v1,
- becomes `READY` when its graph predecessors are satisfied,
- counts as transition-satisfied without requiring an acknowledgement event,
- future exposure-aware Context/Intervention capabilities may change this through a versioned runtime capability, not a case-specific branch.

`DECISION`
- the first Decision Step maps to the current editable WeighSession decision,
- it is `READY` while the session is DRAFT and `COMPLETED` after Commit,
- any later Decision Step is `BLOCKED` until graph predecessors are satisfied, then `UNSUPPORTED` with reason `FLOW_DECISION_REVISION_REQUIRED` until DecisionRevision exists.

`COLLECTIVE_RESULT`
- `BLOCKED` before Commit,
- `READY` after Commit,
- reveal payload remains served only by the existing Commit-gated Reveal endpoint; the Flow runtime does not duplicate or leak result data.

`REFLECTION`
- graph-readable but runtime v1 marks it `UNSUPPORTED` with reason `FLOW_REFLECTION_RUNTIME_PENDING` once reachable.

Unknown future Primitives are graph-readable and marked `UNSUPPORTED` with `FLOW_PRIMITIVE_UNSUPPORTED`; they never fall through to a case-specific default.

### Graph semantics

- Step identity/order/transition targets come from pinned `resolved_flow`.
- A Step with unmet blocking predecessors is `BLOCKED` with `FLOW_PREDECESSOR_PENDING`.
- Informational CONTEXT Steps are non-blocking in runtime v1.
- The first Decision Step is the current single-Commit barrier.
- Result availability derives only from server session Commit state.
- Runtime state never trusts client claims about completed Steps or Commit status.

### Execution support

`FULL` means every reachable Step can be represented by runtime v1 semantics for the current single-Commit model.

`PARTIAL` means the Flow is still parsed generically but contains one or more Steps requiring a capability not yet executable in runtime v1, such as DecisionRevision or Reflection.

`PARTIAL` is not a fallback to a fixed screen and does not mutate the Flow.

### Legacy CaseVersions

Historical CaseVersions without `resolved_flow` return `FLOW_RUNTIME_UNAVAILABLE` (409). They are not silently interpreted using live configuration or an assumed default Flow.

### Security and result leakage

- Flow runtime is authenticated and actor-scoped.
- It may reveal that a result Step is locked/ready, but never includes result percentages, Perspective cards, private reasons or other post-Commit payloads.
- Existing Reveal/Perspective Commit gates remain authoritative.

## Consequences

- Consumer clients gain one server-authoritative Step graph/state model.
- `STANDARD_COMMIT_REVEAL` is fully executable without case-specific code.
- `PRINCIPLE_CONTEXT_RETEST` is parsed by the same runtime and exposes the exact DecisionRevision gap instead of being hard-coded or falsely executed.
- Flutter can move from a fixed screen composition to Primitive-driven rendering incrementally.
- DecisionRevision/Exposure/Intervention can extend the same runtime rather than replacing it.