# ADR-0061 — Decision Flow Shell and State Convergence

Date: 2026-08-01  
Status: Accepted for Slice 23 implementation  
Tracker: #148  
Stack parent: `feature/premium-explore-discovery-slice22`

## Context

The active stacked line already contains premium, theme-adaptive implementations for the nested Decision Journey surfaces: Context, Question input, Signature Balance, private Reason, Reveal, Perspective and first-use completion.

The shared `DecisionFlowScreen` shell still has a visibly older state layer:

- initial loading uses an indeterminate `CircularProgressIndicator`;
- Commit submission replaces the canonical button label with an indeterminate spinner;
- unsupported FlowRuntime capability uses a generic Material `Card`;
- load error and inline sync/error status are plain text/button arrangements;
- the root `AnimatedSwitcher` uses a fixed duration instead of `KefeMotion.resolve`;
- production shows a plain Case title/summary while Product Preview shows the richer `CaseHeroHeader`.

The Product Preview hero may render Preview media because Preview explicitly overrides the media repository. Production currently defaults to `EmptyCaseMediaRepository`. Preview fixtures must never become production fallback.

## Decision

Slice 23 converges the shared Decision Flow shell and its runtime states onto the existing KEFE semantic visual system without changing domain, controller, FlowRuntime, routing or methodology behavior.

### Root state transition

The existing loading / error / loaded state switch remains. Its transition duration resolves through `KefeMotion.resolve` so Reduce Motion and accessible navigation collapse the transition to zero.

### Deterministic loading and working states

Initial loading and Commit submission use deterministic semantic status presentation rather than indeterminate progress animation.

The existing localized strings remain authoritative. No estimated progress, completion percentage or network certainty is invented.

Commit remains the same action:

- stable `commit-button` key;
- disabled while required responses are missing or submission is active;
- retry behavior continues to use `retryPending` when recovery is pending;
- normal behavior continues to use `commit`;
- helper text continues to derive from required/recovery/normal state;
- no Reveal or Perspective appears before successful Commit.

### Production Case summary header

Production retains a text-only Case header because its media repository may legitimately be empty. The title and summary move into a premium, theme-adaptive KEFE surface.

This production header:

- preserves the `case-title` key;
- displays the same raw Case title and summary values already shown by production;
- does not show Preview media, Preview fixture attribution, new metadata claims or Preview-only localization substitutions;
- does not attempt to fall back to Preview data.

Product Preview keeps the existing `CaseHeroHeader` behavior and its explicit Preview repository wiring.

### Capability pending, load error and inline status

Unsupported capability, initial load error and inline status messages use shared KEFE surfaces with semantic accent roles.

Existing localized copy, reason-code mapping, retry action, live-region behavior and stable keys remain unchanged.

An inline offline-draft/sync status remains descriptive. It does not imply successful server persistence or result availability.

### Accessibility and layout

The governed shell must support:

- dark and light themes;
- 360 × 800 phone viewport;
- 1.6× text scale;
- semantic live regions for state changes;
- no independent semantics for decorative icons;
- no continuous decorative animation.

## Preserved behavior

Slice 23 does not change:

- `/case/:caseId` routing or app navigation;
- `DecisionController` load, response, reason, Commit, recovery or Perspective behavior;
- FlowRuntime step order, primitive mapping, blocked-state hiding or unsupported-state semantics;
- Context exposure recording;
- Commit First / Blind First;
- pre-Commit result/Perspective isolation;
- immutable CaseVersion;
- raw Case/question/option/reason values;
- display-localization boundaries;
- first-use completion timing or `/explore` continuation;
- Product Preview/production repository isolation;
- My KEFE non-inference;
- Signal/Impact boundaries;
- backend, API or schema.

## Rejected alternatives

### Use Product Preview media as production fallback

Rejected. This would violate Preview/production isolation and could present representative fixtures as production content.

### Show artificial progress during Commit

Rejected. The client has no truthful percentage or deterministic completion estimate.

### Rebuild nested Question/Reveal/Perspective surfaces in this slice

Rejected. Those surfaces already have separate verified contracts and are outside the residual shell/state scope.

## Verification

Before PASS, one exact runtime SHA must pass:

- API CI;
- Mobile CI;
- MVP Beta Gates;
- Global Readiness.

Mobile verification must include:

- executable contract guard;
- no indeterminate spinner in governed `DecisionFlowScreen` source;
- no generic Material `Card` in governed `DecisionFlowScreen` source;
- root transition uses `KefeMotion.resolve`;
- production text-only premium Case header preserves raw title/summary and `case-title` key;
- Product Preview continues to use `CaseHeroHeader` with explicit repository isolation;
- loading, error, capability-pending, Commit-working and inline-status surface coverage;
- stable Commit controller routing and key preservation;
- no Reveal before Commit;
- first-use completion continuity;
- dark/light, compact-phone and enlarged-text layout;
- full existing mobile regressions, production-copy boundary and phone acceptance.

Human visual/usability review remains external evidence.
