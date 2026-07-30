# ADR-0039 — Premium visual system and scalable localization slice 1

- Status: Accepted
- Date: 2026-07-30
- Tracks: Issue #98
- Extends: ADR-0034, ADR-0037, ADR-0038
- Stack base: PR #97 head `3f989bc74d894ef128aa933e814bdf08415af5f2`
- Verified runtime inherited from PR #97: `f7ab9b9d3db235bd9fdcc0c12950e5c181791018`

## Context

The repository/runtime is materially more mature than the phone UI. Human phone screenshots from the PR #97 Internal Alpha show the actual baseline: a functioning Material/card-based product with a light-theme-dominant presentation, simple balance/result visualizations, preview-style Radar/Atlas surfaces, and mixed-language Product Preview fixture content when English UI chrome is selected.

The audit also found a concrete theme correctness defect: several presentation widgets use dark-only tokens such as `surfaceElevatedDark` while the active theme is light. This produces dark panels whose text still inherits light-theme foreground colors, creating low-contrast or nearly unreadable states. The Weigh featured card has the inverse version of the same problem: a dark gradient is rendered while title text still inherits the light theme.

Visual maturity must therefore be improved as a controlled product-quality layer without changing decision semantics, runtime contracts, or preview/production isolation.

## Decision

### 1. Theme-adaptive semantic visual system

Introduce a Flutter-native semantic visual theme above raw color constants. Presentation code consumes semantic surfaces/foregrounds/borders/glows instead of directly choosing dark-only background tokens.

The visual system is dark-first in identity but must remain fully valid in light mode. It provides at least:

- app/background and elevated surface roles;
- premium/hero surface roles;
- readable foreground/muted foreground roles;
- KEFE gold brand accent;
- Rules/Rights cyan-blue accent;
- Empathy/Compassion warm gold/coral accent;
- supporting attention/success/burgundy roles;
- semantic borders/shadows/glow strengths;
- motion durations that collapse to zero when Reduce Motion / disabled animations is active.

A dark premium surface rendered inside light mode must explicitly own a readable foreground. No presentation widget may assume that the ambient theme foreground matches a manually darkened background.

### 2. First vertical slice is the Decision Journey Foundation

This ADR authorizes only the first controlled UI slice:

- Weigh hub visual hierarchy;
- Decision question card hierarchy;
- binary choice / `KefeBalanceVisual` interaction;
- confidence and reasons surfaces;
- Context/source information surface;
- Commit CTA treatment.

Reveal/KEFE Gap, Perspective, Radar and Atlas are audited but remain follow-up slices unless a shared primitive change touches them incidentally. No big-bang rewrite is authorized.

### 3. Signature balance remains semantically equivalent

`KefeBalanceVisual` remains a generic binary-decision renderer. It may gain Flutter-native drawing, glow, selection emphasis and restrained motion, but:

- option order/value semantics do not change;
- Case-specific logic is forbidden;
- selection remains accessible outside the illustration;
- screen-reader semantics remain explicit;
- Reduce Motion disables non-essential animation;
- renderer failure or visual simplification must never block answer selection or Commit.

### 4. Localization evolves by governed catalogs, not screen branching

ADR-0038 remains authoritative for production presentation. This slice adds a scalable resource boundary:

- new/changed UI copy in the slice is sourced from locale catalogs behind `KefeStrings`;
- presentation code does not add locale branching;
- Product Preview UI chrome is governed, not exempt by default;
- preview fixture content remains explicitly preview-only and may use a dedicated preview content catalog;
- adding a future locale must not require Decision/Weigh presentation logic changes.

The existing TR/EN inline catalog can be migrated incrementally; this slice must not pretend the whole repository is already resource-catalog complete. Exact governed scopes are executable in the companion contract.

### 5. Product truthfulness and runtime invariants remain unchanged

This slice does not alter:

- Commit First or Blind First;
- immutable CaseVersion;
- case-agnostic generic flow runtime;
- preview / production repository isolation;
- preview fixtures as production fallback (forbidden);
- My KEFE descriptive-only semantics;
- Signal/Impact scope;
- inference policy;
- Atlas/Radar preview truthfulness;
- production/store release gates.

## Acceptance

A new verified checkpoint requires on one exact stacked runtime head:

1. theme-adaptive visual contract checks pass;
2. no new governed hardcoded-copy or direct locale branching violations;
3. Decision Journey widget/regression/accessibility tests pass in light and dark modes;
4. Reduce Motion fallback has deterministic test coverage for the signature balance/motion layer;
5. existing phone acceptance, API CI, Mobile CI, MVP Beta Gates and Global Readiness remain green;
6. any new phone APK is tied to that exact runtime head and is not described as production/store ready.
