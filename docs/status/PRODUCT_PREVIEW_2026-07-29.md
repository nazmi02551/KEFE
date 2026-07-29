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

Preview artifact from that run:

- artifact name: `kefe-preview-android`
- artifact id: `8724944101`
- workflow artifact digest: `sha256:5b1661c8d477bb3b0cd2a109a7b3873cd280b6f81e4daa3e23a48e42ef06b144`

## Signature KEFE scale / Results depth

PR #74 — `Add signature KEFE balance and richer Reveal results`

Merge commit:

`2a4958488f0da068431b146edb1a5a145c0eef35`

Implemented in the existing generic decision presentation rather than adding a Case subtype:

- reusable Flutter-drawn `KefeBalanceVisual` with no image-asset dependency;
- binary SINGLE_CHOICE decisions use the same typed question primitive but now present a recognizable two-sided KEFE scale interaction;
- non-binary SINGLE_CHOICE behavior keeps the generic fallback;
- existing option identity, draft persistence, reason capture and Commit semantics remain unchanged;
- Reveal now separates `SENİN KARARIN` from the community distribution;
- `KEFE UÇURUMU` provides only a descriptive selected-share versus highest-share comparison;
- no political, personality, psychometric or causal inference was introduced;
- Commit-before-Reveal remains binding;
- layout-sensitive decision-flow tests were made scroll-safe rather than shrinking the richer mobile experience.

Verified exact-head Mobile CI:

- run `30463781173` — PASS
- analyze PASS
- widget/unit tests PASS
- Android preview APK build PASS
- artifact upload PASS

Preview artifact from that run:

- artifact name: `kefe-preview-android`
- artifact id: `8728968655`
- workflow artifact digest: `sha256:2a7a100cbff7a55b371258ef2de6c033359c384b9c40d1709ad0f43553d983cf`
- extracted APK sha256: `b1ae03acfbeb9e9847a50cf97475c294910654cd072a2b33852176339e548867`

## Premium Case hero / Flow hierarchy

PR #76 — `Add premium Case hero and explicit Flow journey to Product Preview`

Merge commit:

`ca3e865bd525c9a04071774220d9c77089a216de`

Implemented:

- generic `CaseHeroHeader` using existing Case and Flow runtime metadata;
- domain / format / risk metadata, title and summary in one premium Case surface;
- `KARAR YOLCULUĞU` rail derived from generic Flow primitives and runtime states;
- repeated primitives are numbered rather than converted into Case-specific screens;
- blocked, ready, completed and unsupported steps remain visually distinguishable;
- `productPreviewVisualModeProvider` defaults false;
- only the explicit Product Preview composition opts into the richer visual hero;
- production `main.dart`, normal `KefeApp`, networking and failure behavior remain unchanged.

Verified exact-head Mobile CI:

- run `30465112912` — PASS
- analyze PASS
- widget/unit tests PASS
- Android preview APK build PASS
- artifact upload PASS

Preview artifact from that run:

- artifact name: `kefe-preview-android`
- artifact id: `8729454335`
- workflow artifact digest: `sha256:44b5cd2060d2e8c2e88b5bcd25e5c8d9839082daed98b450cab6395a42fe1f16`
- extracted APK sha256: `a81da791487a36919ec7c51ac0392bedf8ac317ab47f2c689e6a89439f06ecb4`

## DecisionRevision / Reflection journey

PR #78 — `Make DecisionRevision and Reflection tangible in Product Preview`

Merge commit:

`63fcd6d96f7517ad86d36165743fdf014fd9a68f`

Implemented without adding a Case-specific runtime class or changing production networking:

- Product Preview explicitly composes `PreviewJourneyDecisionRepository` on top of the deterministic preview catalog;
- the airline child-seat Case demonstrates a generic `Decision → Counterview Context → DecisionRevision → Reflection` Flow;
- this Flow intentionally has no collective-result primitive, proving that collective exposure is a composable capability rather than a mandatory screen;
- first and second decision responses are retained separately in the preview lineage and Reflection derives observed change from those responses;
- the intervening counterview is labeled Product Preview editorial material rather than live fact, research result or causal intervention;
- shared Reflection UI presents a visual decision journey with first/final revision nodes, recorded encounter count and observed change summary;
- the non-causal disclosure remains explicit: KEFE shows change and intervening encounters together but does not claim that an encounter caused the change;
- existing Reflection completion, idempotency and recovery behavior is preserved.

The first implementation attempt expected a collective Reveal after the revision and correctly failed its widget assertion. The final slice was narrowed to the already-proven Reflection-only generic Flow rather than forcing a result primitive into the journey.

Verified exact-head Mobile CI:

- run `30468367898` — PASS
- analyze PASS
- widget/unit tests PASS
- Android preview APK build PASS
- artifact upload PASS

Preview artifact from that run:

- artifact name: `kefe-preview-android`
- artifact id: `8730817374`
- workflow artifact digest: `sha256:ba801bf3fc908d93cb77800dc267e14b6550ce1b3d368e5229064ed1f793bffd`
- extracted APK sha256: `4cb20971bce9eaa79855782b45d561b8b99b37188cc9c3862c8880d3b6fd8bbf`

## Case media presentation boundary

PR #80 — `Lock provider-neutral Case media presentation boundary`

Merge commit:

`874e8a35e1678b461b699c411d9f3cf7a6571cb4`

Added:

- ADR-0031 `case-media-presentation-boundary`
- `case-media-presentation.v1.yaml`

Binding decisions include:

- Case media is a separate CaseVersion-pinned presentation/read concern rather than Claim truth, evidence or Flow semantics;
- consumer UI reads media through a provider-neutral `CaseMediaRepository` boundary;
- semantic media identity and exposure phase are immutable presentation metadata, while delivery renditions remain replaceable infrastructure;
- initial generic slots are `EXPLORE_CARD`, `CASE_HERO` and `CONTEXT_SUPPORTING`;
- initial media kinds are IMAGE, ILLUSTRATION and VIDEO_POSTER;
- informative media requires alt text and decorative media must be explicit;
- media is `PRE_COMMIT_SAFE` or `POST_COMMIT_ONLY` and cannot bypass Flow authority;
- displaying media does not upgrade it into evidence;
- media failure must degrade to the text-first decision experience;
- preview media is explicit composition data and production may never fall back to it.

Object storage, CDN providers, uploads, processing workers, video playback and automated media generation/selection remain deferred.

## Replaceable Product Preview media runtime

PR #81 — `Add replaceable Case media presentation to Product Preview`

Merge commit:

`7716218761f58123c9b3613cc44c4c5783883b17`

Implemented:

- provider-neutral Case media presentation models and `CaseMediaRepository`;
- production-safe `EmptyCaseMediaRepository` as the default adapter;
- deterministic `PreviewCaseMediaRepository` injected only by `main_preview.dart`;
- all eight preview CaseVersions receive explicit asset identities, content hashes and Turkish accessibility text;
- reusable `CaseMediaSurface` with accessibility semantics and graceful missing/unsupported-media fallback;
- a local Flutter-rendered `KEFE_ABSTRACT_V1` illustration family with no remote provider, CDN URL or image-host dependency;
- featured Explore Case and premium Case hero consume the same repository boundary;
- initial preview assets are PRE_COMMIT_SAFE only and cannot unlock any Flow step or expose collective data;
- automated tests assert that production `main.dart` never imports the preview media repository and that decision Commit semantics remain intact after the richer visual treatment.

The richer vertical layout exposed stale viewport assumptions in Product Preview widget tests. Those tests were corrected to scroll to visible content and to verify Commit/Reveal semantics from controller state where the ListView legitimately keeps post-Commit widgets outside the current viewport.

Verified exact-head Mobile CI:

- run `30470981100` — PASS
- analyze PASS
- widget/unit tests PASS
- Android preview APK build PASS
- artifact upload PASS

Latest preview artifact:

- artifact name: `kefe-preview-android`
- artifact id: `8731906910`
- workflow artifact digest: `sha256:657519d3d01ad86a7b728427a9aad319b8ee723dc58a5c4e811ab7fc17928974`
- extracted APK sha256: `54dacdc835d31ac64dded87e63c3fe93d728a93ce095ba0b536fc3d0478dc910`

## What is now visibly testable

The installable Product Preview now exposes multiple product journeys on the same generic Flow renderer:

`Keşfet + Case görseli → premium Case hero / Karar Yolculuğu + Case görseli → Case Context → signature Tartım → Commit → premium Reveal / KEFE Uçurumu → Karşı Görüşler`

and, for the airline child-seat preview Case:

`Tartım 1 → karşı görüş → yeniden tartım → non-causal Karar Yolculuğu / Reflection`

alongside navigable preview surfaces for:

- Radar
- Tartım hub
- Atlas
- My KEFE

The Case decision paths continue to use existing generic Flow primitives and typed decision contracts. Visual media is now replaceable presentation metadata outside those contracts.

## Important limitations

This is still a Product Preview, not a Play Store release or production-data pilot.

- Radar ranking is deterministic preview data, not live trend detection.
- Atlas country values are preview examples, not measured country aggregates.
- My KEFE history is still a static illustrative preview rather than a repository-backed descriptive journey read model.
- the DecisionRevision/Reflection scenario is deterministic preview lineage, not a live study of persuasion or behavior;
- provider-neutral media metadata and local abstract preview rendering exist, but production object storage/CDN/upload/processing infrastructure is not implemented;
- release signing/AAB/distribution optimization is deferred;
- debug APK size is not a product-completeness metric.

## Next visible slice

Continue the visible-product track before returning to long invisible backend sequences:

1. replace the static My KEFE preview with a generic repository-backed descriptive journey read model using only observed history fields;
2. keep meaningful weigh count, distinct cases/domains, recent Cases and observed DecisionRevision summaries separate from any personality/ideology scoring;
3. use the latest phone-installable Product Preview to gather concrete UX feedback across standard Reveal, DecisionRevision/Reflection and media-rich Case journeys;
4. only then decide which production progress/media API gaps should be connected next.

The scale metaphor, richer Results/KEFE Uçurumu, premium Case hero/Flow hierarchy, non-causal DecisionRevision/Reflection journey and provider-neutral media presentation are now tangible. Future iterations must preserve generic Flow composition, explicit preview isolation, accessibility and Commit-before-collective-exposure rules.

## Documentation note

The published Documentation Ecosystem v3.4 remains the current packaged DOCX/PDF milestone. No publication package regeneration is warranted for this implementation checkpoint.

A separate contract-manifest reconciliation is required because the live `docs/contracts/manifest.v1.yaml` baseline does not yet fully reflect later ADR/contract additions. That cleanup should preserve existing history rather than silently rewriting prior contract lineage.
