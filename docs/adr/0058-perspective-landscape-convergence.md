# ADR-0058 — Perspective Landscape High-Fidelity Convergence

Date: 2026-07-31  
Status: Accepted for Slice 20 implementation  
Tracker: #142  
Stack parent: `feature/atlas-world-globe-slice19`

## Context

The verified Perspective experience already consumes a bounded post-Commit response containing:
- up to four cards in semantic slots `NEAR`, `OPPOSING`, `BRIDGE`, `ALTERNATIVE_CONTEXT`;
- card body/source/provenance/moderation state;
- methodology mode, sample kind, sample size, generation time and provenance note.

The current payload does **not** contain a measured user coordinate, population-density coordinate, ideological/value position, continuous user/community percentage, psychometric score, correctness score, measured distance or causal interpretation.

Premium concept references include a terrain/fikir-coğrafyası visual with apparent user and population percentages. Reproducing those values without a methodology/data contract would create false analytics and conflict with KEFE's non-inference and truthfulness boundaries.

ADR-0041 already allowed a future Perspective Landscape seam to remain presentation-only. Slice 17 now provides the reusable visual-composition/performance/accessibility foundation needed to implement that seam safely.

## Decision

Slice 20 introduces a **qualitative Perspective Landscape** inside the existing post-Commit Perspective loaded surface.

The landscape is a deterministic, Flutter-native visual composition of the **recognized Perspective slots that are actually present** in the current `PerspectiveResult.cards` list.

It is not a statistical landscape and must not be interpreted as one.

### Semantic meaning

The renderer may encode only:
- presence/absence of a recognized Perspective slot;
- the stable semantic identity of that slot;
- visual adjacency/composition chosen by the presentation system.

The geometry is fixed presentation grammar, not measured data. Peak height, horizontal position, glow, contour density, path spacing and visual prominence must not imply popularity, correctness, ideological distance, user similarity, community density or sample strength.

The existing cards remain the complete semantic/text representation and preserve API order. The landscape must never replace card body, provenance or methodology disclosure.

### User-position prohibition

Slice 20 does not render a `Sen` marker, user percentage, community percentage, KEFE-distance coordinate or other measured-user marker because the current Perspective payload does not contain such data.

A future quantitative/user-position landscape requires a separate methodology/data ADR and contract before any runtime rendering.

### Placement

The landscape appears only in loaded Perspective states (`READY`, `CLUSTER_PENDING`, `DEGRADED_CURATED`) when at least one recognized card is present.

It remains inside the existing `PerspectiveSection` after successful Reveal. It does not create a standalone route, primary navigation destination or pre-Commit surface.

Existing degraded-curated and cluster-pending notes remain visible before the landscape/cards, and existing methodology disclosure remains visible after them.

### Rendering

Use lightweight Flutter-native composition:
- deterministic layered contour/terrain paths;
- theme-adaptive Rules/Empathy/Gold/success semantic roles;
- fixed slot anchors driven by slot enum, never Case ID/title/domain;
- no idle continuous animation;
- optional state transition only through existing shared Reduce Motion policy;
- `RepaintBoundary` around expensive custom painting;
- no WebView, Three.js or mandatory live 3D.

The terrain geometry is decorative and excluded from accessibility semantics. Existing Perspective cards provide the accessible content representation.

### Accessibility/layout

- valid dark and light themes;
- compact layout for constrained phone height/width;
- enlarged-text-safe surrounding layout;
- no text embedded into CustomPainter;
- visible slot labels, when used, must resolve through existing `KefeStrings.perspectiveSlotLabel` and must not be the only semantic representation;
- no content may become unreachable because of the landscape height.

## Preserved invariants

Slice 20 does not change:
- Commit First / Blind First;
- immutable CaseVersion;
- generic runtime/capability composition;
- Preview/production isolation;
- Perspective fetch timing or retry semantics;
- Perspective domain/repository/API/schema;
- API card order or local reranking prohibition;
- methodology modes or fields;
- Consensus/Community/Progress/Share semantics;
- My KEFE non-inference boundary;
- Signal/Impact boundaries.

## Explicit non-claims

Slice 20 must not claim or visually imply:
- measured population density;
- user percentile or community percentile;
- ideological/value/psychometric position;
- user-to-community distance;
- correctness, consensus authority or recommendation;
- causal interpretation;
- real-time clustering quality beyond existing methodology mode;
- Signal/Impact readiness;
- human usability/visual approval;
- production/store/provider/SLO readiness.

## Verification

Before PASS, one exact runtime SHA must pass:
- API CI;
- Mobile CI;
- MVP Beta Gates;
- Global Readiness.

Mobile verification must include:
- contract guard;
- post-Commit-only reachability;
- no pre-Commit landscape;
- no numeric user/community position copy;
- slot-presence mapping without Case-specific branch;
- preserved API card order;
- dark/light rendering;
- compact phone layout;
- enlarged text layout;
- existing Perspective consumption/retry/methodology regressions;
- production copy boundary and phone acceptance.

Human visual/usability review remains external evidence.
