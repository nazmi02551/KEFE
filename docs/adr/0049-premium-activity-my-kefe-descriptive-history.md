# ADR-0049 — Premium Activity + My KEFE descriptive history visual slice 11

- Status: Accepted
- Date: 2026-07-31
- Stack base: PR #117 status head `32c06b352b32709927b322b392fabf5b2edd7a36`
- Inherited verified localization runtime: `16d1f731e0ab7791e246e522afc55fdca16a5058`
- Extends: ADR-0032, ADR-0033, ADR-0039

## Context

The current Decision, Reveal, Perspective, Radar and Atlas surfaces use the theme-adaptive semantic KEFE visual system, while Activity, My KEFE Journey and the reusable Progress section still contain older generic Material presentation and direct dark-only visual tokens.

The real current code shows:

- `ActivityScreen`: generic `Card`, direct `KefeColorTokens.textMutedDark`, fixed translucent avatar colors, generic Chips and Dividers.
- `MyKefeJourneyScreen`: manually authored fixed dark gradient, `surfaceDark` / `textMutedDark` dependencies, generic Cards, Chips and `LinearProgressIndicator`.
- `ProgressSection`: generic Cards and outlined metric containers that do not share the premium surface taxonomy.

These screens are product-valid. This ADR authorizes visual convergence only; it does not authorize new product interpretation or new history metrics.

## Decision

1. Activity, My KEFE Journey and Progress/account-offer presentation will migrate to shared theme-adaptive `KefeSurface`, `KefeVisualTheme` and semantic KEFE roles.
2. Existing data models, controller behavior, navigation destinations, public keys and loading/error/retry semantics remain unchanged.
3. My KEFE remains an observed/descriptive history read model. Presentation must not infer personality, ideology, psychometrics, bias, morality, intent, preference profile or causality.
4. Existing counts, domains, journey updates and reflection completion states may be given stronger hierarchy, but no new score, rank, normative interpretation or derived metric may be invented.
5. Preview-only data remains clearly identified as Product Preview sample data. Preview fixtures must never become production fallback.
6. Light and dark themes use semantic surface/foreground roles; governed screens must not reintroduce direct dark-only presentation tokens.
7. Motion is optional and must collapse under Reduce Motion. This slice does not require continuous animation.
8. Screen-reader semantics and text-first comprehension remain primary. Decorative treatment carries no data meaning by itself.
9. Renderer/presentation failure must not alter or block the underlying navigation/history/product flow beyond ordinary Flutter rendering failure handling.
10. Existing localization boundaries remain unchanged and all new user-facing copy, if any is required, must pass through governed localization resources.

## Visual direction

- premium dark-first KEFE identity with valid light-theme parity;
- gold for brand/history emphasis;
- cyan/blue for factual/history structure where useful;
- coral/gold only as non-normative supporting accents;
- stronger section hierarchy and compact semantic metric surfaces;
- history rows should feel like navigable journey records, not generic list tiles;
- methodology/non-inference notes should be visually distinct from primary content without appearing like warnings or scores.

## Acceptance

One exact runtime SHA must prove:

- Activity, My KEFE Journey and Progress surfaces render in TR/EN and light/dark without overflow or contrast regressions;
- existing keys/navigation/controller semantics remain green;
- progress/journey values are unchanged from supplied read models;
- preview truthfulness notice remains visible for deterministic preview data;
- non-inference note remains present;
- governed screens do not use direct dark-only `KefeColorTokens.surfaceDark`, `borderDark` or `textMutedDark` presentation dependencies;
- no new user-facing hardcoded copy is introduced;
- existing production My KEFE access, Progress, discovery continuity and phone acceptance tests remain green;
- API CI, Mobile CI, MVP Beta Gates and Global Readiness succeed on the same candidate SHA.

## Out of scope

Backend/read-model changes, new analytics metrics, scoring, profiling/inference, Signal/Impact, advanced behavioral visualization, production/store readiness and deployed SLO evidence are not authorized by this ADR.
