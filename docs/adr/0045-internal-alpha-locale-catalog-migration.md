# ADR-0045 — Internal Alpha locale catalog migration slice 7

- Status: Accepted
- Date: 2026-07-30
- Tracks: Issue #110 under #108
- Extends: ADR-0044
- Stack base: PR #109 status head `7aeeba5ec91ac10552c907af6a652948fa236a68`
- Inherited verified localization runtime: `f6f2f7839cc3f1260ae3c8fd788edb155cf54738`

## Context

Slice 6 established `KefeLocaleCatalog` and migrated Progress/My KEFE copy. The next concentrated legacy area is `InternalAlphaStrings`, which owns navigation, account conversion, Activity, Weigh hub, privacy, sharing, community reasons, consensus and several Decision/Reveal presentation labels. It still branches directly on `locale.languageCode == 'tr'` through `_iaTr`.

The larger core `KefeStrings` class remains separate and must not be coupled into this migration.

## Decision

1. Move all current Internal Alpha TR/EN user-facing copy into `InternalAlphaStringCatalog`, resolved through `KefeLocaleCatalog`.
2. Preserve every existing public getter/method name and return wording for supported Turkish and English callers.
3. Preserve semantic branching that is not locale selection, including count singular/plural selection, known code-to-label mapping and unknown-code fallback formatting.
4. Dynamic values such as destination, error code, limit, sample values and percentages use centralized placeholder interpolation where applicable.
5. `internal_alpha_strings.dart` must contain no direct `locale.languageCode`, `_iaTr`, Turkish-vs-English conditional literal selection or locale switch.
6. English defines catalog key parity; Turkish must provide the same required keys.
7. Unknown locale resolution falls back to English but does not declare that locale supported.
8. Core `KefeStrings` migration remains deferred to a separate stacked slice.
9. No product logic, persistence, API content, CaseVersion, inference, Signal/Impact or visual semantics change is authorized.

## Acceptance

One exact runtime head must prove:

- full TR/EN Internal Alpha catalog key parity;
- current representative TR/EN getter/method behavior remains unchanged;
- unknown locale fallback is deterministic;
- dynamic placeholders and unknown-code fallbacks remain correct;
- `internal_alpha_strings.dart` has no direct locale branching;
- existing navigation/account/activity/weigh/privacy/share/community/consensus/reveal tests remain green;
- locale/theme preference regressions and production copy boundary remain green;
- API CI, Mobile CI, MVP Beta Gates and Global Readiness all succeed on that same SHA.
