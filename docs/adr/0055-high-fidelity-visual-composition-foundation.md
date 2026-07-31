# ADR-0055 — High-Fidelity Visual Composition Foundation

Date: 2026-07-31
Status: Accepted for stacked implementation
Tracks: #129
Depends on: PR #128 / ADR-0054

## Context

The premium stack through Slice 16 has established theme-adaptive KEFE surfaces, localization, shared navigation, accessibility/Reduce Motion, trust/share/community presentation and a reusable Flutter-native balance visual. The mobile client also has a provider-neutral `CaseMediaRepository` seam with asset identity/content hash, exposure phase and rendition metadata.

That media seam is intentionally narrow today: `EXPLORE_CARD`, `CASE_HERO`, `CONTEXT_SUPPORTING` and Product Preview renderer `KEFE_ABSTRACT_V1`. It is sufficient for representative abstract illustrations, but not yet a complete foundation for the high-fidelity art direction represented by current concept references such as a signature scale hero, Atlas world scene, Perspective landscape or Spatial CALL scene.

Implementing those concepts directly as one-off screen artwork now would duplicate crop/loading/fallback/accessibility/performance logic, encourage Case-specific branching and make preview assets harder to isolate from production. The safer sequence is foundation first, then separate high-fidelity screen convergence slices.

The concept references are target art direction. They are not current runtime evidence, pixel-exact specifications, new data contracts or proof of human usability.

## Decision

Slice 17 establishes a reusable high-fidelity visual-composition layer on top of the existing KEFE design system and media presentation boundary.

Authorized architecture:

1. **Provider-neutral visual presentation**
   - presentation consumes versioned visual/media descriptors rather than vendor/CDN-specific URLs;
   - source/provider-specific asset resolution remains behind adapters;
   - preview fixture resolution remains isolated and can never become production fallback.

2. **Semantic composition slots**
   - extend the existing media-slot model only where current product surfaces require reusable visual scenes;
   - slots describe presentation role, not a Case subtype or product meaning;
   - CaseVersion/capability composition selects the visual presentation; screen code must not branch on named Cases.

3. **Deterministic rendition rules**
   - descriptors may define aspect ratio, focal point/crop intent, safe-area intent, theme suitability and fallback class;
   - asset identity and content hash remain pinned for reproducibility;
   - pre-Commit-safe and post-Commit-only exposure remain explicit and enforced.

4. **Hybrid rendering**
   - rich visual feel may use optimized pre-rendered/static assets for expensive art direction;
   - Flutter-native layers remain responsible for interactive controls, live labels, accessible data overlays and lightweight deterministic motion;
   - continuously rendered 3D, WebView or Three.js is not required and is excluded from this foundation.

5. **State and fallback contract**
   - visual compositions have deterministic loading, empty, unavailable/error and safe fallback states;
   - fallback must preserve core task completion and Blind First boundaries even when the high-fidelity asset is unavailable;
   - decorative media must never become the only carrier of decision/result meaning.

6. **Accessibility and motion**
   - every visual descriptor is explicitly decorative or semantic;
   - semantic media requires meaningful alternative text or an equivalent text-first representation;
   - Reduce Motion collapses nonessential transitions without hiding state or meaning.

7. **Performance budget**
   - low-end Android remains a first-class target;
   - implementation must define bounded decode/cache/memory behavior and avoid unbounded animation or scene work;
   - visual fidelity cannot block the generic decision path.

8. **Visual verification**
   - contract/source tests protect preview-production isolation and exposure rules;
   - theme/locale/text-scale/representative-phone visual regressions are required for governed components;
   - human phone review remains separate evidence and is never inferred from CI.

## Planned post-foundation sequence

After Slice 17 is repo-verified, high-fidelity vertical convergence should proceed initially in this order unless a fresh audit provides a stronger reason to reorder:

1. Weigh / signature Balance hero.
2. Atlas world/globe hero.
3. Perspective Landscape.
4. Spatial CALL scene.
5. Remaining primary-screen loading/empty/error/skeleton, typography and spacing convergence.

These later slices may replace or enrich the current lightweight representative visuals while keeping the same product/runtime semantics.

## Behavioral invariants

- Commit First remains unchanged.
- Blind First remains unchanged.
- Published CaseVersion remains immutable.
- Runtime remains case-agnostic and composition-driven.
- Raw backend/CaseVersion values are not altered by presentation/localization.
- No pre-Commit collective result, Perspective or other post-Commit information is introduced through media.
- My KEFE remains observed/descriptive only.
- Signal and Impact remain outside this slice.
- Preview fixtures are never production fallback.

## Explicit exclusions

This ADR does not authorize:

- a new question/result/Atlas/Perspective/CALL methodology or metric;
- a Case-specific feature family or hard-coded named-Case renderer;
- a live 3D globe/field engine, WebView or Three.js runtime;
- production CDN/media-provider readiness without separate implementation and evidence;
- automatic asset generation/publishing;
- personality, ideology, psychometric, bias or causal inference;
- store, production OTP/provider, production SLO or operator rollback claims;
- a claim that concept references are already implemented or human-usability approved.

## Documentation propagation

This ADR is an engineering working-layer decision. It does not change the constitutional product semantics in Master Product Document v1.3.0.

At the next declared documentation publication milestone, the accepted foundation must be synchronized into the existing logical documents rather than creating a new official document:

- **Design System**: scene/hero composition taxonomy, rendition/fallback/accessibility/performance/golden rules;
- **Engineering Blueprint**: provider-neutral asset resolution, caching/performance boundaries and test architecture;
- **Product Bible**: target art-direction/application pattern and screen-level adoption sequence;
- **MVP Delivery Plan** only if the delivery sequence or acceptance gates materially change.

CURRENT v3.4 is not superseded by this stacked working ADR.

## Verification

Runtime implementation requires an executable contract on the same candidate line. No Slice 17 repo-verified/PASS/APK claim is valid until API CI, Mobile CI, MVP Beta Gates and Global Readiness succeed on one exact runtime SHA with the applicable visual-contract, accessibility and performance regressions.