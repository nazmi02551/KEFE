# ADR-0065 — Activity History State and Localization Convergence

Date: 2026-08-01  
Status: Accepted for Slice 27 implementation  
Tracker: #162  
Stack parent: `feature/progress-state-convergence-slice26`

## Context

Slice 26 introduced `ProgressAsyncStateSurface` for `ProgressSection` and `MyKefeJourneyScreen`, which are consumers of the same `progressControllerProvider` used by Activity.

A fresh audit found that `ActivityScreen` still:

- duplicates its own loading and retryable-error presentation;
- has no stable keys for those async states;
- renders enriched and legacy history titles directly from raw model values instead of applying the governed display-time Case title localizer.

The underlying progress/history contract is already settled. The remaining work is presentation/state and localization convergence.

## Decision

Slice 27 updates only `ActivityScreen` presentation.

### Shared async states

Activity must consume `ProgressAsyncStateSurface` for:

- idle/loading;
- retryable error;
- retry action.

Stable keys:

- `activity-loading`;
- `activity-error`;
- `activity-retry`.

Loading remains deterministic and does not expose a percentage or estimated completion. Retry invokes only the existing `ProgressController.load()` path.

### Display-time title localization

Both enriched `MyKefeRecentJourney` rows and legacy `RecentProgressCase` rows must resolve their displayed title through:

- `kefeContentLocalizerProvider`;
- `KefeContentNamespace.caseTitle`;
- the current locale;
- the raw model title only as fallback.

The localized display title must also be used for the row's semantic label. Stored/backend/model values are not mutated.

### Preserved behavior

Slice 27 does not change:

- `ProgressController`, repository or provider selection;
- progress/history/account-offer data contracts;
- Activity pull-to-refresh;
- Saved Cases composition or visibility;
- empty-state behavior;
- Product Preview notice behavior;
- row navigation route;
- history ordering, update/reflection markers or methodology;
- production/Product Preview isolation;
- API, schema or migrations;
- Decision journey dispatch behavior;
- Commit First, Blind First or immutable CaseVersion;
- My KEFE/Activity descriptive-only and non-inference boundaries;
- Signal/Impact boundaries.

## Accessibility and layout

The governed states and rows must support:

- light and dark themes;
- 360 × 800 viewport;
- 1.6× text scale;
- live-region state announcements through the shared primitive;
- localized semantic labels;
- no indeterminate spinner or artificial progress;
- no continuous decorative animation.

## Rejected alternatives

### Keep Activity-specific async UI

Rejected. Activity consumes the same controller and state semantics, so duplicated state presentation creates unnecessary drift.

### Localize model values before storage

Rejected. Display localization must not mutate raw backend/history values.

### Add history inference or ranking

Rejected. Activity remains observed/descriptive actor history only.

## Verification

Before PASS, one exact runtime SHA must pass API CI, Mobile CI, MVP Beta Gates and Global Readiness. Executable coverage must include shared-state consumption, stable keys, loading/error/retry, localized enriched/legacy rows, semantic labels, empty/preview/navigation continuity and compact/enlarged-text theme regressions.

Human usability, editorial, production provider/SLO, store and rollback evidence remain external.