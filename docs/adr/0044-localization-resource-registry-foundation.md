# ADR-0044 — Localization resource registry foundation and first feature migration

- Status: Accepted
- Date: 2026-07-30
- Tracks: Issue #108
- Stack base: PR #107 status head `5e3db35870eb885d188e77249c3f8e145cb05a0e`
- Inherited verified Atlas runtime: `50d22ad336e42196b88579faaa9fb84c3615ffe8`

## Context

KEFE already centralizes much presentation copy behind `KefeStrings`, but its implementation and several feature extensions still encode Turkish/English selection through repeated boolean locale branches. Radar and Atlas now use locale-keyed catalogs, demonstrating a safer additive model for future locales.

A repo-wide one-shot rewrite of every copy getter would be unnecessarily risky. The migration therefore needs a shared resource resolver and incremental feature ownership while keeping current public string APIs and locale preference behavior stable.

## Decision

### 1. One shared locale-resource resolver

Introduce a core `KefeLocaleCatalog` boundary that resolves a string key from a locale-keyed resource table.

- English is the deterministic fallback locale for a missing/unsupported feature resource.
- Missing localized keys fall back to the English value.
- A missing English key degrades to the stable key rather than throwing and breaking the decision journey.
- Placeholder interpolation is deterministic and owned by the resolver.
- Locale inspection belongs only inside localization infrastructure, never in migrated presentation/feature string getters.

### 2. Resource ownership remains feature-oriented

Shared/core copy and feature copy do not have to live in one monolithic file. A feature may own a catalog so long as it uses the common resolver contract and obeys key-parity tests.

The first governed migration is Progress / My KEFE strings. Existing getter/method names remain intact so runtime screens/controllers do not need a broad rewrite.

### 3. Current supported locale claim remains TR/EN

This architecture makes another locale additive, but KEFE must not claim a language as supported until all required catalogs for the product surface are complete and the locale is deliberately added to the supported-locale registry.

Unknown locale resolution may fall back to English internally; that fallback is not equivalent to declaring the locale supported.

### 4. Catalog parity is executable

For every production catalog:

- English defines the canonical key set.
- every currently supported locale must provide the same required key set unless a contract explicitly marks an optional key;
- CI tests verify parity and deterministic fallback/interpolation;
- migrated string getter files must not contain `locale.languageCode`, `_isTurkish`, `_tr`, or direct locale-selection branches.

### 5. Preserve existing wording and behavior

This slice moves ownership only. It does not intentionally rewrite Turkish/English copy, plural semantics, product terminology, locale persistence, theme persistence, domain/runtime semantics or API content localization.

### 6. Migration remains incremental

This slice migrates `ProgressStrings` only. Core `KefeStrings` and `InternalAlphaStrings` remain known legacy implementations and are explicitly scheduled for follow-up stacked slices under Issue #108.

No PASS claim for repo-wide localization completion is allowed until those remaining catalogs are migrated and exact-head verified.

## Acceptance

Slice 6 requires one exact runtime head where:

1. the common locale resolver and Progress catalog exist;
2. Progress/My KEFE string getters contain no direct locale branching;
3. TR and EN Progress catalog key parity is tested;
4. unknown locale fallback and placeholder interpolation are tested;
5. existing Progress/My KEFE behavior tests remain green;
6. existing app locale/theme preference tests remain green;
7. production copy boundary remains green;
8. API CI, Mobile CI, MVP Beta Gates and Global Readiness all succeed on the same SHA.
