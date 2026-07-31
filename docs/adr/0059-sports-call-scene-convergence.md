# ADR-0059 — Sports CALL Scene High-Fidelity Convergence

Date: 2026-07-31  
Status: Accepted for Slice 21 implementation  
Tracker: #144  
Stack parent: `feature/perspective-landscape-slice20`

## Context

KEFE already supports a generic `SPORTS_CALL` Case through the same case-agnostic decision runtime used by other Cases. The current representative Preview Case is:

- title: `Bu pozisyonda penaltı kararı doğru muydu?`;
- binary decision: `Doğru` / `Yanlış`;
- optional confidence;
- generic private-reason schema.

The current media boundary is provider-neutral and CaseVersion-pinned. For the representative Sports CALL Case, Preview currently exposes a `PRE_COMMIT_SAFE` illustration whose semantic asset locator is `SPORTS_DECISION` and whose alt text explicitly describes an abstract football-field, ball and decision-moment illustration.

The current CaseVersion/media model does **not** contain typed spatial evidence: no player/ball coordinates, event frame/time, camera view collection, VAR frame, referee position, contact/offside/goal-line annotations or adjudication result metadata.

Premium concept references show a much richer football scene with multiple camera modes and decision geometry. Reproducing those controls or lines without typed evidence would fabricate product capabilities and potentially present decoration as evidence.

## Decision

Slice 21 introduces a shared provider-neutral renderer family:

`KEFE_SPORTS_SCENE_V1`

The renderer produces a materially richer **illustrative football decision scene** for a Case media rendition that explicitly selects this renderer family.

The renderer is a presentation capability, not a Case type. Runtime selection is by `CaseMediaRendition.rendererCode`; the renderer must not inspect Case ID, Case title, Case format or Domain.

### Preview adoption

The existing Preview asset specification with semantic locator `SPORTS_DECISION` selects `KEFE_SPORTS_SCENE_V1` instead of the generic `KEFE_ABSTRACT_V1` renderer.

Other Preview media assets remain on their existing renderer unless separately contracted later.

This does not create Preview fallback in production. Production rendering supports the provider-neutral renderer family only when a production media repository explicitly supplies an approved rendition using that code.

### Illustrative, not evidentiary

The sports scene may render only a stylized football environment such as:
- pitch perspective and field markings;
- goal structure;
- abstract opposing player figures;
- ball;
- ambient stadium/depth treatment;
- non-semantic decision-focus glow.

These shapes are decorative illustration. Their positions, spacing and perspective are fixed renderer grammar and do not encode factual event coordinates.

The renderer must not render or imply:
- offside/contact/goal-line evidence;
- a factual referee position;
- a VAR camera/frame;
- a measured player or ball coordinate;
- an adjudication line;
- a ruling/correctness indicator;
- replay controls or evidence-view tabs.

Existing alt text and attribution remain the semantic/provenance truth of the presentation item. Presentation media remains separate from Claim/Source/Evidence authority.

### Decision behavior

The scene does not replace the question controls. The canonical `Doğru` / `Yanlış` values, confidence, reason capture, Commit, Reveal and Perspective flow remain unchanged.

No binary percentage/coordinate is derived from the scene. Selection state does not mutate scene evidence or imply that KEFE has adjudicated the call.

### Exposure

The existing `MediaExposurePhase` remains authoritative. The current representative scene is `PRE_COMMIT_SAFE`; no result or collective information may appear in it.

### Rendering and performance

Use lightweight deterministic Flutter-native rendering:
- `CustomPainter`/standard widgets only;
- theme-adaptive KEFE semantic roles;
- bounded fixed geometry;
- `RepaintBoundary` around custom painting;
- no idle continuous animation;
- no WebView, Three.js or mandatory live 3D;
- no remote asset dependency required for the Preview renderer.

Unsupported renderer/theme/media failure continues to use the existing deterministic fallback and must not block the decision core.

### Accessibility

The illustration itself is not a second source of semantic facts. Existing informative `CaseMediaPresentation.altText` remains the image semantic label. Decorative internal geometry is excluded from independent semantics.

Attribution remains available according to the existing media presentation policy.

## Future typed Spatial CALL

An interactive spatial-evidence CALL with multiple camera views, frame selection, adjudication lines or coordinate overlays is a **future capability**, not Slice 21.

Before that capability can exist, KEFE requires a separate contract defining at least:
- immutable evidence/view identity;
- coordinate/reference-frame semantics;
- view/camera provenance;
- annotation meaning and author/reviewer provenance;
- exposure phase;
- evidence-vs-decoration distinction;
- accessibility representation;
- editorial validation and rights/provenance;
- deterministic fallback when spatial data is absent.

No future spatial-evidence schema is inferred from the decorative geometry introduced here.

## Preserved invariants

Slice 21 does not change:
- Commit First / Blind First;
- immutable CaseVersion;
- generic decision runtime;
- question/answer semantics;
- media exposure rules;
- Preview/production isolation;
- Claim/Source/Evidence authority;
- My KEFE non-inference;
- Signal/Impact boundaries;
- backend/API/schema or production provider readiness.

## Verification

Before PASS, one exact runtime SHA must pass:
- API CI;
- Mobile CI;
- MVP Beta Gates;
- Global Readiness.

Mobile verification must include:
- executable contract guard;
- renderer selected by rendition code, not named Case logic;
- Sports Preview media uses `KEFE_SPORTS_SCENE_V1`;
- non-Sports Preview media renderer continuity;
- current Sports CALL title/question/options unchanged;
- scene reachable pre-Commit on the representative Sports CALL Case;
- no Reveal before Commit;
- no fake VAR/view/offside/adjudication controls or copy;
- dark/light rendering;
- compact phone and enlarged-text surrounding layout;
- media fallback does not block the decision core;
- full existing mobile regressions, production-copy boundary and phone acceptance.

Human visual/usability review remains external evidence.
