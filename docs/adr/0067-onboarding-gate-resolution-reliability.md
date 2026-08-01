# ADR-0067: Onboarding Gate Resolution Reliability

- Status: Accepted for Slice 29
- Date: 2026-08-01
- Issue: #169

## Context

`OnboardingGateScreen` resolves the persisted onboarding-completion flag before deciding whether to route to Explore or render onboarding. The existing asynchronous lookup has no explicit failure state. If persistence throws, the future terminates and the screen can remain indefinitely in its loading presentation.

This is a launch-path reliability defect. It must be fixed without changing what “onboarding completed” means, without mutating persistence, and without silently bypassing onboarding.

## Decision

The screen owns a small presentation-local resolution state machine:

- `resolving`: one completion lookup is active;
- `ready`: the store returned incomplete, or `reviewMode` explicitly exposes onboarding;
- `error`: the lookup failed and a retry action is available.

A duplicate-resolution guard prevents concurrent lookup attempts. Retry invokes only the existing `OnboardingController.isCompleted()` method.

Successful semantics remain unchanged:

- completed → navigate to `/explore`;
- incomplete → render the existing onboarding pages;
- `reviewMode` → render onboarding immediately and do not read persistence.

Failure never marks onboarding complete, never writes persistence, and never routes around onboarding.

## Presentation contract

- Loading key: `onboarding-loading`.
- Error key: `onboarding-error`.
- Retry key: `onboarding-retry`.
- Loading and error surfaces use semantic KEFE roles and live-region announcements.
- Decorative icons are excluded from semantics.
- No indeterminate progress indicator, artificial percentage, or continuous animation.

## Explicit non-changes

- no `OnboardingController` or `OnboardingStore` interface change;
- no persistence key, format, completion meaning, onboarding copy/page, route, API, schema, migration, auth, or Product Preview provider change;
- no automatic completion or fallback write on read failure.

## Evidence

Slice 29 requires executable contract/source/widget coverage plus exact-SHA success in API CI, Mobile CI, MVP Beta Gates, and Global Readiness. CI does not prove human usability, production persistence behavior across all devices, store compliance, or production SLOs.
