# ADR-0038 — Internal Alpha localization boundary and phone acceptance

- Status: Accepted
- Date: 2026-07-30
- Tracks: Issue #96
- Extends: ADR-0034, ADR-0036, ADR-0037
- Base checkpoint: PR #95 exact-head `135b781a0fe3e9ff059d130acccd913304623f2b`

## Context

KEFE now has an exact-head verified MVP/global-readiness checkpoint, persistent System/Türkçe/English locale preference, persistent System/Light/Dark theme preference, and locale/country-aware content metadata. The remaining productization gap is that several production presentation files still contain user-facing TR/EN literals and direct locale branching. That makes translation coverage difficult to audit, encourages duplicated wording, and weakens future locale expansion.

A phone-test candidate also needs a repeatable repository-owned acceptance path without pretending that CI is human usability evidence.

## Decision

### 1. Production copy has one localization boundary

Production mobile presentation code must not own translated user-facing copy. Screens consume `KefeStrings` or feature string catalogs. Production screens may keep only technical literals such as route names, stable keys, enum/error codes, protocol confirmation tokens, interpolation separators and the KEFE brand.

Direct `locale.languageCode == 'tr'` / ternary translation branches are forbidden in production presentation code once this ADR is enforced.

Product Preview fixture *content* remains deterministic fixture data and may be localized separately; it is never a production fallback. Preview UI chrome should reuse the same localization boundary where practical.

### 2. Locale and theme preference remain user-owned

- Locale preference remains `system`, `tr`, or `en` for this checkpoint.
- Theme preference remains `system`, `light`, or `dark`.
- Preferences persist locally and are shared by production and Product Preview shells.
- Unsupported device locales fall back through Flutter's supported-locale resolution; screens do not invent their own locale fallback logic.

Adding a future locale must not require changing production screen business logic.

### 3. Internal phone acceptance is repository-owned evidence only

CI must cover the deterministic phone acceptance journey:

1. app launch and primary navigation;
2. locale preference switch and persistence;
3. theme switch and persistence;
4. Explore search/filter/save continuity;
5. Weigh → Commit → Reveal;
6. Activity/My KEFE continuity;
7. privacy/settings entry;
8. Share deep-link landing while preserving Blind/Commit First.

This is automated regression evidence, not human usability approval.

### 4. Existing invariants remain unchanged

- Commit First / Blind First remain global.
- CaseVersion remains immutable and case-agnostic.
- Product Preview fixtures never become production fallback.
- My KEFE remains observed/descriptive product history only.
- Consensus remains descriptive WE; Signal and Impact remain outside this slice.
- No fake provider, store, editorial, production SLO or human-usability PASS may be claimed.

## Acceptance gate

The Internal Alpha code checkpoint requires, on one exact stacked head:

1. executable copy-boundary contract passes with zero production user-facing hardcode violations;
2. Flutter format/analyze/all tests pass;
3. deterministic phone-acceptance test passes in TR and EN plus theme persistence coverage;
4. API CI, Mobile CI, MVP Beta Gates and Global Readiness remain green;
5. the internal phone APK artifact is tied to that exact head and clearly identified as Product Preview/internal, not production/store ready.
