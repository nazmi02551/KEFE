# ADR-0050 — Premium shared navigation shell visual slice 12

- Status: Accepted
- Date: 2026-07-31
- Issue: #119
- Stack base: PR #118 cleanup head `63b2838b6695f5939639167d3b11d0dba2bbf1a0`
- Inherited verified Slice 11 runtime: `54aa984fda97a1adb1295bec8701543955568d61`
- Extends: ADR-0038, ADR-0039, ADR-0049

## Context

The core Decision/Reveal/Perspective/Radar/Atlas and Activity/My KEFE/Progress surfaces have converged onto the theme-adaptive KEFE visual system. Shared navigation chrome is now one of the clearest remaining cross-journey presentation inconsistencies.

Current code on the Slice 11 stack shows:

- `PrimaryNavigationShell` still draws a fixed `KefeColorTokens.borderDark` boundary around the canonical four-tab `NavigationBar`;
- Product Preview build identity still uses fixed `surfaceDark`, `goldSoft` and `textMutedDark` presentation tokens;
- production and Product Preview settings access FABs remain generic Material chrome;
- Product Preview Radar/Atlas secondary route wrapper uses a generic AppBar despite those preview surfaces already using premium KEFE treatment.

The navigation model itself is product-valid and must not change in this slice.

## Decision

1. The shared four-tab shell will use existing `KefeVisualTheme` semantic surface, border, foreground and gold roles rather than fixed dark-only tokens.
2. The canonical tab order and routes remain exactly `Explore`, `Weigh`, `Activity`, `My KEFE` mapped to `/explore`, `/weigh`, `/activity`, `/my-kefe`.
3. `selectedIndex`, `onDestinationSelected`, existing `ValueKey('primary-navigation')`, route ownership and go/push semantics remain unchanged.
4. Radar and Atlas remain Product Preview secondary destinations. They must not become primary tabs or imply production availability.
5. Product Preview build identity continues to render `PreviewBuildInfo.label` truthfully and must remain visually separate from production chrome without relying on fixed dark-only styling.
6. Production and Product Preview settings access retain their existing keys and navigation destination. This slice may improve their visual treatment only.
7. Product Preview Radar/Atlas secondary route chrome may converge to semantic KEFE navigation styling while preserving back behavior and titles.
8. No new user-facing copy is authorized. Existing localized primary navigation/settings labels and existing preview proper names are reused.
9. Light/dark parity, text scaling, screen-reader semantics and accessible tap targets are required. This slice adds no continuous animation.
10. Presentation failure must not alter navigation semantics or product state.

## Visual direction

- theme-adaptive raised navigation dock using semantic KEFE surfaces and borders;
- restrained gold selected-state emphasis inherited from the shared theme;
- visually quiet unselected navigation chrome;
- semantic preview identity surface that remains recognizable in both themes;
- settings access treated as part of the premium shell without competing with primary actions;
- secondary preview route chrome visually consistent with the KEFE system but clearly secondary to the four-tab shell.

## Acceptance

One exact candidate SHA must prove:

- production and Product Preview four-tab shells render in TR/EN and light/dark without overflow;
- exactly four canonical `NavigationDestination` widgets remain present on primary shell routes;
- tab selection still navigates to the same route destinations;
- production `open-settings` and preview `open-preview-settings` keys still navigate to `/settings`;
- `preview-build-identity` still renders `PreviewBuildInfo.label` and remains preview-only;
- Radar/Atlas remain secondary and primary navigation is absent on their secondary route pages;
- governed shell code does not use direct `KefeColorTokens.surfaceDark`, `borderDark` or `textMutedDark` presentation dependencies;
- no new hardcoded user-facing product copy is introduced;
- existing Commit First, Blind First, CaseVersion, preview isolation, My KEFE no-inference, phone acceptance and production copy-boundary tests remain green;
- API CI, Mobile CI, MVP Beta Gates and Global Readiness succeed on the same candidate SHA.

## Out of scope

Route architecture changes, new tabs, backend/read-model work, CaseVersion changes, new product modes, personalization/profiling/inference, Signal/Impact, production/store readiness, deployed SLO evidence and human usability claims are not authorized by this ADR.
