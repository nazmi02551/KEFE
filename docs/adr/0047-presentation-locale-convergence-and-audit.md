# ADR-0047 — Presentation locale convergence and localization audit slice 9

- Status: Accepted
- Date: 2026-07-30
- Tracks: Issue #114 under #108
- Extends: ADR-0044, ADR-0045, ADR-0046
- Stack base: PR #113 status head `b00b85ac10d7a00cc2ba25e8c89b881bd897cc33`
- Inherited verified core runtime: `f99fece4188261c1cb8a7d83d85c9103c871b556`

## Context

The shared `KefeLocaleCatalog` architecture now governs Progress/My KEFE, Internal Alpha and core `KefeStrings`. A post-migration audit still finds two legacy direct language branches in Settings and Explore presentation strings. Radar and Atlas already have additive TR/EN catalogs and English fallback but use feature-local lookup logic rather than the shared resolver.

`PreviewContentLocalizer` serves a different purpose: display-time localization of representative preview content using the original content as fallback. It is not presentation chrome and remains outside this convergence.

## Decision

1. Move Settings and Explore presentation copy into feature-owned locale resource catalogs resolved through `KefeLocaleCatalog`.
2. Preserve every existing public Settings/Explore extension getter/method signature and exact current TR/EN output, domain aliases and count wording.
3. Keep Radar and Atlas feature-owned catalogs, but route locale selection, fallback and key resolution through `KefeLocaleCatalog`.
4. Preserve Radar/Atlas public string APIs, Product Preview truthfulness, representative data and navigation semantics.
5. English remains the deterministic fallback resource language; no unknown locale becomes supported.
6. Turkish and English remain the only declared supported app locales.
7. Add an explicit source audit covering the governed presentation-localization files; do not infer repo-wide completion from migration count alone.
8. `PreviewContentLocalizer` remains outside this source audit because it is a content-localization seam, not presentation copy selection.
9. No product logic, API behavior, persistence, CaseVersion, Commit/Blind First, Signal/Impact, inference or visual redesign is authorized.

## Acceptance

One exact runtime head must prove:

- Settings and Explore TR/EN catalog parity and English fallback;
- Settings/Explore current behavior unchanged;
- Radar/Atlas catalog parity, fallback and current behavior unchanged;
- governed presentation source files contain no direct locale-based TR/EN copy branching or private locale-selection helpers;
- core KefeStrings, Internal Alpha, Progress/My KEFE, Settings, Explore, Radar and Atlas all consume the shared resolver boundary;
- app supported locales remain Turkish and English only;
- existing localization, Product Preview, accessibility/theme, navigation and mobile regression tests remain green;
- production copy boundary and phone acceptance remain green;
- API CI, Mobile CI, MVP Beta Gates and Global Readiness all succeed on the same SHA.
