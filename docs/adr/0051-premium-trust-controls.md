# ADR-0051 — Premium trust & controls visual slice 13

- Status: Accepted
- Date: 2026-07-31
- Issue: #121
- Stack base: PR #120 cleanup/status head `86c88ddfbe3fe60ced5a17655d1ce0a8bc2c3761`
- Inherited verified Slice 12 runtime: `b4f1e5405e022132618c5cc142172c0290b5c3c0`
- Extends: ADR-0038, ADR-0039, ADR-0045, ADR-0050

## Context

After the shared-shell convergence, Settings, Privacy and Account conversion are the clearest remaining behaviorally mature but visually generic trust/control surfaces.

The audit shows that product semantics are already established:

- Settings persists System/Türkçe/English locale selection and System/Light/Dark theme selection through `AppPreferencesController`.
- Settings privacy navigation already routes to `/privacy` when the privacy entry is presented.
- Privacy export/delete behavior is owned by `PrivacyController`; delete requires the existing `DELETE` confirmation phrase and successful deletion navigates to `/welcome`.
- Privacy is feature-gated by `privacyExperienceEnabledProvider`; this slice must not enable it where it is currently disabled.
- Account conversion remains optional and is controlled by the existing EMAIL/SMS → OTP → verify/merge state machine. Guest continuation must remain available.
- No production OTP/provider readiness is established by these presentation surfaces.

Public Share/deep-link presentation is a separate Blind First acquisition journey and is intentionally deferred.

## Decision

1. Settings, Privacy and Account conversion will converge onto existing `KefeVisualTheme` + `KefeSurface` semantic presentation primitives.
2. Existing localized copy is authoritative. This slice adds no new product semantics and should avoid new user-facing copy where existing strings express the state/action.
3. Settings preserves the exact `AppLocalePreference` and `AppThemePreference` values, persistence calls and route to `/privacy`.
4. Preference selection remains immediately interactive; presentation may group choices into premium semantic surfaces but must not add confirmation or hidden state.
5. Privacy preserves `privacyExperienceEnabledProvider` gating. Disabled privacy stays hidden/disabled exactly as before; presentation work cannot silently activate it.
6. Privacy export preserves the machine-readable JSON clipboard behavior and existing success dialog copy.
7. Privacy deletion preserves the `privacy-delete`, `privacy-delete-confirmation` keys, exact `DELETE` typed confirmation rule, controller call and successful `/welcome` navigation.
8. Account conversion preserves every existing `AccountUiState`, channel values `EMAIL`/`SMS`, controller calls, input semantics, existing widget keys, OTP length behavior, complete-state history messaging and guest escape path.
9. Account remains optional. Premium treatment must not imply that conversion is required, verified, production-ready or provider-backed beyond the existing runtime state.
10. Error/loading/working treatment may become visually clearer but must remain descriptive of existing state only and deterministic for test settlement; no continuous decorative motion is authorized.
11. Light/dark parity, TR/EN rendering, text scaling, screen-reader semantics and accessible tap targets are required.
12. Commit First, Blind First, immutable CaseVersion, generic runtime, preview/production isolation and My KEFE observed/descriptive-only boundaries remain untouched.

## Visual direction

- trust/control pages use theme-adaptive raised/sunken KEFE surfaces rather than bare generic lists/cards;
- locale/theme options remain familiar radio controls but gain coherent grouped hierarchy and selection affordance;
- privacy export and destructive delete are visually separated by intent, with destructive styling restrained and explicit;
- account entry/code/complete/error states read as one trustworthy conversion journey with clear state hierarchy;
- gold remains the KEFE primary accent; destructive privacy actions may use semantic error color only where Material theme already defines it;
- no dark-only fixed surface dependencies in governed Slice 13 presentation files.

## Acceptance

One exact candidate SHA must prove:

- Settings renders in TR/EN and light/dark without overflow, keeps all locale/theme values and privacy route behavior;
- Privacy feature-gate behavior is preserved and the enabled surface keeps export/delete/confirmation keys and semantics;
- Account entry/code/complete/error/guest presentation preserves existing keys, channels and controller/state boundaries;
- governed Slice 13 presentation uses KEFE semantic surfaces and does not depend on direct `KefeColorTokens.surfaceDark`, `borderDark` or `textMutedDark` values;
- no provider/production OTP claim is introduced;
- no new hardcoded user-facing production copy is introduced outside already-authorized literals such as the exact `DELETE` confirmation token;
- existing production copy boundary, phone acceptance, Commit First/Blind First and privacy/account regressions stay green;
- API CI, Mobile CI, MVP Beta Gates and Global Readiness succeed on the same candidate SHA.

## Out of scope

Authentication backend/provider changes, OTP deliverability, preference schema changes, new supported locales, route architecture changes, Public Share/community redesign, user profiling/inference, Signal/Impact, production/store readiness, deployed SLO evidence and human usability claims are not authorized by this ADR.
