# ADR-0057 — Atlas World / Globe Convergence

**Status:** Accepted working architecture  
**Date:** 2026-07-31  
**Tracker:** #140  
**Parent:** ADR-0055 High-Fidelity Visual Composition Foundation

## Context

The existing Atlas is a secondary Product Preview surface. It currently uses a selected Preview Case, six deterministic country fixtures and a representative 0–10 KEFE continuum. The screen already states that these values are Product Preview examples and are **not real country results**.

The target art direction calls for a much richer world/globe hero. Visual fidelity must not convert representative fixture data into a claim of live sampling, national representativeness, methodology validation, Signal, authority or production Atlas readiness.

Slice 17 established reusable composition/fallback/accessibility/performance rules. Slice 18 demonstrated that a high-fidelity visual can improve materially while keeping truthfulness and generic runtime semantics intact.

## Decision

Converge the existing Preview Atlas to a richer **Atlas World / Globe** presentation while preserving its current product and data status.

### 1. Atlas status remains Preview-only

This slice does not promote Atlas into production navigation or a primary tab.

- `/atlas` remains a secondary Product Preview route.
- Product Preview fixture data remains isolated from production.
- No new API, schema, aggregation service, country sampling pipeline or production provider is introduced.

### 2. Representative data remains explicitly representative

The existing notice that Atlas values are representative Product Preview data and not real country results remains conspicuous and must be reachable in the phone candidate.

The six current country fixtures remain examples on a 0–10 continuum.

This slice must not invent:
- national sample size;
- date range;
- confidence score;
- raw-versus-weighted methodology;
- demographic or local breakdown;
- per-country Rules/Rights versus Empathy percentages;
- live update time;
- causal explanation for country differences.

Future production Atlas may require these fields and methodology through a separate product/data contract. This visual slice cannot imply that future evidence already exists.

### 3. Existing scalar meaning is preserved

Each country currently owns one representative `value` in the 0–10 Preview continuum.

The new globe may encode only that existing scalar through:
- marker position/color/emphasis in the KEFE continuum;
- country code/name and existing formatted value;
- visual glow/depth.

It may not derive two percentages that sum to 100 or reinterpret the scalar as population support.

### 4. High-fidelity globe is presentation, not globe engine

Implement a lightweight Flutter-native dimensional globe using bounded static composition:
- radial atmosphere/depth;
- sphere lighting;
- latitude/longitude graticule;
- subtle abstract landmass silhouettes;
- deterministic orbit/network arcs;
- deterministic country marker nodes;
- KEFE Rules cyan → gold → Empathy warm visual continuum.

No mandatory live 3D engine, WebView or Three.js.

The globe is static while idle. Any transition added later must resolve through the Slice 17 Reduce Motion policy.

### 5. Country marker placement is presentation metadata only

For Preview rendering, marker positions may use a deterministic presentation-only world coordinate map associated with the existing country codes.

Those positions:
- exist only to place markers on the stylized globe;
- do not change country result semantics;
- are not evidence of sample geography or jurisdictional methodology;
- must not be exposed as analytical data.

### 6. Truth notice and selected Case hierarchy stay strong

The hero must preserve:
- selected Case title;
- `worldView` framing;
- representative-data notice above/before the analytical cards;
- country-average heading and country cards;
- existing 0–10 continuum labels.

The richer globe must not visually overpower or hide the notice that the values are examples.

### 7. Accessibility and compact layout

- Globe geometry is decorative unless a marker has an explicit semantic label.
- Country cards remain the complete text-accessible representation of all fixture values.
- No information may be available only by color, spatial position or glow.
- Compact phone layouts reduce globe height/detail deterministically rather than hiding truth labels or cards.
- Light and dark themes remain valid.
- Text scaling must not cause the representative-data notice to be clipped.

### 8. Performance

Reuse Slice 17 performance principles:
- bounded CustomPainter work;
- no idle per-frame repaint;
- no continuous particles/shader loop;
- no remote asset dependency required for the first implementation;
- RepaintBoundary around the globe composition when useful;
- deterministic rendering on low-end Android.

### 9. Preview reachability

The existing Product Preview Explore secondary action must continue to reach `/atlas`.

Phone regression must prove:
- Atlas action exists;
- route opens Atlas;
- representative-data notice is visible/reachable;
- high-fidelity globe is present;
- selected Case and country cards remain present;
- no production route gains `/atlas` accidentally.

## Consequences

### Positive
- Atlas becomes visually much closer to the premium world/globe concept direction.
- Data truthfulness is not sacrificed for visual fidelity.
- Later production Atlas can replace Preview fixtures behind a separate data/methodology contract without rewriting the visual system.
- Country cards remain accessible and auditable.

### Trade-offs
- The first globe is a stylized deterministic Flutter rendering, not a photorealistic or interactive 3D planet.
- Preview country markers are presentation-only and must not be mistaken for production geographic analytics.
- The concept mockup’s richer percentages/metadata cannot be copied until real methodology supplies them.

## Rejected alternatives

### Invent Rules/Empathy percentages from the 0–10 scalar
Rejected because it changes meaning and creates false precision.

### Add fake sample size/confidence/update timestamp for visual similarity
Rejected because it fabricates evidence.

### Promote Atlas into production navigation during the visual slice
Rejected because that is a separate product decision.

### Live 3D/WebView globe
Rejected because it adds unnecessary performance and platform complexity for this scope.

## Verification

The slice is not complete until exact-head required CI passes and tests cover:
- Preview-only routing remains intact;
- representative notice text remains present;
- fixture values unchanged;
- no fabricated percentage/sample/confidence/live metadata;
- globe hero exists in light/dark and compact layouts;
- country cards preserve text values;
- Reduce Motion/performance rules remain compatible;
- Product Preview action → Atlas reachability;
- production route isolation;
- existing mobile regressions.

Human visual approval remains external evidence.