# KEFE Product Preview Checkpoint — 2026-07-29

This file is a durable engineering/product checkpoint. It supplements `docs/status/CURRENT.md`; it does not replace the published Documentation Ecosystem v3.4 milestone.

## Why this checkpoint exists

The previous installable Android preview was a valid technical smoke test but exposed only onboarding and a single minimal Case. Product/UX evaluation therefore lagged substantially behind the backend and Flow architecture.

The product direction was intentionally rebalanced so the next milestone is tangible: an installable KEFE Product Preview that communicates the actual product family and the KEFE 2.0 visual identity while preserving the newer generic Flow architecture.

## Architecture lock

PR #70 — `Lock Product Preview visual north star and preview boundary`

Merge commit:

`cd366e5974ee5e32ff492329dbcb303da83b3f51`

Added:

- ADR-0030 `mobile-product-preview-visual-north-star`
- `mobile-product-preview.v1.yaml`

Binding decisions include:

- deep navy / near-black + warm-gold KEFE visual north star;
- primary product shell: Explore / Radar / Weigh / Atlas / My KEFE;
- preview is an explicit build-time composition mode, never a production network fallback;
- production presentation/domain/Flow concepts are reused rather than creating a second fake product;
- Commit-before-Reveal remains binding;
- multiple materially different Cases are required;
- preview Radar/Atlas/My KEFE data must be disclosed as preview data;
- political, personality and psychometric inference from decisions remains forbidden.

## First tangible Product Preview shell

PR #71 — `Build the first tangible KEFE Product Preview shell`

Merge commit:

`fd2945683bad68860aa151af7aea54f797bf92b6`

Implemented:

- premium dark/gold design tokens;
- dedicated `ProductPreviewApp` composition launched only by `main_preview.dart`;
- persistent bottom navigation: Keşfet / Radar / Tartım / Atlas / Profil;
- rich Explore home with featured Case, categories and trend cards;
- deterministic catalog of 8 Cases across daily life, technology, sports, civic, work/economy and education;
- preview ContextRepository with structured evidence/source blocks;
- Radar, Weigh hub, Atlas and My KEFE preview destinations;
- explicit non-live/example-data disclosure on preview-only read models;
- production `main.dart` networking left unchanged;
- preview isolation and multi-case widget tests.

Verified Mobile CI:

- run `30452484780` — PASS

## Case / Weigh visual depth

PR #72 — `Deepen KEFE Product Preview Case and weigh experience`

Merge commit:

`ceec8ae42e2fd23882dd15a748ac01b0b5dc86f9`

Implemented in the shared Flow-driven presentation layer:

- premium Case evidence detail with `Olay özeti`, source hierarchy and information-status summary;
- status visuals for VERIFIED / CLAIMED / DISPUTED / UNKNOWN without changing canonical Claim semantics;
- richer typed SINGLE_CHOICE and CONFIDENCE presentation;
- dedicated `GEREKÇELER` rationale card using the existing reason/privacy contract;
- visual differentiation for Near / Opposing / Bridge / Alternative Context perspectives;
- methodology/degraded-curated disclosure retained;
- end-to-end Product Preview widget test proving Context → Weigh → Commit → Reveal → Perspective and no Reveal before Commit.

Verified exact-head Mobile CI:

- run `30453985724` — PASS
- analyze PASS
- widget/unit tests PASS
- Android preview APK build PASS
- artifact upload PASS

Latest preview artifact from that run:

- artifact name: `kefe-preview-android`
- artifact id: `8724944101`
- workflow artifact digest: `sha256:5b1661c8d477bb3b0cd2a109a7b3873cd280b6f81e4daa3e23a48e42ef06b144`

## What is now visibly testable

The installable Product Preview now exposes a recognizable KEFE application rather than a one-Case smoke fixture:

`Keşfet → Case Context → Tartım → Commit → Reveal → Karşı Görüşler`

alongside navigable preview surfaces for:

- Radar
- Tartım hub
- Atlas
- My KEFE

The Case decision path continues to use the existing generic Flow-driven renderer and typed decision contracts.

## Important limitations

This is still a Product Preview, not a Play Store release or production-data pilot.

- Radar ranking is deterministic preview data, not live trend detection.
- Atlas country values are preview examples, not measured country aggregates.
- My KEFE history is preview data, not the authenticated user's production history.
- remote media/illustration pipeline is not yet implemented;
- final Case header, scale visualization and Results comparison surface still need deeper visual work;
- release signing/AAB/distribution optimization is deferred;
- debug APK size is not a product-completeness metric.

## Next visible slice

Continue the visible-product track before returning to long invisible backend sequences:

1. upgrade shared Case header and step hierarchy;
2. make the Weigh screen's KEFE scale metaphor more prominent without hard-coding Case types;
3. redesign Reveal into a premium Results surface using only data legitimately available from the result/read model;
4. deepen Reflection/DecisionRevision visual journey;
5. add visual/media presentation metadata and replaceable media repository boundaries;
6. gather phone-based product feedback against the Product Preview APK;
7. only then decide which production API gaps should be connected next.

## Documentation note

The published Documentation Ecosystem v3.4 remains the current packaged DOCX/PDF milestone. No publication package regeneration is warranted for this implementation checkpoint.

A separate contract-manifest reconciliation is required because the live `docs/contracts/manifest.v1.yaml` baseline does not yet fully reflect later ADR/contract additions. That cleanup should preserve existing history rather than silently rewriting prior contract lineage.
