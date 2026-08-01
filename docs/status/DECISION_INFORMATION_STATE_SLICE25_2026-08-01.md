# Decision Journey Information-State Convergence — Slice 25 Verification

**Date:** 2026-08-01  
**Tracker:** #156  
**Pull request:** #157  
**Stack parent:** PR #154 / `feature/reflection-state-convergence-slice24`  
**Verified runtime SHA:** `1578b27d931e1856655c0734f8d8991817c9c00c`

This document is the durable verification record for Slice 25. Any later commit on the branch that changes documentation only does not redefine the verified runtime SHA above.

## Scope

Slice 25 converges the remaining indeterminate async information states in the primary Decision Journey:

- pre-Commit Context loading/error/retry;
- post-Commit Perspective loading/error/retry and defensive unavailable state.

The slice changes presentation and executable coverage only. It does not change:

- Context or Perspective provider/controller/repository behavior;
- Context pre-Commit availability;
- Perspective post-Commit/Reveal isolation;
- answer, private reason, Commit or Reveal dispatch;
- Context block/source values, ordering, disclosure or claim status;
- Perspective cards, slots, source/provenance values, methodology or API order;
- Consensus, Community Reasons, Progress or Share composition;
- routes, backend, API or schema;
- Commit First, Blind First, immutable CaseVersion or generic runtime;
- Preview/production isolation;
- My KEFE, Signal or Impact boundaries.

## Implemented Context convergence

`apps/mobile/lib/features/context/presentation/context_section.dart` now provides:

- deterministic semantic loading state with `context-loading`;
- theme-adaptive error state with `context-error`;
- stable `context-retry` action;
- live-region treatment for loading/error changes;
- decorative status icons excluded from independent semantics;
- no indeterminate spinner or artificial progress.

Retry still invalidates only `contextSnapshotProvider(caseVersionId)`. Empty optional Context remains omitted with `SizedBox.shrink()`; no placeholder Context, source or evidence is fabricated.

## Implemented Perspective convergence

`apps/mobile/lib/features/decision/presentation/perspective_section.dart` now provides:

- deterministic semantic loading state with `perspective-loading`;
- theme-adaptive retryable error state with `perspective-error`;
- preserved stable `perspective-retry` action;
- defensive semantic unavailable state with `perspective-unavailable` when a loaded state unexpectedly has no result;
- live-region treatment for meaningful state changes;
- decorative status icons excluded from independent semantics;
- no indeterminate spinner or artificial progress.

Perspective remains absent before Commit/Reveal. Retry continues to invoke only the existing Perspective retry callback and does not replay answer, private reason, Commit or Reveal.

## Stable state keys

- `context-section`
- `context-loading`
- `context-error`
- `context-retry`
- `perspective-section`
- `perspective-loading`
- `perspective-error`
- `perspective-retry`
- `perspective-unavailable`

## Executable verification

New regression file:

`apps/mobile/test/decision_information_state_slice25_test.dart`

Coverage includes:

- executable Slice 25 contract guard;
- governed-source boundary guard;
- Context deterministic loading and resolution;
- Context error/retry provider invalidation;
- Context empty omission;
- Perspective deterministic loading;
- Perspective retry callback isolation;
- Perspective defensive null-result state;
- dark/light themes;
- 360 × 800 viewport;
- 1.6× text scale;
- no indeterminate spinner.

Existing repository tests also continue to prove:

- Context remains visible before Commit;
- Perspective is not requested or visible before Commit;
- Perspective retry never replays answer, reason, Commit or Reveal;
- loaded Perspective cards, methodology and downstream committed composition remain intact.

The Context error test disables Riverpod automatic provider retry only inside the test `ProviderScope`, so the error surface can be observed deterministically. Production retry policy and provider implementation are unchanged.

## Exact-runtime workflow evidence

All required repository-owned workflows succeeded on the same exact runtime SHA `1578b27d931e1856655c0734f8d8991817c9c00c`:

- API CI #945 — run `30695358124` — SUCCESS
- Mobile CI #735 — run `30695358118` — SUCCESS
- MVP Beta Gates #449 — run `30695358112` — SUCCESS
- Global Readiness #347 — run `30695358132` — SUCCESS

The successful gates include formatting, analyzer, full mobile regressions, accessibility/locale/theme checks, API contracts and tests, PostgreSQL integration, production-copy boundary, phone acceptance and Android candidate builds.

## Phone artifact evidence

Global Readiness #347 produced:

- artifact name: `kefe-internal-alpha-phone-preview`
- artifact ID: `8817119041`
- artifact archive digest: `sha256:f9e296b3a8a27c9f9eaba9f0d2c3b6115890b23d8bf1a6744b3c672f92c1a11c`
- payload: `app-debug.apk`
- payload size: `160577802` bytes
- APK SHA-256: `19f555f1976619d4e611c5c591fdf193c4e2fd7613d3761d84c9eaa98a02dc99`
- `beta-api.invalid` raw APK scan: ABSENT
- `beta-api.invalid` unpacked APK scan: ABSENT

This artifact is an internal Product Preview phone candidate for the exact verified runtime. It is not production/public-beta/store, production-provider, editorial-acceptance or human-usability evidence.

## Failed-candidate evidence retained

The following candidate SHAs were not accepted:

### `ad597b7900df7caa61c53d24d4e5cc5b8836c7ac`

- API CI succeeded;
- MVP Beta Gates detected canonical Dart format drift;
- the initial Context error test failed because its fixture lifecycle did not isolate the error state;
- no PASS claim was made.

### `2e5621fb6d1e40ec68c572de921b63e38631b086`

- format and analyzer gates succeeded;
- the Context error assertion still failed;
- no PASS claim was made.

### `5a33a8edc7dfe0f8ff7971863380d370d839fbd8`

- source formatting and analyzer succeeded;
- the direct family-provider override still auto-retried under Riverpod 3 before the error surface could be observed;
- no PASS claim was made.

The final test disables automatic retry only in the test scope, exercises the first error and explicit retry deterministically, and leaves production behavior unchanged. The accepted runtime is `1578b27d931e1856655c0734f8d8991817c9c00c`.

## External evidence still pending

Repository CI does not prove:

- human phone visual approval;
- human usability;
- editorial CQB acceptance;
- real production provider/network/SLO readiness;
- Apple/Google store compliance, signing or review;
- operator-validated production rollback.

## Continuation

PR #157 remains stacked on PR #154 and must not be merged before its parent chain. The next slice must begin with a fresh audit from the canonical top branch after re-reading `AGENTS.md`, `docs/status/CURRENT.md`, this verification record and live GitHub/CI state.
