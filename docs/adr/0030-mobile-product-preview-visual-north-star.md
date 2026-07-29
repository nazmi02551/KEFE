# ADR-0030 — Mobile Product Preview Visual North Star

- Status: Accepted
- Date: 2026-07-29
- Depends on: ADR-0022, ADR-0023, ADR-0024, ADR-0025, ADR-0026, ADR-0027, ADR-0028, ADR-0029

## Context

KEFE now has substantial backend, decision-lineage, Flow, Reflection, knowledge and ingestion architecture, but the installable Android preview exposes only onboarding plus one minimal demo Case. This is technically useful as a CI smoke test but is not sufficient for product/UX validation.

The product needs a tangible preview that lets an owner/tester judge whether KEFE feels coherent, understandable and desirable before more invisible backend depth is added.

The visual direction is the approved KEFE 2.0 concept language: deep navy/black surfaces, warm gold identity, premium information-dense cards, strong scale/decision metaphors, and a coherent family across Explore, Case detail, Weigh, Results, Radar, Atlas and My KEFE.

## Decision

### 1. Product Preview becomes the next visible milestone

The next mobile milestone is a coherent, installable Product Preview rather than another single-case technical demo.

The preview must make the core journey visible:

`Explore → Case Context → Weigh → Commit → Reveal → Perspectives → Reflection`

It also establishes visible application navigation for:

- Explore
- Radar
- Weigh/active decision entry
- Atlas
- My KEFE

The first implementation may use deterministic preview data for surfaces whose production service is not yet available.

### 2. The KEFE 2.0 visual language is the north star

The mobile design system should converge on:

- deep navy/near-black backgrounds;
- warm gold as the KEFE identity/action accent;
- blue for rule/order-side visual semantics where needed;
- red/coral for empathy/impact-side contrast where needed;
- high-contrast typography and restrained glow/gradient use;
- rounded premium cards with dense but readable information hierarchy;
- prominent KEFE scale iconography and decision-state feedback;
- bottom navigation as the persistent product shell on primary destinations.

The implementation must not copy a screenshot pixel-for-pixel when doing so conflicts with accessibility, responsive layout or later product decisions.

### 3. Preview is a composition mode, never a production fallback

`main_preview.dart` remains an explicit build-time entrypoint.

Preview repositories may provide deterministic data and simulated transitions, but production `main.dart` never falls back to preview data on network/API failure.

The same presentation components, domain models and Flow-driven decision renderer should be reused wherever possible. Preview-specific code must stop at composition/data boundaries rather than fork the product UI into a separate fake app.

### 4. Preview must contain multiple materially different Cases

The Product Preview should expose enough cases to test information hierarchy and content diversity, including examples from multiple domains such as:

- daily-life dilemma;
- technology/AI;
- civic/public decision;
- Sports CALL;
- workplace/economic dilemma.

At least one Case must exercise the generic Commit/Reveal path. A later preview slice should exercise DecisionRevision and Reflection through a materially different Flow.

Case-specific Flutter screen classes are forbidden. Differences must be expressed through existing typed question models, Flow primitives, capabilities and presentation metadata.

### 5. The shell may expose preview-only destination data, not preview-only product semantics

Radar, Atlas and My KEFE may initially render deterministic preview view-model data while their production read APIs are incomplete.

However:

- their visible concepts must correspond to approved product concepts;
- preview-only data must not create a new source of truth;
- the UI must be replaceable by production repositories without redesigning the screen hierarchy;
- unsupported future features should be honestly represented rather than silently simulated as completed production behavior.

### 6. Results remain descriptive, not psychometric

The visual concepts may show comparisons such as the user's current Case result, community distribution, country distribution, expert/verified-group distribution, gap or decision-history summaries.

They must not infer or label political ideology, personality, mental traits or psychometric identity from user decisions.

A My KEFE summary may describe observable decision history, for example number of weighs, domains explored, revisions made, or Cases where the user differed from a comparison group, without turning those observations into hidden identity scoring.

### 7. Commit-before-reveal remains binding

The richer visual experience does not weaken decision integrity.

Collective result, comparison and perspective content that could bias the initial decision remains blocked until the relevant Commit gate is satisfied according to the server/preview Flow runtime.

### 8. Accessibility and responsiveness outrank ornamental fidelity

The design must support:

- readable contrast;
- Dynamic Type/text scaling within practical bounds;
- touch targets appropriate for mobile;
- screen-reader semantics for primary controls and result summaries;
- layouts that work across common Android phone widths;
- dark-theme-first design without making light theme a prerequisite for this milestone.

### 9. Debug APK size is not a product-content metric

CI may continue to produce a debug Preview APK for fast installation. Its file size is not treated as evidence of product completeness.

A later distribution milestone must add release/AAB size and startup checks separately.

## First implementation slice

The first visible slice should:

1. promote the dark/gold KEFE visual token set;
2. add the primary bottom-navigation shell;
3. redesign Explore into a real KEFE home surface with hero/trending/categories;
4. expand deterministic preview data to multiple Cases;
5. restyle the existing Case/Decision/Reveal path without bypassing Flow authority;
6. add lightweight Radar, Atlas and My KEFE preview destinations backed by replaceable preview view models;
7. preserve production networking and existing decision contracts;
8. add widget/architecture tests proving preview remains isolated and production never imports preview repositories.

## Deferred

- production Radar ingestion/read API;
- production Atlas aggregation API;
- production My KEFE history/profile API;
- remote media pipeline and CDN assets;
- final illustration/brand asset pack;
- release signing and Play Store bundle;
- Admin Studio mobile UI;
- political/personality profiling.

## Consequences

- KEFE becomes testable as a product rather than only as architecture.
- UX feedback can be collected before more backend investment hardens weak interaction choices.
- preview data can fill temporary API gaps without contaminating production behavior.
- the original KEFE 2.0 visual ambition is restored while keeping the newer modular Flow/knowledge architecture intact.
