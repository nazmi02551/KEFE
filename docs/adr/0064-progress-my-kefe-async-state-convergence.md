# ADR-0064 — Progress and My KEFE Async-State Convergence

Date: 2026-08-01  
Status: Accepted for Slice 26 implementation  
Tracker: #159  
Stack parent: `feature/decision-information-state-slice25`

## Context

The active stack already presents post-Commit progress in two consumer surfaces:

- `ProgressSection`, composed after Perspective in the Decision journey;
- `MyKefeJourneyScreen`, the dedicated descriptive history destination.

Both surfaces read the same `progressControllerProvider`, but each independently renders loading and retryable-error UI. The duplicated implementations have drifted in stable keys, retry affordance, live-region treatment, decorative semantics and compact/enlarged-text coverage.

This is a presentation consistency problem. The `ProgressController`, repository, API projection and My KEFE product boundary remain valid.

## Decision

Slice 26 introduces one reusable, presentation-only progress async-state primitive consumed by both surfaces.

The primitive supports exactly two states:

- deterministic loading;
- retryable error with the existing load callback.

It accepts consumer-specific stable keys while using shared KEFE semantic surfaces and theme roles.

### Stable keys

`ProgressSection` preserves and completes:

- `progress-loading`;
- `progress-error`;
- `progress-retry`.

`MyKefeJourneyScreen` gains:

- `my-kefe-loading`;
- `my-kefe-error`;
- `my-kefe-retry`;
- `my-kefe-empty` for the existing zero-history state.

### Accessibility and visual behavior

The shared primitive must:

- use localized existing loading/unavailable/retry copy;
- announce loading/error changes as semantic live regions;
- exclude decorative status icons from independent semantics;
- use `KefeSurface` and `KefeVisualTheme` roles;
- remain valid in dark and light themes;
- remain usable at 360 × 800 and 1.6× text scale;
- avoid indeterminate spinners, artificial percentages and continuous decorative animation.

## Preserved behavior

Slice 26 does not change:

- `ProgressController` state transitions or duplicate-load guard;
- repository/provider selection;
- API, schema, migrations or routes;
- readiness, count, domain, recent-journey or methodology values;
- account-offer eligibility, placement, creation availability or guest dismissal;
- refresh behavior;
- Saved Cases composition;
- Product Preview/production isolation;
- Commit First, Blind First or immutable CaseVersion;
- localization/raw-value boundaries;
- My KEFE's observed/descriptive-only boundary;
- personality, ideology, psychometric, bias or causal inference prohibitions;
- Signal or Impact boundaries.

Retry invokes only the existing `ProgressController.load()` path. It does not replay answer, private reason, Commit, Reveal, Perspective or Reflection.

## Rejected alternatives

### Keep duplicated state widgets

Rejected. They already drift in keys and accessibility behavior and would require parallel maintenance.

### Add a progress percentage or skeleton implying completion

Rejected. The controller exposes no truthful progress measure.

### Move state handling into the controller

Rejected. The controller already has the correct domain-neutral state machine; this slice concerns presentation only.

### Infer a user profile from progress values

Rejected. My KEFE remains descriptive history and low-claim progress only.

## Verification

Before PASS, one exact runtime SHA must pass:

- API CI;
- Mobile CI;
- MVP Beta Gates;
- Global Readiness.

Mobile verification must include:

- executable Slice 26 contract guard;
- both consumers using the shared primitive;
- stable loading/error/retry/empty keys;
- no indeterminate spinner or generic Material `Card` in governed async-state sources;
- retry dispatch exactly once through the existing load path;
- ready data and account-offer continuity;
- My KEFE empty state and non-inference note continuity;
- dark/light, 360 × 800 and 1.6× text coverage;
- existing regressions, production-copy boundary and phone acceptance.

Human visual/usability, editorial, production provider/SLO, store and operator rollback evidence remain external.