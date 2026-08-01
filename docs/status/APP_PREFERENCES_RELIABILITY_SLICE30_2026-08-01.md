# App Preferences Persistence Reliability — Slice 30 Verification

**Date:** 2026-08-01  
**Issue:** #172  
**PR:** #173  
**Parent:** PR #170 / Slice 29  
**Verified runtime SHA:** `e41cea5fc7bccb4bbe085b48cd15ea5a2fead082`

## Scope closed

Slice 30 makes locale/theme preference persistence explicit, recoverable and truthful without changing the preference model.

- `AppPreferencesController` now owns idle, loading, ready, saving and error state.
- read failures are caught instead of escaping a fire-and-forget startup task;
- startup continues with deterministic system defaults while persistence resolves;
- Settings starts the existing guarded load path when opened independently;
- unresolved/read-error fallback choices remain visible for structural continuity but are disabled and accompanied by a loading/error disclosure;
- retry invokes only the existing store read path;
- locale/theme writes are single-flight and optimistic only while saving;
- write failure restores the last known persisted locale/theme snapshot;
- loading, error, retry and saving states use stable keys and a KEFE semantic state surface;
- compact error presentation places retry below the message and remains valid at 360×800 with 1.6× text;
- EN/TR and light/dark behavior is covered.

## Preserved boundaries

No change was made to:

- `AppPreferencesStore` interface;
- SharedPreferences keys;
- enum-name serialization;
- locale choices or meaning;
- theme choices or meaning;
- routes, onboarding or Privacy semantics;
- API, schemas or migrations;
- authentication;
- production/Product Preview provider isolation.

The root app still does not block launch on preferences persistence. Disabled system-default choices before a successful read are fallback presentation, not a claim that those values were persisted.

## Executable evidence

Tests cover:

- contract/source boundary guards;
- read failure and retry recovery;
- locale write rollback;
- theme write rollback;
- duplicate load guard;
- duplicate write guard;
- disabled fallback choices before persistence recovery;
- retry re-enabling settings interaction;
- saving disclosure and single-flight UI behavior;
- compact 360×800, 1.6× text;
- Turkish and English;
- light and dark themes;
- prior Slice 13 Settings semantic regressions;
- absence of indeterminate progress indicators.

## Exact-SHA workflow evidence

All required workflows succeeded on `e41cea5fc7bccb4bbe085b48cd15ea5a2fead082`:

- API CI #1002 / run `30708122770` — SUCCESS
- Mobile CI #788 / run `30708122780` — SUCCESS
- MVP Beta Gates #506 / run `30708122782` — SUCCESS
- Global Readiness #400 / run `30708122781` — SUCCESS

## Phone artifact

Global Readiness #400 produced:

- artifact: `kefe-internal-alpha-phone-preview`
- artifact ID: `8821041756`
- archive digest: `sha256:bdfd0dc95833082edd5525eda134287fa4105b04ec5d904458a423bd7cd03923`
- payload: `app-debug.apk`
- APK size: `160585878` bytes
- APK SHA-256: `c8ba5f717e86543d1ffc0fbfe3c6f87dc7c01469f87d45d30591569351404389`
- `beta-api.invalid`: absent in raw and unpacked scans.

This artifact is an internal Product Preview candidate for the exact verified runtime. It is not production/store, human usability, target-device persistence reliability, provider delivery, editorial CQB, production SLO or rollback evidence.

## Rejected candidates

The following candidates are not PASS:

- `a68b1caaf5feb67642df276a8d04bd04353d742f` — MVP canonical Dart format drift; its Mobile CI also exposed preference/Settings regression failures.
- `87492618d7bc8370029a3970f0ab6898dc8a3cff` — format/analyzer clean, but the same behavioral test failures remained.
- `32c901f94925ae660ebe36e90548f1d2e22a1611` — new compact tests passed and failures dropped from ten to four, but legacy Settings semantic tests still failed because unresolved choices were hidden.

Only `e41cea5fc7bccb4bbe085b48cd15ea5a2fead082` is the verified Slice 30 runtime.

## Remaining external evidence

CI does not prove:

- human phone usability or visual approval;
- SharedPreferences behavior on target production devices;
- store compliance/signing/review;
- production provider delivery;
- deployed production SLO/load/observability;
- operator-validated rollback controls.
