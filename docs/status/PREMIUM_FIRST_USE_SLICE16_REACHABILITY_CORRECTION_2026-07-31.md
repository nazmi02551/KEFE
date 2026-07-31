# KEFE Premium First-Use Slice 16 — Phone Preview Reachability Correction

Date: 2026-07-31
Status: REPO_VERIFIED / HUMAN_PHONE_USABILITY_PENDING
Tracks: Issue #127 / PR #128 / ADR-0054 / `premium-first-use-slice16.v2.json`

## Why this correction exists

The earlier Slice 16 runtime `86b75bb621b866770371f34500a2fc7148bac484` correctly implemented and tested the premium first-use presentation in the production `KefeApp`, but the distributed `kefe-internal-alpha-phone-preview` artifact is composed through `main_preview.dart` / `ProductPreviewApp`. That preview app intentionally opened at `/explore` and did not expose `/welcome`, so the redesigned onboarding was not reachable from the actual phone-preview APK. Clearing application data could not fix that routing fact.

The earlier CI evidence remains valid for the code it exercised, but `86b75bb...` is superseded as the human first-use visual-review checkpoint.

## Corrected verified runtime

Pinned runtime SHA:

`68b390584901dc706059485afb6f29d7f073defc`

All required repo-owned workflows succeeded on this exact SHA:

- API CI #821 / run `30642405804` — SUCCESS
- Mobile CI #623 / run `30642406123` — SUCCESS
- MVP Beta Gates #325 / run `30642405824` — SUCCESS
- Global Readiness #235 / run `30642405813` — SUCCESS

Subsequent documentation-only commits do not redefine this runtime SHA.

## Reachability correction

- Production `main.dart`, `KefeApp` initial `/welcome` behavior and persisted onboarding semantics are unchanged.
- Product Preview still opens normally at `/explore`.
- Product Preview now exposes `/welcome?review=1` using the same `OnboardingGateScreen` in explicit review mode.
- Explore exposes the preview-only `open-preview-first-use` action so first-use presentation can be replayed without clearing app data.
- Review mode bypasses only the persisted-completion read; it does not add or reorder onboarding promises.
- `main_preview.dart` owns an in-memory onboarding store so preview review activity cannot mutate production/shared onboarding persistence.
- Product Preview Case routing now preserves the existing `firstUse=1` query so the first-Reveal completion surface is reachable from the review journey.
- Preview secondary actions were kept in a horizontal group after a rejected candidate showed that a third vertically stacked action could occlude Explore save controls.

## Regression evidence

The exact runtime includes executable coverage proving:

- the v2 contract preserves two onboarding promises and all core product invariants;
- TR/EN × light/dark premium onboarding remains valid;
- review mode renders even when the supplied onboarding store reports `completed=true` and does not read or write that completion store during the review gate;
- Product Preview Explore exposes `open-preview-first-use`;
- tapping the preview first-use action reaches promise 1, then promise 2, then the existing demo Case with Reveal still hidden pre-Commit;
- existing Explore save continuity, Activity continuation, decision flow, accessibility/locale/theme regressions and phone acceptance remain green;
- production entrypoint does not import or use the preview in-memory onboarding store.

## Rejected correction candidate

`360c8c45b91b83d5c9936308cca40d38dde54e92` is NOT a verified checkpoint.

It failed because:

1. two new test files had canonical Dart format drift; and
2. the initial vertical three-action Product Preview tool stack overlapped Explore Case save hit areas, causing existing save-continuity regressions to fail.

Both issues were corrected before the pinned runtime.

## Corrected phone artifact

- artifact: `kefe-internal-alpha-phone-preview`
- artifact ID: `8798145837`
- artifact archive digest: `sha256:da667b71de223b23a9faf16b2cca66317613455636629ba72d65f2c9f9b3c4b9`
- payload: `app-debug.apk`
- APK size: `160503874` bytes
- APK SHA-256: `3b056e860e92bb871c405f0729b14c6914a330db89933f3b1e8085a8d1cada77`
- `beta-api.invalid`: ABSENT in raw APK and unpacked APK scans.

This is an isolated Product Preview/internal phone-test artifact, not a production/store release.

## How to review on phone

The Product Preview intentionally still opens on Explore. Use the new first-use preview action (`open-preview-first-use`, visually the sparkle/first-use action in the preview tool group) to open the premium onboarding. No application-data clearing is required. Complete the two promise pages to enter the existing demo Case; after the first Reveal, the premium first-use completion surface is part of the same review journey.

## Non-claims

No human real-device usability PASS is claimed by CI. No production OTP/provider, editorial CQB, store compliance, deployed SLO/load/observability or operator rollback evidence is claimed. No Signal/Impact expansion or profile/inference behavior is introduced.
