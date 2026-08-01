# ADR-0062 — Reflection State and Semantic-Surface Convergence

Date: 2026-08-01  
Status: Accepted for Slice 24 implementation  
Tracker: #153  
Stack parent: `feature/decision-flow-shell-state-slice23`

## Context

ADR-0026 and `docs/contracts/reflection-runtime.v1.yaml` already define the generic Reflection runtime, actor-private server-derived read model, immutable lineage-cursor-aware completion, idempotent recovery and non-causal methodology boundary.

The canonical active stack now has a premium theme-adaptive Decision Flow shell, but `ReflectionStepCard` remains a residual presentation island:

- the root uses a generic Material `Card`;
- presentation uses direct dark-only `KefeColorTokens` values;
- the journey graphic uses a screen-local fixed gradient;
- initial loading and load error/retry are plain text/button arrangements;
- an inline completion error is plain text;
- completing Reflection replaces the action icon with an indeterminate `CircularProgressIndicator`.

These are presentation/state inconsistencies. They do not justify reopening the Reflection domain or methodology contract.

## Decision

Slice 24 converges the existing reusable `REFLECTION` primitive presentation onto the shared KEFE semantic visual system without changing its runtime behavior.

### Semantic root and state surfaces

The existing `ReflectionStepCard` remains the reusable Flow-driven component and preserves its stable root key. Its root and nested state treatments use `KefeSurface` plus theme-adaptive `KefeVisualRoles` instead of generic Material Card or direct dark-only tokens.

The governed presentation includes semantic treatments for:

- initial loading;
- initial error and retry;
- decision-revision journey summary;
- intervention-count disclosure;
- non-causal methodology note;
- inline completion error;
- completion working state;
- completed state.

Existing localized strings remain authoritative. No new interpretation, recommendation, causal explanation, persuasion claim or methodology label is introduced.

### Deterministic loading and completion working state

Initial loading and completion submission use deterministic semantic status presentation. The client has no truthful progress percentage or completion estimate, so no artificial progress is shown.

The existing stable `reflection-complete-button` remains the single completion action. While completion is in progress it stays disabled, presents deterministic localized working treatment and does not imply server success. No indeterminate spinner remains in the governed Reflection source.

### Reflection methodology remains descriptive and non-causal

The existing server-derived values remain the only data authority:

- revision count;
- decision-changed boolean;
- changed-question count;
- intervention count and type codes;
- contribution classes;
- completion state.

The presentation may visualize revision movement and intervention count, but it must not represent an Intervention as causing the decision change. The existing `reflectionNonCausalNote` remains visible and authoritative.

The journey graphic is decorative support for the textual summary. It must be excluded from independent semantic meaning and may not expose raw response values, private reason text, a correctness judgment, persuasion score, ideology/value coordinate, personality trait or causal path.

### Theme, layout and motion

The component must support:

- dark and light themes using semantic visual roles;
- 360 × 800 phone viewport;
- 1.6× text scale;
- no direct dark-only presentation tokens;
- no screen-local fixed RGB gradient;
- no continuous decorative animation;
- decorative icons/graphics excluded from semantics;
- live-region treatment for meaningful loading/error/completing/completed state changes where appropriate.

No mandatory WebView, Three.js or live 3D dependency is introduced.

## Preserved behavior

Slice 24 does not change:

- ADR-0026 or `reflection-runtime.v1.yaml` semantics;
- generic `REFLECTION` primitive dispatch;
- FlowRuntime step order or state evaluation;
- actor/session/CaseVersion ownership checks;
- server-derived read-model fields or values;
- raw response/private reason non-exposure;
- completion-store reconciliation;
- lineage-cursor matching;
- idempotency-key creation or reuse;
- pending completion recovery;
- completion endpoint calls;
- post-completion Flow refresh/adoption;
- DecisionDraft persistence/cleanup behavior;
- DecisionRevision, DecisionDelta or Intervention creation/classification;
- routes or navigation;
- localized copy or raw backend values;
- collective results, Signal, Impact, advocacy or research inputs;
- My KEFE descriptive/non-inference boundary;
- backend, API or schema.

## Rejected alternatives

### Infer why the decision changed

Rejected. ADR-0026 explicitly defines the relationship as descriptive and non-causal.

### Turn Reflection completion into a new Decision

Rejected. Completion is an immutable acknowledgement at a lineage cursor and does not create or mutate DecisionRevision.

### Add a Case-specific Reflection screen

Rejected. Reflection remains one generic Flow primitive with no Case/domain/format branch.

### Show artificial progress while completing

Rejected. The client has no truthful progress measure.

### Keep dark-only tokens and patch light mode locally

Rejected. Slice 24 adopts shared semantic visual roles instead of maintaining parallel screen-local theme logic.

## Verification

Before PASS, one exact runtime SHA must pass:

- API CI;
- Mobile CI;
- MVP Beta Gates;
- Global Readiness.

Mobile verification must include:

- executable Slice 24 contract guard;
- existing ADR-0026/reflection-runtime semantic continuity;
- no generic Material `Card` in governed Reflection source;
- no `CircularProgressIndicator` in governed Reflection source;
- no direct dark-only presentation token or screen-local fixed RGB gradient;
- stable Reflection keys;
- deterministic loading, root error/retry, inline error, completing and completed states;
- completion action disablement and single-dispatch behavior;
- pending idempotency-key recovery continuity;
- non-causal note and actor-private/raw-value boundaries;
- generic Flow-driven DecisionRevision → Reflection → completion journey;
- dark/light, compact-phone and enlarged-text layout;
- full existing mobile regressions, production-copy boundary and phone acceptance.

Human visual/usability review remains external evidence.
