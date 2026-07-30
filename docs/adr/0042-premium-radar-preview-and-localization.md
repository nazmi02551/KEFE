# ADR-0042 — Premium Radar Preview and governed localization slice 4

- Status: Accepted
- Date: 2026-07-30
- Tracks: Issue #104
- Extends: ADR-0030, ADR-0039, ADR-0041
- Stack base: PR #103 status head `3056514c4814567d9218b6cde0e1b7247939701f`
- Inherited repo-verified Perspective runtime: `199acad08de0ce1281566bcbc7c6893754db92ae`

## Context

The real Product Preview Radar remains a valid representative capability, but its current implementation is visually and localization-wise behind the verified Decision/Reveal/Perspective surfaces:

- all Radar chrome and ranking copy is hardcoded Turkish in presentation;
- ranking cards are standard Material cards with raw `KefeColorTokens`;
- the preview notice is correct but visually weak;
- static pills visually resemble interactive filtering despite having no implemented interaction;
- `Senin için`/For-you language can imply personalization that Product Preview does not actually perform;
- the representative ranking must not be mistaken for live trend ingestion or a production popularity model.

Radar is currently a Product Preview-only supporting capability. This slice must improve maturity without inventing backend behavior or widening product authority.

## Decision

### 1. Radar remains explicitly representative Product Preview data

The fixed ranking is presentation/demo data only. The UI must clearly state that it is not live trend data and must not imply freshness, production popularity, inferred personalization or a real-time ranking engine.

No live ingestion, ranking algorithm, trend score, velocity metric, recommendation system or personalization model is introduced.

### 2. Separate fixture structure from localized presentation

Stable representative Radar item structure may live in a Product Preview fixture boundary using:

- rank;
- canonical Case id;
- domain code;
- signal/status code;
- raw fallback title only where required by the existing Product Preview content-localization seam.

Presentation must not contain user-facing Turkish/English literals for Radar chrome/items. Chrome/status labels use a dedicated resource-style Radar preview string catalog. Case titles use the existing `KefeContentLocalizer` display-time boundary so raw Case ids/content semantics remain unchanged.

The Radar string catalog must be keyed by locale and string id so adding another locale is an additive catalog extension rather than presentation refactoring. Direct locale branching in `radar_preview_screen.dart` is forbidden.

### 3. Semantic premium visual system

Radar uses `KefeVisualTheme` / `KefeSurface` semantic roles for:

- header identity;
- preview truthfulness notice;
- view/status chips;
- ranking cards;
- rank marker;
- domain/signal metadata;
- navigation affordance.

Direct dark-only surface tokens and generic unstyled `Card` ranking shells are forbidden in governed Radar presentation.

Shared Product Preview primitives may be made theme-adaptive where the change is semantic-only and does not alter Atlas product semantics or data.

### 4. Static view chips must be truthful

Until filtering is implemented, Radar view pills are status/navigation context, not tappable filters. They must not expose button semantics or hover/tap affordance.

The unsupported `For you` preview label is removed from Radar because it implies personalization that does not exist. This does not remove any runtime capability because no personalization/filter action is currently implemented.

### 5. Case navigation remains canonical

Selecting a Radar ranking card continues to open `/case/:caseId` using the existing stable Case id and generic Decision runtime. Radar must not create case-specific screens or mutate CaseVersion/decision semantics.

### 6. Performance and accessibility

The slice remains lightweight Flutter-native layout only. No continuously running animation, WebView, Three.js or heavy rendering is authorized.

Ranking cards must retain button semantics, readable metadata hierarchy, sufficient contrast in light/dark themes and text-first comprehension.

### 7. Atlas remains separately governed

This slice does not redesign Atlas data, country values, 0–10 semantics or selected-case framing. Theme-adaptive changes to shared preview header/notice primitives are allowed only when they preserve Atlas structure and truthfulness.

## Acceptance

A verified Slice 4 checkpoint requires one exact runtime head where:

1. Radar presentation contains no direct user-facing TR/EN copy except stable product/technical identifiers;
2. no direct locale branching exists in Radar presentation;
3. Radar item/chrome localization is covered for TR and EN with additive locale-catalog structure;
4. representative/live-data truthfulness copy remains visible;
5. unsupported personalization language/interaction is absent;
6. ranking cards still navigate through canonical Case ids;
7. governed Radar/shared preview visuals use semantic theme roles with no direct dark-only surface tokens;
8. light/dark/accessibility and existing Product Preview navigation regressions pass;
9. API CI, Mobile CI, MVP Beta Gates and Global Readiness all succeed on the same runtime SHA.
