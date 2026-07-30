# ADR-0040 — Premium Reveal and KEFE Gap slice 2

- Status: Accepted
- Date: 2026-07-30
- Tracks: Issue #100
- Extends: ADR-0038, ADR-0039
- Stack base: PR #99 status head `d9168a72116cb20563d3868f38f8a8f53184dc3c`
- Inherited repo-verified visual runtime: `21cc0faf76e5dfcf1c54953dd965b026c204865d`

## Context

PR #99 established a theme-adaptive semantic visual system and verified the first Decision Journey visual/localization slice. The real phone baseline still shows a Reveal surface whose behavior is correct but whose presentation remains materially behind the runtime:

- personal decision and community distribution are visually flat;
- result rows are basic progress bars;
- KEFE Gap uses a dark-only raw token inside light mode;
- methodology has weak hierarchy;
- Product Preview result labels can still expose raw Turkish fixture keys while English chrome is active.

Reveal is post-Commit information. Any visual upgrade must preserve the existing Commit First / Blind First boundary and must not move collective data earlier in the journey.

## Decision

### 1. Reveal semantics do not change

The slice may change presentation only. The existing `RevealResult` values, sample size, confidence, selected response and KEFE Gap arithmetic remain authoritative. No new aggregate, inference, ranking or causal interpretation is introduced.

### 2. Personal choice and community distribution are distinct visual layers

Reveal must clearly separate:

1. the user's committed decision;
2. the community distribution;
3. the derived descriptive KEFE Gap;
4. methodology/sample/confidence context.

The personal choice must not visually imply correctness. The leading community option must not be styled as objectively correct.

### 3. KEFE Gap remains descriptive

KEFE Gap continues to express distance between the user's selected share and the leading community share using existing arithmetic. It must not imply personality, ideology, bias, quality, morality or causality.

### 4. Result labels may be localized only at display time

Raw reveal map keys and selected decision values remain unchanged. Presentation may localize labels through `KefeContentLocalizer` using the same option namespace introduced by ADR-0039. This keeps Commit/Reveal lookup semantics stable while allowing locale-consistent Product Preview display.

### 5. Theme-adaptive surfaces only

Reveal presentation must consume semantic `KefeVisualTheme` / `KefeSurface` roles. Direct dark-only surface tokens are forbidden in the governed Reveal scope.

Progress/distribution rendering must remain lightweight Flutter-native UI. Animation is optional and must collapse under Reduce Motion / accessible-navigation settings.

### 6. Progressive disclosure remains safe

Methodology can be visually quieter than the distribution but remains available and readable. No post-Commit data may appear before Commit because of animation state, prefetch presentation or shared widget reuse.

### 7. Future Perspective Landscape seam

This slice may expose a clean presentation seam after Reveal for a future Perspective Landscape, but does not authorize a speculative advanced visualization or new data model.

## Acceptance

A verified slice 2 checkpoint requires one exact runtime head where:

1. production copy boundary passes;
2. governed Reveal code contains no dark-only raw surface tokens or direct presentation locale branching;
3. selected raw option values and reveal map keys remain unchanged while localized display labels are tested;
4. Commit First / Blind First regression tests pass;
5. sample/confidence/methodology and KEFE Gap arithmetic remain covered;
6. Reduce Motion/accessibility behavior remains valid;
7. API CI, Mobile CI, MVP Beta Gates and Global Readiness all succeed on the same runtime SHA.
