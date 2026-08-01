# Saved Cases Persistence-State Reliability Convergence — Slice 28

**Date:** 2026-08-01  
**Issue:** #164  
**Pull request:** #165  
**Stack parent:** PR #163 / `feature/activity-history-convergence-slice27`

## Verified runtime

`eb1d5dbea2218f3e8730909b47af64459c6b0b45`

All required repository-owned workflows succeeded on that exact SHA:

- API CI #974 / run `30698260150` — SUCCESS
- Mobile CI #761 / run `30698260157` — SUCCESS
- MVP Beta Gates #478 / run `30698260162` — SUCCESS
- Global Readiness #373 / run `30698260156` — SUCCESS

## Implemented scope

Saved Cases now presents the existing `SavedCasesController` state contract truthfully:

- idle/first-load loading renders deterministic `saved-cases-loading`;
- loading with existing items preserves those items and adds a non-blocking status disclosure;
- error with zero items renders `saved-cases-error` and `saved-cases-retry` rather than claiming the list is empty;
- error with existing items preserves those items and adds retryable error disclosure;
- only successful ready/zero-items state renders `saved-cases-empty`.

A feature-local `SavedCasesStateSurface` provides live-region announcements, decorative-icon semantic exclusion and theme-adaptive KEFE presentation without indeterminate progress or artificial completion claims.

The Saved Cases localization catalog now includes governed English and Turkish loading, unavailable and retry resources.

Retry invokes only `SavedCasesController.load()`.

## Preserved boundaries

Slice 28 did not change:

- `SavedCasesController` state machine or duplicate-load guard;
- `SavedCaseStore` interface, persistence key or serialized format;
- optimistic `toggle` and `remove` behavior;
- write-failure reload behavior;
- saved-item ordering or deduplication;
- open/remove routes and actions;
- visibility-triggered loading;
- display-time Case title/summary localization;
- production/Product Preview isolation;
- API, schema or migrations;
- Commit First, Blind First or immutable CaseVersion;
- My KEFE/Activity non-inference boundaries;
- Signal/Impact boundaries.

## Stable keys

- `saved-cases-loading`
- `saved-cases-error`
- `saved-cases-retry`
- preserved `saved-cases-empty`

## Executable evidence

Coverage includes:

- executable contract/source guards;
- deterministic first load without empty-state leakage;
- error-with-zero-items distinct from empty;
- retry producing one additional store read;
- stale items preserved during refresh loading;
- stale items preserved after refresh failure;
- existing optimistic remove/write behavior;
- English retry localization;
- Turkish compact error presentation;
- light/dark themes;
- 360 × 800 viewport and 1.6× text scale;
- full mobile regression, production-copy and phone-acceptance gates.

## Failed candidate retained as evidence

`5a7d1030a9ad921420c79cb4bc199b61c187cdec` was rejected because the canonical Dart formatter changed the new state surface and test file. The MVP format gate stopped before mobile tests. It is not PASS.

## Phone artifact

Global Readiness #373 produced:

- artifact: `kefe-internal-alpha-phone-preview`
- artifact ID: `8818009938`
- archive digest: `sha256:af8e99918c46c2ee517c69a719a83175989fb50d07a4facc3f81b67b5a8fe2e9`
- payload: `app-debug.apk`
- payload size: `160578938` bytes
- APK SHA-256: `421e02b2e370ea3427af97e64e857b167026e86d21043039a459d554c251ba97`
- `beta-api.invalid`: absent in raw and unpacked scans.

This is an internal Product Preview artifact for the exact verified runtime. It is not production/public-beta/store, production-provider, editorial-acceptance or human-usability evidence.

## External gates

Still external and not proven by this slice:

- human visual/usability review;
- editorial CQB acceptance;
- real production provider delivery and SLO;
- store compliance/signing/review;
- operator-validated rollback controls.
