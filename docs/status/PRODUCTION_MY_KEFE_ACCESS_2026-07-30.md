# KEFE Production My KEFE Access Checkpoint — 2026-07-30

This checkpoint records ADR-0033 and the first runtime slice that makes the shared actor-scoped My KEFE journey reachable from the production Flutter router while keeping Product Preview data isolated.

## Baseline

- v7 Product Preview remains the verified phone-test baseline from PR #84.
- v7 Mobile CI run: `30488318184` — PASS.
- v7 artifact id: `8739080881`.
- v7 extracted APK sha256: `75e7ad87078d7c7c7474cae2bac492b4f2f21ca85513ea26898486e9363c6666`.

## ADR-0033

- production adds `/my-kefe` through the shared `MyKefeJourneyScreen` and existing `ProgressRepository`;
- production Explore exposes an accessible route-owned My KEFE action;
- no preview repository or deterministic preview fallback is allowed in production;
- preview-only Radar, Atlas and Weigh hub remain unavailable in production;
- guest actor continuity remains valid;
- observed-history and non-inference boundaries remain unchanged.

## Runtime slice

- `KefeApp` exposes `/my-kefe` with normal back navigation;
- production `/explore` reuses embedded Explore and adds an accessible My KEFE action;
- Product Preview keeps its five-destination shell unchanged;
- Product Preview profile now displays compile-time APK identity (`preview version · short commit`);
- Mobile CI stamps the next APK as v8 using `KEFE_PREVIEW_VERSION` and `KEFE_PREVIEW_COMMIT` Dart defines;
- widget coverage verifies production navigation, back behavior, preview isolation and build identity.

## Publication note

The published Documentation Ecosystem v3.4 remains unchanged. This engineering checkpoint does not warrant DOCX/PDF regeneration.
