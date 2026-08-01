# KEFE Sports CALL Scene High-Fidelity Convergence — Slice 21

Date: 2026-08-01  
Status: REPO_VERIFIED / HUMAN_VISUAL_USABILITY_PENDING  
Issue: #144  
PR: #145  
ADR: ADR-0059  
Executable contract: `docs/contracts/sports-call-scene-slice21.v1.json`

## Verified runtime

Exact runtime SHA:
`eb7dbb2f85f5fa955040c5da60c6ab4c928e7da8`

Any later documentation-only commit on PR #145 must not redefine this verified runtime.

## Exact-head CI evidence

All four required workflows completed successfully on the exact same runtime SHA:

- API CI #903 — run `30686665292` — SUCCESS
- Mobile CI #698 — run `30686665293` — SUCCESS
- MVP Beta Gates #407 — run `30686665297` — SUCCESS
- Global Readiness #310 — run `30686665295` — SUCCESS

Verified gates include canonical Dart formatting, analyzer, complete Flutter regressions, the Sports CALL renderer/route/entrypoint tests, production-copy boundary, phone acceptance, API/generic-runtime contracts, PostgreSQL MVP/global regressions, and Android candidate builds.

## What Slice 21 implemented

### Provider-neutral Sports scene renderer

A shared Flutter-native renderer family was introduced:

`KEFE_SPORTS_SCENE_V1`

Runtime selection is exclusively through `CaseMediaRendition.rendererCode`. The renderer does not inspect Case ID, Case title, Case format or Domain.

The existing Preview media item with semantic locator `SPORTS_DECISION` now selects this renderer. Other Preview media assets retain `KEFE_ABSTRACT_V1` unless separately contracted.

### Rich illustrative football scene

The renderer produces a deterministic, theme-adaptive football decision illustration using:
- pitch perspective and markings;
- goal structure;
- abstract opposing player figures;
- ball;
- ambient stadium/depth treatment;
- non-semantic decision-focus glow.

The scene uses Flutter widgets and `CustomPainter`, is isolated by `RepaintBoundary`, and has no continuous idle animation, WebView, Three.js or mandatory live 3D dependency.

### Truthfulness boundary preserved

The current CaseVersion/media payload does not contain player or ball coordinates, event frames, camera viewpoints, VAR frames, referee position, adjudication annotations or correctness metadata.

Therefore Slice 21 does **not** render or claim:
- `Üstten`, `Hakem` or `VAR` evidence-view controls;
- replay controls;
- player/ball/referee coordinates;
- offside/contact/goal-line adjudication lines;
- factual camera geometry;
- a correctness/ruling indicator;
- spatial evidence or reconstructed event truth.

The scene remains explicitly representative presentation media, not Claim/Source/Evidence authority. Existing alt text and attribution remain semantic/provenance truth.

### Decision semantics preserved

The representative Sports CALL remains unchanged:
- title: `Bu pozisyonda penaltı kararı doğru muydu?`;
- question: `Hakemin penaltı kararını nasıl değerlendiriyorsun?`;
- canonical options: `Doğru` / `Yanlış`;
- optional confidence;
- existing private-reason, Commit, Reveal and Perspective behavior.

The scene is `PRE_COMMIT_SAFE` and exposes no collective result before Commit.

### Generic runtime and fallback preserved

Executable tests prove:
- renderer selection is by rendition code;
- no named Sports Case branch exists;
- the Sports Preview item selects `KEFE_SPORTS_SCENE_V1`;
- non-Sports Preview assets retain their existing renderer;
- unsupported renderer fallback does not block the media surface or decision core;
- the generic Case route reaches the Sports scene under the exact phone-preview provider configuration;
- lazy decision controls remain reachable and retain raw option keys;
- Reveal is absent before Commit;
- `main_preview.dart` retains the visual-mode and Preview media repository overrides;
- Product Preview retains its generic `/case/:caseId` route.

### Accessibility and performance

- dark and light theme coverage;
- enlarged-text surrounding layout coverage;
- informative media semantics continue to use existing alt text;
- internal scene geometry does not create a second semantic evidence source;
- deterministic fixed geometry and no idle continuous animation;
- Android phone acceptance and full mobile regressions passed.

## Rejected/corrected candidates

No PASS claim attaches to the following candidates:

- `0c042a67224ab7f465a8e0fbaa5534ac66acecf7` — analyzer failure caused by missing visual-composition extension import.
- `61a46874a548a086bd00666af29f244350bcf110` — Product Preview test used an unbounded `pumpAndSettle` assumption.
- `f5fec755f59b3776c6ed439440fe8e297abcb04a` — canonical Dart format gate failed.
- `afb55ede6e077a03d6e50d2741142cb001bffb10` — production-copy boundary interpreted a presentation-layer technical key literal as product copy.
- `6db412367c36cd926a6b7d1fee09374af716a691` and `9174c382e8697728a1426dc3065d3ae6fd30a545` — Product Preview reachability harness did not match the distributed preview visual-mode configuration.
- `6b18fd49f350084d4740c86854ae9bc84dbc9796` — canonical Dart format gate failed.
- `76ba0de46821c405c62f0ee68d63f173cf1d8a03` — combined Product Preview shell lifecycle test remained brittle.
- `c353507b7ef0d1ef214535fe3d7db496957491cd` — split runtime/entrypoint tests required canonical formatting.
- `50edb8c4d2bae9514c2c2a3f613ee8e9d9aaeafe` — Case route test used the platform secure draft store in a widget-test environment.
- `21f3d385eb3cb6e35d6d5bc8c53703b82c96731f` — runtime scene passed but the test incorrectly asserted raw Turkish display text through a localization layer.
- `5a2e84940d7ac4cb997697168d5b7fa85011bd5e` — lazy ListView decision controls were asserted before being mounted.

Each failure was corrected at its actual source. No gate was weakened and no failed head was promoted.

## Phone artifact evidence

From Global Readiness #310 / run `30686665295`:

- artifact name: `kefe-internal-alpha-phone-preview`
- artifact ID: `8814220147`
- archive digest: `sha256:174008c0c4bb5dba1c1888a9e67650fd259bbc5e32af23baaebe0d45a8ac1429`
- runtime SHA: `eb7dbb2f85f5fa955040c5da60c6ab4c928e7da8`
- payload: `app-debug.apk`
- APK size: `160560670` bytes
- APK SHA-256: `6cec0c4e94417e38e8bdf59738de48f173984efcc754366b8d3b6125744db323`
- `beta-api.invalid`: NOT FOUND in raw APK
- `beta-api.invalid`: NOT FOUND in unpacked APK

This artifact is an isolated internal Product Preview candidate, not a production/public-beta/store release.

## Not claimed

Slice 21 does not claim:
- real event reconstruction or VAR evidence;
- adjudication correctness;
- player/referee/ball tracking;
- production media-provider readiness;
- human visual approval or usability PASS;
- Signal/Impact readiness;
- production OTP/provider/store/SLO/rollback readiness.

## Next

The Slice 17 high-fidelity visual adoption chain now has four materially visible verified surfaces: Signature Balance, Atlas World, qualitative Perspective Landscape and Sports CALL Scene. The next work should be selected from remaining primary-screen state/typography/spacing/accessibility/performance debt or architecture-pending non-visual priorities under a fresh audit and contract. A truly interactive Spatial CALL remains blocked on a separate typed spatial-evidence and provenance contract.
