# ADR-0050: Progressive Active-Step Decision Journey

- Status: Accepted for implementation
- Date: 2026-08-03
- Issue: #277
- Base: PR #118 (`feature/premium-history-slice11`)

## Context

The shared mobile Decision Flow renderer currently places every runtime-supported step in one vertical `ListView`. The runtime remains authoritative, but completed Context, ready Decision, Collective Result, Perspectives, Progress and Reflection surfaces can accumulate into a long page. This weakens focus, makes the active task less obvious and does not express the intended KEFE decision journey as clearly as the existing Flow progress rail.

KEFE must also support materially different generic flows, including repeated Decision primitives, Context between revisions, optional Collective Result and Reflection-only endings. A screen-specific hardcoded wizard would duplicate or override Flow authority and would not be acceptable.

The onboarding copy also currently combines community comparison, perspective discovery and longitudinal change in one promise. The product value can be explained more clearly as three concise stages without claiming a personality profile, social rank or causal effect.

## Decision

### 1. Runtime-authoritative active step

The mobile Decision Flow presentation will default to a progressive active-step mode:

- the Case hero and Flow progress rail remain visible;
- exactly one runtime step is presented as the primary active surface;
- the active runtime step is selected from server-provided `FlowRuntimeSnapshot.steps`, preferring `READY`, then actionable `UNSUPPORTED`, and never inventing a default order;
- completed and blocked states remain visible in the Flow rail but are not re-rendered as full long-scroll sections;
- repeated primitives remain distinct through their runtime step identity and order;
- Context exposure, Decision commit, Result, DecisionRevision and Reflection behavior remain owned by the existing controller/repository contracts.

### 2. Presentation sub-stages may not become domain steps

A runtime primitive may use local presentation sub-stages only to progressively disclose content that is already authorized by that primitive. In the initial slice, Collective Result may show the committed personal/community result first and reveal Perspectives through an explicit user action. This local disclosure:

- does not create a new Flow primitive;
- does not unlock data before Commit;
- does not replay Commit, responses or private reasons;
- does not change repository or API semantics.

### 3. Reusable presentation boundary

A reusable, feature-neutral active-journey component will live under the shared mobile design layer. Future sequential screens should use this component when all of the following are true:

- there is one authoritative current stage;
- earlier stages are completed history rather than simultaneously editable forms;
- advancement is controlled by domain/runtime state rather than scroll position;
- accessibility, reduced motion and deterministic tests can be preserved.

List, dashboard, feed, discovery, comparison and reference-information screens must not be converted merely because they are vertically long.

### 4. Rollback and compatibility

The existing long-scroll renderer will remain available in the same codebase for this slice. Build-time switches will independently control:

- progressive Decision Journey presentation;
- onboarding copy/page version.

The default build enables the new experience. A build can restore the previous presentation without reverting domain, API or persistence changes. The entire slice is also isolated in a stacked branch/PR so a normal Git revert remains available.

No remote kill-switch, operator rollback or production rollout claim is introduced by this ADR.

### 5. Onboarding v2

Onboarding will use three concise promises:

1. make and see your own decision before community exposure;
2. see where that decision sits within the community distribution;
3. inspect different perspectives and follow the observed decision journey.

The Turkish wording may say “Kararının toplumdaki yerini gör,” but must refer to the decision’s descriptive position in a distribution—not the person’s social value, identity, ideology or personality. English copy must preserve the same boundary.

## Invariants

- Commit First and Blind First remain binding.
- Published CaseVersion immutability remains binding.
- Flow runtime remains case-agnostic and authoritative.
- Preview data never becomes a production fallback.
- No personality, ideology, psychometric, bias, morality, social-worth or causal inference is introduced.
- Existing answer, reason, draft, retry, idempotency, exposure and Reflection contracts remain unchanged.
- Result and Perspective data remain post-Commit only.

## Consequences

### Positive

- the user sees one clear task at a time;
- the visual journey matches generic runtime state;
- revision and Reflection flows can reuse the same presentation model;
- future suitable sequential screens gain a governed reusable component;
- rollback is possible without undoing domain work.

### Costs and risks

- hidden completed content is less immediately scannable than the legacy long page;
- local Result disclosure state requires dedicated widget coverage;
- deep links do not target a presentation sub-stage in this slice;
- human phone usability remains pending until an exact-head artifact is reviewed.

## Verification

The implementation must add tests proving:

- the default mode renders only the authoritative active runtime step;
- legacy mode preserves the previous long-scroll behavior;
- no Result/Perspective appears before Commit;
- Result appears before Perspective disclosure;
- repeated/revision flows advance according to refreshed runtime state;
- onboarding v2 has three pages and guarded TR/EN copy;
- onboarding legacy mode remains available;
- the reusable component has semantics and reduced-motion-safe transitions;
- all existing mobile regression and phone-acceptance gates remain green.
