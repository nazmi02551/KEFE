# ADR-0033 — Production Mobile Access to My KEFE

- Status: Accepted
- Date: 2026-07-30
- Extends: ADR-0012, ADR-0030, ADR-0032

## Context

ADR-0032 and merged PRs #84/#85 made My KEFE a real repository-driven, actor-scoped decision-journey surface. The Product Preview exposes that surface through its five-destination shell, and the production API now returns the additive OpenAPI 0.17 `journey` member.

The production Flutter router still exposes only onboarding, Explore and Case routes. Therefore the production user cannot intentionally open the already-implemented My KEFE surface even though the shared screen and HTTP repository exist.

The next slice should close that access gap without pretending that preview-only Radar, Atlas or Weigh-hub data is production-ready and without prematurely replacing the production navigation model with demo destinations.

## Decision

### 1. My KEFE becomes an explicit production route

The production mobile router adds `/my-kefe` and renders the shared `MyKefeJourneyScreen` through the existing production `ProgressRepository`.

No preview repository, deterministic preview data or preview fallback may be imported by the production entrypoint.

### 2. Explore provides the first production entry point

The production `/explore` route owns an accessible My KEFE action that navigates to `/my-kefe` while reusing `ExploreScreen` in embedded mode.

The Product Preview continues to use its existing five-destination shell and does not render this additional production action.

### 3. No fake production shell

This slice does not expose Radar, Atlas or the preview Weigh hub in production. A full production bottom-navigation shell requires those destinations to have real production contracts or explicit capability gating and will be decided separately.

### 4. Guest continuity remains valid

My KEFE remains actor-scoped and may describe the current guest actor's recorded history. This slice does not force account creation and does not change the post-Reveal account-offer rules.

### 5. Existing safety boundaries remain binding

The production My KEFE route continues to show observed history only. It must not expose raw responses, private reasons, DecisionDelta payloads, Exposure/Intervention metadata, personality, ideology, psychometric inference or causal claims.

### 6. Navigation and failure behavior are explicit

- My KEFE supports normal back navigation to the previous production destination.
- Loading, retryable error, empty and populated states remain owned by the shared My KEFE screen.
- API failure must not substitute preview data.
- Existing onboarding, Explore and Case routes remain backward compatible.

## First implementation slice

1. add `/my-kefe` to `KefeApp`;
2. add an accessible production-only My KEFE action to the `/explore` route;
3. render `MyKefeJourneyScreen` with a production app bar/back affordance;
4. add widget tests proving production navigation and preview isolation;
5. keep the Product Preview five-destination shell unchanged;
6. add build identity to the Product Preview profile footer so phone testers can distinguish APK revisions without changing production behavior.

## Deferred

- full production five-destination navigation shell;
- production Radar/Atlas contracts;
- account enrollment or guest-to-account conversion;
- cross-user comparison or recommendation targeting;
- push-notification center behavior;
- release signing, AAB or Play Store distribution.

## Consequences

- The already-real My KEFE read model becomes reachable in the production mobile application.
- The production app does not expose preview-only destinations as if they were live.
- Product Preview and production continue to share the same My KEFE screen and repository abstraction while preserving strict data-source isolation.
- A future full production shell remains an explicit product decision rather than an accidental copy of the preview shell.
