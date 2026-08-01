# Premium Explore Discovery — Slice 22 Repo-Verified Status

Date: 2026-08-01  
Tracker: #146  
Pull request: #147  
Stack parent: PR #145 / `feature/sports-call-scene-slice21`

## Verified runtime

`0891ed8a96e2f0c5bc2666e07f9f7e549e5af067`

All required workflows completed successfully on that exact runtime SHA:

- API CI #912 — run `30688162655` — SUCCESS
- Mobile CI #706 — run `30688162658` — SUCCESS
- MVP Beta Gates #416 — run `30688162656` — SUCCESS
- Global Readiness #318 — run `30688162654` — SUCCESS

Later documentation-only commits do not redefine the verified runtime.

## Contract-first boundary

- ADR-0060: `docs/adr/0060-premium-explore-discovery-convergence.md`
- executable contract: `docs/contracts/premium-explore-discovery-slice22.v1.json`

Slice 22 is presentation-only convergence for the existing primary Explore discovery journey. It does not change the repository/controller, filter algorithm, item order, saved-case model, route map, backend/API/schema, CaseVersion, media exposure or Signal/Impact boundaries.

## Delivered

The governed Explore presentation now:

- uses shared theme-adaptive `KefeSurface` roles for discovery controls, featured Case, regular Cases and state surfaces;
- removes residual generic Material `Card` use from the governed screen;
- removes direct dark-only token dependencies and the screen-local fixed RGB featured gradient;
- preserves repository order and keeps the existing first item featured without introducing recommendation, ranking, popularity, personalization or editorial-priority semantics;
- preserves title/summary substring search, exact domain filtering, saved-only filtering and clear-all behavior;
- preserves all established Explore/search/filter/save/no-result keys;
- preserves SavedCasesController persistence and Activity continuity;
- preserves canonical `/case/:caseId` navigation while the nested save action remains local and does not trigger Case navigation;
- replaces initial indeterminate loading with deterministic semantic status treatment;
- distinguishes repository-empty, filtered no-result, error/retry and more-coming states;
- uses responsive header/section/filter layout for narrow phone and enlarged text;
- preserves Case media alt text, attribution, exposure and provider isolation;
- introduces no continuous decorative animation, WebView, Three.js or mandatory live 3D.

## Executable verification

The Slice 22 test/CI set covers:

- executable contract truth and invariant guards;
- semantic-surface source guard with no direct dark tokens, fixed local gradient or generic Material Card return/child usage;
- repository-order and first-featured continuity without percentage/ranking UI;
- nested save action persistence without Case navigation;
- deterministic loading, repository-empty and error states with independent Riverpod fixture containers;
- existing discovery search/domain/saved/clear and Activity continuity regressions;
- canonical Case navigation;
- dark/light, 360×800 and 1.6× text-scale layout;
- production-copy boundary;
- full mobile regressions and phone acceptance;
- API contracts, generic runtime and PostgreSQL continuity.

## Rejected or corrected candidates

No PASS claim attaches to the following earlier heads:

- `e4816594b49ec95b2a117237a357645d7183c737` — canonical Dart format gate failed;
- `622ac1fbd741a0bfda3f34ff2395ed39640cdccc` / formatter follow-up — temporary branch-scoped formatting automation only, not a release candidate;
- `b4c24f9022e5f5304f882e8529020b54008089bc` — formatter/analyzer passed, but state-fixture test reused the previous Riverpod container and failed the repository-empty assertion.

The temporary formatter workflow was removed before the verified runtime. The final solution fixed the test harness by recreating the provider container for each fixture; no production gate was weakened.

## Internal phone artifact

Global Readiness #318 produced:

- artifact: `kefe-internal-alpha-phone-preview`
- artifact ID: `8814744443`
- archive digest: `sha256:42b641f63e425e6e4851e89937fcb0f6826b180bc317fc904d8fe0fe86cca189`
- payload: `app-debug.apk`
- APK size: `160567650` bytes
- APK SHA-256: `feebeb1b1a4294c8eaa47f40bf9e3cfae87bced0cc33b0eff753c40f5018c2d3`
- `beta-api.invalid`: absent in raw and unpacked APK scans.

This is an isolated Product Preview/internal phone-test artifact. Preview fixtures are not production fallback. It is not production, public-beta, store-release or human-usability evidence.

## Governance

PR #147 remains draft and stacked on PR #145. No merge is performed by this checkpoint. This status document belongs to the WORKING branch stack and does not supersede the canonical CURRENT documentation baseline.
