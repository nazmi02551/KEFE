# Activity History State and Localization Convergence — Slice 27

**Date:** 2026-08-01  
**Issue:** #162  
**Pull request:** #163  
**Stack parent:** PR #160 / `feature/progress-state-convergence-slice26`

## Verified runtime

`b8df16e0a4dc74750044a3cc7cd56aa7170157db`

All required repository-owned workflows succeeded on that exact SHA:

- API CI #964 / run `30697640968` — SUCCESS
- Mobile CI #752 / run `30697640977` — SUCCESS
- MVP Beta Gates #468 / run `30697640962` — SUCCESS
- Global Readiness #364 / run `30697640969` — SUCCESS

## Implemented scope

`ActivityScreen` now consumes the Slice 26 shared `ProgressAsyncStateSurface` for deterministic progress-history loading and retryable-error presentation.

Stable state keys:

- `activity-loading`
- `activity-error`
- `activity-retry`

Retry continues to invoke only the existing `ProgressController.load()` path.

Both enriched `MyKefeRecentJourney` rows and legacy `RecentProgressCase` rows now resolve their displayed title through `kefeContentLocalizerProvider` and `KefeContentNamespace.caseTitle`. The raw model title remains fallback only and is not mutated. The localized display title is also the semantic row label.

Decorative hero, history, arrow and Preview icons are excluded from independent semantics.

## Preserved boundaries

Slice 27 did not change:

- `ProgressController`, repository or provider selection;
- Activity history data contracts or ordering;
- readiness, update/reflection markers or methodology;
- pull-to-refresh;
- Saved Cases composition;
- empty-state and Product Preview notice behavior;
- row navigation route;
- account-offer behavior;
- production/Product Preview isolation;
- API, schema or migrations;
- Decision journey dispatch behavior;
- Commit First, Blind First or immutable CaseVersion;
- Activity/My KEFE observed-descriptive history boundary;
- personality, ideology, psychometric, bias, causal or normative inference boundaries;
- Signal/Impact boundaries.

## Executable evidence

Coverage includes:

- executable contract/source guards;
- shared loading/error/retry primitive consumption;
- one retry action producing one additional progress repository load;
- enriched history title localization;
- legacy history title localization;
- localized semantic row labels;
- Activity empty-state reachability in a lazy list;
- 360 × 800 viewport;
- 1.6× text scale;
- light/dark themes;
- full mobile regression, production-copy and phone-acceptance gates.

## Failed candidates retained as evidence

- `9df69f2d58beb235228a7d30526557b5a46bae31` — rejected because the canonical Dart formatter changed two long test assertions.
- `665b3e098030f8d13dc02d346889a0f3e8c2ce8e` — rejected because the compact test asserted a below-fold lazy `ListView` child before scrolling it into the build viewport. Runtime behavior was correct.
- `12aa0721ec20cddc25c3d68ce5f7cd48f62d96be` — rejected because the canonical formatter collapsed the new `scrollUntilVisible` invocation.

None of these candidates is PASS.

## Phone artifact

Global Readiness #364 produced:

- artifact: `kefe-internal-alpha-phone-preview`
- artifact ID: `8817831461`
- archive digest: `sha256:044b5155ed6f4ad5c6aaa6ef7b6aac3eded868b636d757aefaf426a0e14616c5`
- payload: `app-debug.apk`
- payload size: `160576458` bytes
- APK SHA-256: `7b299b52d56c0957604a819152153f5f8d1e036287b0021aab171a62fc8b3663`
- `beta-api.invalid`: absent in raw and unpacked scans.

This is an internal Product Preview artifact for the exact verified runtime. It is not production/public-beta/store, production-provider, editorial-acceptance or human-usability evidence.

## External gates

Still external and not proven by this slice:

- human visual/usability review;
- editorial CQB acceptance;
- real production provider delivery and SLO;
- store compliance/signing/review;
- operator-validated rollback controls.
