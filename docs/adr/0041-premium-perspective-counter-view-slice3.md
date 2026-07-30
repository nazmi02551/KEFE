# ADR-0041 — Premium Perspective / counter-view slice 3

- Status: Accepted
- Date: 2026-07-30
- Tracks: Issue #102
- Extends: ADR-0038, ADR-0039, ADR-0040
- Stack base: PR #101 status head `dc1e4615b2988808edc4510afe5b7175d283b513`
- Inherited repo-verified Reveal runtime: `08f9122a1aa9519bfd6045345c836aa3173d831b`

## Context

The verified Reveal slice now gives the post-Commit result a stronger visual hierarchy, but the existing Perspective surface remains materially closer to the earlier Material/card baseline:

- the section shell is a standard `Card` with a fixed purple accent;
- slot cards use ad-hoc colors and raw presentation tokens instead of the semantic KEFE visual system;
- methodology and curated/degraded state notes have weak hierarchy;
- raw Perspective body/provenance fixture text can remain Turkish while English UI chrome is selected in Product Preview;
- there is no clean presentation seam for a future richer Perspective Landscape, even though the current bounded card model is product-valid.

Perspective is post-Commit content. It must remain subordinate to the user's committed decision and descriptive result; it is not evidence that KEFE has inferred the user's ideology, personality, bias or psychological profile.

## Decision

### 1. Perspective semantics remain unchanged

This slice changes presentation and display-time localization only. `PerspectiveResult`, `PerspectiveCard`, `PerspectiveMethodology`, slot identities, source kind, moderation state, retry behavior and repository/controller lifecycle remain authoritative and unchanged.

No new ranking, recommendation, user profiling, psychometric interpretation, ideology inference, bias inference, causal interpretation or Signal/Impact semantics are introduced.

### 2. Perspective remains post-Commit only

Perspective must not be requested or rendered before the existing Commit → Reveal boundary. Existing controller behavior that loads Perspective after Reveal remains unchanged. Retry must reload Perspective only; it must never replay answers, private reasons, Commit or Reveal.

### 3. Semantic slot hierarchy

The four existing slots remain generic and case-agnostic:

- `near`: a perspective that is relatively near the represented decision space, not a claim about the user's identity;
- `opposing`: a materially opposing perspective;
- `bridge`: a perspective that exposes a possible common value or reconciliation frame;
- `alternativeContext`: a context shift that may change how the dilemma is weighed.

Presentation may give these slots distinct visual roles, but must not imply correctness, moral quality, political placement, or a measured distance from the individual user.

### 4. Theme-adaptive KEFE surfaces only

The governed Perspective shell, state notes, cards and methodology disclosure must consume semantic `KefeVisualTheme` / `KefeSurface` roles. Direct dark-only surface tokens and fixed ad-hoc accent colors are forbidden in the governed slice.

Rendering remains Flutter-native and lightweight. No WebView, Three.js, continuous heavy shader animation or speculative 3D engine is authorized.

### 5. Display-time content localization

Production Perspective content remains pass-through because production content is expected to arrive locale/CaseVersion pinned. Product Preview may translate fixture content through `KefeContentLocalizer` using stable Perspective card/methodology identifiers.

Localization must not mutate raw `PerspectiveCard.id`, slot, body, source kind, provenance label, moderation state or methodology values in the repository/domain layer.

Presentation files must not add direct locale branching.

### 6. Methodology and degraded states stay visible

`DEGRADED_CURATED` and `CLUSTER_PENDING` remain descriptive methodology states. The UI may improve their hierarchy but must not hide or rename them into stronger quality claims.

Methodology remains progressively disclosed but readable, including provenance note, sample kind and sample size.

### 7. Future Perspective Landscape seam without speculative data model

This slice may introduce a reusable presentation structure that could later host a richer Perspective Landscape. It does not authorize a new graph, distance metric, inferred user coordinate, clustering claim or new backend schema.

### 8. Adjacent post-Commit capabilities remain intact

Consensus, Community Reasons, Progress and Share remain separate bounded capabilities and retain their current lifecycle and semantics. This slice must not merge them into Perspective or change their ordering/eligibility rules beyond harmless visual spacing needed by the Perspective shell.

## Acceptance

A verified slice 3 checkpoint requires one exact runtime head where:

1. production copy boundary passes;
2. governed Perspective presentation has no direct dark-only raw surface tokens, fixed purple visual dependency, or direct locale branching;
3. Perspective remains unrequested/unrendered before Commit and retry does not replay answer/reason/Commit/Reveal;
4. raw Perspective ids/slots/content/source/moderation/methodology values remain unchanged while Product Preview display localization is tested;
5. near/opposing/bridge/alternative-context hierarchy is accessible and does not imply user profiling or objective correctness;
6. curated/degraded/cluster-pending and methodology disclosure remain represented;
7. light/dark themes and accessibility semantics remain valid;
8. API CI, Mobile CI, MVP Beta Gates and Global Readiness all succeed on the same runtime SHA.
