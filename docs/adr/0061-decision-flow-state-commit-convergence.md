# ADR-0061 — Decision Flow State and Commit Convergence

Date: 2026-08-01  
Status: Accepted for Slice 23 implementation  
Tracker: #150  
Stack parent: `feature/premium-explore-discovery-slice22`

## Context

KEFE's primary Case journey is already functionally complete and governed by the generic flow runtime. It preserves Commit First, Blind First, immutable CaseVersion, generic primitive dispatch, uncertain-Commit recovery, Reveal, Perspective, Reflection and first-use completion.

The surrounding `DecisionFlowScreen` presentation still contains residual state debt:

- initial Case loading uses an indeterminate `CircularProgressIndicator`;
- Commit submitting uses a second indeterminate spinner inside the action;
- the root `AnimatedSwitcher` uses a fixed duration instead of `KefeMotion.resolve`;
- unsupported capability presentation uses a generic Material `Card`;
- root error and inline status presentation are not aligned with shared KEFE semantic surfaces.

This creates inconsistent behavior relative to the verified premium Explore, Reveal, Perspective, first-use and visual-composition slices.

## Decision

Slice 23 converges the Decision Flow state and Commit presentation onto shared theme-adaptive KEFE primitives without changing the decision state machine.

### Root state presentation

Initial loading becomes a deterministic semantic status surface. It must not use an indeterminate progress spinner or continuous decorative animation.

Root loading/content/error transition duration must resolve through `KefeMotion.resolve`. Reduce Motion or accessible navigation collapses the transition to zero duration.

Root error uses a shared KEFE raised surface with localized message and retry action. Retry continues to invoke the existing `_load` path.

### Commit action presentation

The existing Commit button remains the only Commit action and keeps its stable `commit-button` key.

Enablement remains exactly:

- disabled when required responses are incomplete;
- disabled while submitting;
- retry-pending action when recovery is pending;
- normal Commit otherwise.

Submitting presentation becomes deterministic and semantic. It may replace the button label/icon with a bounded status treatment, but must not introduce a second Commit action, progress percentage, optimistic success or continuous spinner.

The helper text remains driven only by existing required-response, recovery-pending and normal Commit states.

### Inline status

The existing `decision-status-message` live region remains. It moves into a shared semantic surface and preserves the distinction between offline-draft/recovery information and error information through theme-adaptive roles.

No raw error code or technical transport detail becomes user-facing.

### Unsupported capability

`_CapabilityPendingCard` moves from generic Material `Card` to `KefeSurface`. Existing localized title/body and stable `capability-pending-<stepCode>` key remain authoritative.

No unsupported primitive is silently hidden, reordered or treated as completed.

### Accessibility and responsive behavior

- deterministic loading and submitting status remain screen-reader discoverable;
- loading/status surfaces use live-region semantics where appropriate;
- decorative icons are excluded from independent semantics;
- dark and light theme remain valid;
- 360×800 and enlarged text must not overflow;
- no essential text is painted inside a custom painter;
- no continuous idle animation is introduced.

## Preserved behavior

Slice 23 does not change:

- DecisionController or repository behavior;
- question definitions, raw answer values or response persistence;
- required-response validation;
- reason-tag or private-reason semantics;
- Commit request payload, idempotency or uncertain-Commit recovery;
- pre-Commit Reveal absence;
- flow primitive order or generic dispatch;
- Context exposure recording;
- Reveal, Perspective, Reflection or first-use completion;
- CaseVersion immutability;
- production/Product Preview isolation;
- routes or stable interaction keys;
- My KEFE non-inference;
- Signal/Impact boundaries;
- backend/API/schema.

## Verification

Before PASS, one exact runtime SHA must pass:

- API CI;
- Mobile CI;
- MVP Beta Gates;
- Global Readiness.

Mobile verification must include:

- executable contract guard;
- no governed `CircularProgressIndicator` in `decision_flow_screen.dart`;
- `KefeMotion.resolve` controls root state transition;
- loading/error/capability/status surfaces use `KefeSurface`;
- Commit enablement and recovery behavior unchanged;
- submitting state is deterministic and prevents duplicate Commit;
- Reveal remains absent before Commit;
- existing question/reason/Context/Reveal/Perspective/Reflection continuity;
- dark/light, 360×800 and 1.6× text scale;
- production copy boundary, full mobile regressions and phone acceptance.

Human visual/usability review remains external evidence.
