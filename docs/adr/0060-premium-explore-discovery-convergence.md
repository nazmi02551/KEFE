# ADR-0060 — Premium Explore Discovery Convergence

Date: 2026-08-01  
Status: Accepted for Slice 22 implementation  
Tracker: #146  
Stack parent: `feature/sports-call-scene-slice21`

## Context

The primary Explore tab is functionally complete and already provides the canonical discovery journey:

- repository-driven Case summaries in repository order;
- title/summary search;
- domain filters;
- saved-only filtering;
- device-local save/unsave continuity into Activity;
- canonical `/case/:caseId` navigation;
- representative Case media through the existing provider-neutral media seam.

The current Explore implementation predates the shared premium visual system used by later verified slices. It still contains residual generic Material `Card` surfaces, direct dark-only color tokens, a screen-local fixed gradient and indeterminate loading presentation. This creates inconsistent dark/light behavior and visual hierarchy across the primary navigation.

The issue is presentation debt, not a discovery-product or ranking problem.

## Decision

Slice 22 converges the existing Explore discovery journey onto shared theme-adaptive KEFE semantic surfaces and visual roles.

The slice is presentation-only. It does not change the repository, controller, filter algorithm, item order, saved-case model, navigation map, CaseVersion data or media exposure semantics.

### Generic discovery hierarchy

The Explore surface may distinguish only existing structural roles:

- screen identity/header;
- discovery controls;
- the existing first item as the featured Case;
- remaining items as regular Case rows;
- loading, error, empty, no-result and more-coming states.

The implementation must not branch on named Case ID, Case title, Case format or domain to select special visual composition. Domain icons/labels may continue to use the existing generic domain mapping.

The first item remains featured because the existing repository/order already makes it first. Slice 22 does not introduce recommendation, personalization, popularity, ranking score or editorial priority semantics.

### Search and filters

Existing behavior remains authoritative:

- search matches title or summary using the current normalized substring behavior;
- domain selection is exact and additive to the current search;
- saved-only is additive to search/domain filters;
- clear resets query, selected domain and saved-only state;
- no-result state remains distinct from repository-empty state;
- filter and search changes remain local presentation state.

No query analytics, targeting, personalization or new persistence is introduced.

### Saved Cases and navigation

Existing stable keys and actions remain unchanged:

- `explore-list`;
- `explore-search-field`;
- `domain-filter-all` and `domain-filter-<DOMAIN>`;
- `saved-only-filter`;
- `clear-explore-filters`;
- `explore-case-<CASE_ID>`;
- `save-case-<CASE_ID>`;
- `explore-no-results`.

Save/unsave continues through `SavedCasesController`. Tapping a Case continues to push the canonical `/case/:caseId` route. Save controls must not accidentally trigger Case navigation.

### Theme and surface system

The governed Explore source must use shared semantic KEFE roles/surfaces instead of direct dark-only tokens or screen-local hard-coded gradients.

Requirements:

- dark-first premium identity with valid light theme;
- shared `KefeSurface` tones for featured, raised and state surfaces;
- semantic foreground, muted, border, gold, rules/empathy accents through `KefeVisualTheme`;
- no direct `KefeColorTokens.*Dark` dependencies in governed Explore presentation;
- no direct fixed RGB gradient owned by the Explore screen;
- save, domain and navigation affordances remain visually distinct and accessible.

### Deterministic states and motion

Loading, empty, no-result, error and more-coming states use deterministic semantic treatment. Indeterminate continuous decorative loading is removed from the governed Explore surface.

Refresh remains the existing user-triggered `RefreshIndicator`; this slice does not alter refresh behavior.

Any state transition motion must use the existing Reduce-Motion-aware system or remain static. No idle continuous animation is introduced.

### Accessibility and responsive behavior

- Search/filter/save/Case navigation semantics remain explicit.
- Informative Case media keeps existing alt/provenance behavior.
- Decorative icons do not become duplicate semantic facts.
- Layout must avoid overflow on narrow phone widths and enlarged text.
- Featured and regular Case content must remain reachable in a scrollable list.
- Minimum touch targets remain compatible with Material accessibility expectations.

### Performance

Use standard Flutter widgets and existing bounded Case media composition. No WebView, Three.js, mandatory live 3D, remote decorative asset dependency or continuously repainting background is introduced.

## Preserved invariants

Slice 22 does not change:

- Commit First / Blind First;
- immutable CaseVersion;
- generic Flow/Case runtime;
- raw Case values or display localization boundaries;
- media exposure phase or evidence authority;
- preview/production isolation;
- My KEFE descriptive-only boundary;
- Signal/Impact scope;
- backend/API/schema/provider behavior;
- primary navigation or route architecture.

## Verification

Before PASS, one exact runtime SHA must pass:

- API CI;
- Mobile CI;
- MVP Beta Gates;
- Global Readiness.

Mobile verification must include:

- executable contract guard;
- existing search/domain/saved-only/clear behavior;
- saved-case continuity into Activity;
- canonical Case navigation;
- save action does not trigger Case navigation;
- stable key preservation;
- repository item order preserved and first item remains featured without new ranking semantics;
- deterministic loading/error/empty/no-result/more-coming presentation;
- no direct dark-only tokens or fixed screen-local gradient in governed Explore source;
- dark/light rendering;
- narrow-phone and enlarged-text overflow checks;
- production and Product Preview reachability;
- full existing mobile regressions, production-copy boundary and phone acceptance.

Human visual/usability review remains external evidence.
