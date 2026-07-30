# ADR-0046 — Core KefeStrings locale catalog migration slice 8

- Status: Accepted
- Date: 2026-07-30
- Tracks: Issue #112 under #108
- Extends: ADR-0044 and ADR-0045
- Stack base: PR #111 status head `086a3a3a4ecc131d98edf68a1936d5528b79c480`
- Inherited verified Internal Alpha runtime: `c1921c8267dfe39ccaf4b5df2f8530fddb205b8b`

## Context

Slice 6 established the shared locale resolver and migrated Progress/My KEFE. Slice 7 migrated `InternalAlphaStrings`. The remaining concentrated localization debt is the core `KefeStrings` class, which still selects Turkish versus English user copy through `_tr` and direct locale branching.

This class is also the public localization surface consumed by production/mobile presentation, so the migration must preserve its constructor, `of(context)`, `supportedLocales`, delegate behavior and all public getter/method signatures.

## Decision

1. Move all current core Turkish/English user-facing copy from `KefeStrings` into `CoreStringCatalog`, resolved through `KefeLocaleCatalog`.
2. Preserve every current public getter/method name and supported Turkish/English return wording.
3. Preserve `KefeStrings(this.locale)`, `KefeStrings.of(context)`, `supportedLocales` and `KefeStringsDelegate` behavior.
4. Preserve semantic branching that is not language selection, including claim/source/reason/status/flow/error mappings, reflection state, PerspectiveSlot mapping and unknown-code fallbacks.
5. Dynamic counts, limits and other values use catalog placeholder interpolation while retaining current output exactly.
6. `kefe_strings.dart` must contain no `_tr` helper or direct locale-based Turkish/English copy selection after migration.
7. English remains the deterministic fallback resource language; fallback does not make an unknown locale supported.
8. Turkish and English remain the only declared supported app locales in this slice.
9. No product logic, API behavior, persistence, CaseVersion, Commit/Blind First, Signal/Impact, inference or visual semantics change is authorized.

## Acceptance

One exact runtime head must prove:

- exact TR/EN core catalog key parity;
- representative current getter/method behavior unchanged in Turkish and English;
- deterministic unknown-locale English fallback;
- dynamic placeholder behavior and enum/code/unknown fallbacks preserved;
- `kefe_strings.dart` contains no `_tr` or direct locale copy branching;
- `supportedLocales` and delegate support remain exactly Turkish and English;
- existing onboarding/context/decision/offline/reflection/flow/perspective/error regressions remain green;
- production copy boundary, locale/theme preferences and phone acceptance remain green;
- API CI, Mobile CI, MVP Beta Gates and Global Readiness all succeed on the same SHA.
