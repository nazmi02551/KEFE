# ADR-0043 — Premium Atlas Preview and governed localization slice 5

- Status: Accepted
- Date: 2026-07-30
- Tracks: Issue #106
- Extends: ADR-0030, ADR-0039, ADR-0042
- Stack base: PR #105 status head `dfa4c4d74f4cde28cad02a7b1f4c1981eade7a5a`
- Inherited repo-verified Radar runtime: `e1da8aeeff1cad6de60849a6d8d5b9cf834cb19f`

## Context

Atlas is a valid supporting Product Preview capability but still presents representative values through hardcoded Turkish copy, direct dark tokens, a placeholder-like hero and generic country cards. The existing values are explicitly representative and must not be upgraded into stronger claims merely because presentation becomes more mature.

## Decision

1. Atlas remains Product Preview-only representative data. Existing country averages and selected Case id are preserved exactly. No production country analytics, live updates, samples, inferred location or geography engine are introduced.
2. The existing 0–10 value is presented as a KEFE continuum from Rules/Rights to Empathy/Compassion. No percentage split or additional statistic is derived from the value.
3. Atlas fixture structure is separated from presentation: selected Case id/fallback title plus stable country codes and existing average values.
4. Atlas chrome and country names use a locale-keyed additive resource catalog. Selected Case title uses `KefeContentLocalizer`. Direct locale branching in presentation is forbidden.
5. Hero, scale and country cards use semantic `KefeVisualTheme` / `KefeSurface` roles. Decorative world treatment may use static lightweight Flutter `CustomPainter`; it carries no data and is excluded from accessibility semantics.
6. Country cards show only the existing average and its position on the 0–10 continuum. Visual interpolation does not create a new metric.
7. Atlas remains a supporting capability and does not become a primary product mode. Preview/production isolation remains intact.

## Acceptance

One exact runtime head must prove:
- representative/not-live truthfulness remains visible;
- existing country values and Case id are unchanged;
- no invented split/sample/update/geolocation claims;
- TR/EN Atlas rendering works in light/dark themes;
- presentation has no direct locale branching or direct dark-only tokens;
- selected Case content goes through the content-localization boundary;
- Product Preview navigation and existing runtime regressions remain green;
- API CI, Mobile CI, MVP Beta Gates and Global Readiness all succeed on that same SHA.
