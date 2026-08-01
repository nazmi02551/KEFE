# ADR-0063 — Decision Journey Information-State Convergence

Date: 2026-08-01  
Status: Accepted for Slice 25 implementation  
Tracker: #156  
Stack parent: `feature/reflection-state-convergence-slice24`

## Context

The canonical active stack has converged the principal consumer journey onto shared KEFE semantic surfaces through Explore, Decision Flow, Reveal, Perspective content and Reflection.

A fresh audit found two residual indeterminate async states in that same journey:

- `ContextSection` still renders a `CircularProgressIndicator` while loading pre-Commit Context;
- `PerspectiveSection` still renders a `CircularProgressIndicator` while loading post-Commit Perspective.

The loaded Context and Perspective content already uses theme-adaptive KEFE presentation. The remaining inconsistency is the state layer, not the underlying product, methodology, controller or repository contract.

## Decision

Slice 25 converges the async information states for Context and Perspective onto deterministic shared KEFE semantic surfaces.

### Context state boundary

Context remains a pre-Commit-safe, optional CaseVersion-pinned information surface.

The existing provider/repository remains authoritative. Slice 25 changes only presentation for:

- loading;
- retryable error;
- retry action.

Loading uses a deterministic semantic status with the existing localized loading string. No percentage, estimated completion or network-success implication is invented.

The error state retains the existing localized unavailable and retry copy. The retry action continues to invalidate only `contextSnapshotProvider(caseVersionId)`.

An empty Context snapshot remains omitted with `SizedBox.shrink()`. The client does not fabricate Context blocks, source claims or placeholder evidence.

### Perspective state boundary

Perspective remains bounded post-Commit information. It is not requested or shown before successful Commit/Reveal.

Slice 25 changes only presentation for:

- loading;
- retryable error;
- retry action;
- the defensive case where a loaded state unexpectedly has no result.

Loading uses deterministic semantic status with the existing localized loading string. Retry continues to call only the existing `onRetry` path.

The defensive null-result state uses the existing unavailable copy in a semantic surface. It does not create cards, methodology, fallback content or result values.

### Stable state keys

Slice 25 preserves existing keys and adds deterministic state keys:

- Context: `context-section`, `context-error`, `context-loading`, `context-retry`;
- Perspective: `perspective-section`, `perspective-loading`, `perspective-error`, `perspective-retry`, `perspective-unavailable`.

### Accessibility, theme and motion

The governed states must support:

- dark and light themes through `KefeVisualTheme` roles;
- 360 × 800 phone viewport;
- 1.6× text scale;
- semantic live regions for loading/error changes;
- decorative status icons excluded from independent semantics;
- no indeterminate spinner;
- no continuous decorative animation;
- no artificial progress measure.

## Preserved behavior

Slice 25 does not change:

- Context repository/provider/controller behavior;
- Context pre-Commit availability;
- Context block/source ordering, disclosure level, claim status, raw content or source relationship;
- Perspective controller/repository behavior;
- Perspective pre-Commit absence;
- Perspective retry semantics;
- answer, private reason, Commit or Reveal dispatch counts;
- Perspective card order, slots, source/provenance values or methodology;
- curated fallback and cluster-pending semantics;
- Consensus, Community Reasons, Progress and Share composition;
- Commit First or Blind First;
- immutable CaseVersion;
- generic case-agnostic runtime;
- Preview/production isolation;
- localization/raw-value boundary;
- My KEFE descriptive/non-inference boundary;
- Signal/Impact boundaries;
- routes, backend, API or schema.

## Rejected alternatives

### Show artificial progress

Rejected. Neither provider exposes a truthful completion percentage or duration estimate.

### Fabricate placeholder Context or Perspective content

Rejected. Empty/absent data must remain empty/absent rather than becoming invented evidence or viewpoints.

### Retry the entire Decision journey

Rejected. Context retry invalidates only its provider. Perspective retry invokes only its existing retry callback and must not replay answer, reason, Commit or Reveal.

### Combine Context and Perspective data contracts

Rejected. The slice unifies presentation-state quality only; pre-Commit Context and post-Commit Perspective remain separate product/methodology boundaries.

## Verification

Before PASS, one exact runtime SHA must pass:

- API CI;
- Mobile CI;
- MVP Beta Gates;
- Global Readiness.

Mobile verification must include:

- executable Slice 25 contract guard;
- no `CircularProgressIndicator` in governed Context/Perspective sources;
- stable and new state keys;
- deterministic Context loading/error/retry;
- Context empty omission and pre-Commit content continuity;
- deterministic Perspective loading/error/unavailable states;
- Perspective pre-Commit absence;
- Perspective retry does not replay answer, private reason, Commit or Reveal;
- loaded Perspective card/methodology/composition continuity;
- dark/light, compact-phone and enlarged-text layout;
- existing mobile regressions, production-copy boundary and phone acceptance.

Human visual/usability, editorial, production provider/SLO, store and operator rollback evidence remain external.
