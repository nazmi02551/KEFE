# ADR-0048 — Saved Cases localization residual and final presentation audit

- Status: Accepted
- Date: 2026-07-30
- Tracks: Issue #116 under #108
- Extends: ADR-0044 through ADR-0047
- Stack base: PR #115 status head `ca9d447aabe9af0de77b58a5dfd97966e07b58dd`
- Inherited verified convergence runtime: `fd8e1e152f9a90064510a2dc738fa9fb76ee66c9`

## Context

After Slice 9 converged Settings, Explore, Radar and Atlas, a repo-level source scan identified one remaining direct presentation locale branch in `features/saved_cases/presentation/saved_case_strings.dart`.

The same scan found three other language-code uses that are intentional boundaries rather than residual presentation branching: centralized `KefeLocaleCatalog` resource selection, `KefeStringsDelegate` support detection, and `PreviewContentLocalizer` display-time content fallback behavior.

## Decision

1. Move all current Saved Cases/Search/Filter Turkish and English copy into a feature-owned locale catalog resolved through shared `KefeLocaleCatalog`.
2. Preserve every current `SavedCaseStrings` getter signature and exact current TR/EN wording.
3. Remove `_savedCaseIsTurkish` and all direct locale-based copy selection from `saved_case_strings.dart`.
4. Preserve deterministic English resource fallback without declaring unknown locales supported.
5. Turkish and English remain the only declared app locales.
6. Add a final explicit presentation-source audit requiring no direct locale-copy branching outside the three intentional architecture/content boundaries documented above.
7. Branch-stack verification may establish technical readiness of the localization architecture, but parent issue #108 remains open until the stacked PRs are actually merged to main.
8. No product logic, API behavior, persistence, CaseVersion, Commit/Blind First, Signal/Impact, inference or visual semantics change is authorized.

## Acceptance

One exact runtime head must prove:

- Saved Cases TR/EN catalog parity;
- unknown-locale deterministic English fallback;
- current Saved Cases/Search/Filter copy unchanged;
- `saved_case_strings.dart` consumes shared resolver with no direct locale branch;
- repo-level audit finds only `KefeLocaleCatalog`, `KefeStringsDelegate`, and `PreviewContentLocalizer` as intentional direct language-code boundaries;
- supported app locales remain Turkish and English only;
- existing saved-case, Explore, Product Preview, accessibility/theme and mobile regressions remain green;
- production copy boundary and phone acceptance remain green;
- API CI, Mobile CI, MVP Beta Gates and Global Readiness all succeed on the same SHA.
