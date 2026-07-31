# KEFE Atlas World / Globe Convergence — Slice 19

Date: 2026-07-31  
Status: REPO_VERIFIED / HUMAN_VISUAL_USABILITY_PENDING  
Issue: #140  
PR: #141  
ADR: ADR-0057  
Executable contract: `docs/contracts/atlas-world-globe-slice19.v1.json`

## Verified runtime

Exact runtime SHA:
`db514fe61768f0a3cf7b0c4fe1ac4fa525be9edc`

Any later documentation-only commit on PR #141 must not redefine this verified runtime.

## Exact-head CI evidence

All four required workflows completed successfully on the exact same runtime SHA:

- API CI #872 — run `30662660008` — SUCCESS
- Mobile CI #669 — run `30662659924` — SUCCESS
- MVP Beta Gates #376 — run `30662659905` — SUCCESS
- Global Readiness #281 — run `30662659954` — SUCCESS

The exact-head gates include canonical formatting, analyzer, complete Flutter regressions, production-copy boundary, phone acceptance, API/generic-runtime contracts, PostgreSQL MVP/global regressions and Android candidate builds.

## What Slice 19 implemented

### Premium Preview Atlas globe
The existing secondary Product Preview Atlas now uses a dedicated lightweight Flutter-native `AtlasGlobeVisual` with:
- dimensional sphere and atmosphere treatment;
- deterministic graticule and abstract landmasses;
- deterministic orbit/network lines;
- country markers using the existing representative 0–10 fixture values;
- theme-adaptive KEFE Rules/Rights, gold and Empathy/Compassion visual roles;
- no idle continuous animation, WebView, Three.js or mandatory live 3D engine.

Atlas remains Preview-only at `/atlas`; no production route or primary-navigation promotion was introduced.

### Truthfulness preserved
The existing Atlas fixture remains representative Product Preview data only, not real country analytics.

No sample size, percentage split, confidence, weighting, date range, live-update timestamp, national representativeness, causal country explanation, Signal or authority claim was introduced.

The visible representative-data notice remains part of the governed Atlas experience.

### Single source for marker values
During review, globe marker values were found duplicated separately from the country-card fixture. Before acceptance, Slice 19 moved presentation marker coordinates into `AtlasPreviewFixture.countries` and now derives globe marker country code, value and position from that single fixture source.

The executable contract and test suite now forbid duplicate globe value constants and assert globe-marker value parity with `AtlasPreviewFixture.countries`.

Existing representative values remain unchanged:
- TR 7.1
- DE 5.4
- US 6.2
- JP 4.8
- BR 6.7
- ID 7.3

### Accessibility / layout
The complete country cards remain the text-accessible representation of Atlas values; decorative globe geometry is excluded from semantics.

The final runtime also closes real enlarged-text defects found by CI:
- at high text scale the decorative “world view” divider treatment collapses to a centered text treatment instead of overflowing horizontally;
- one-column country cards receive sufficient main-axis height under enlarged text;
- narrow phone layout keeps the 218px compact globe;
- 1.6× text-scale regression coverage verifies that the truth notice, globe and country cards remain usable/reachable without RenderFlex overflow.

### Product Preview reachability
The secondary Atlas action remains directly reachable in Product Preview and the governed route exposes:
Preview action → `/atlas` → representative-data notice → selected Case → globe → country cards.

Production continues to omit the `/atlas` route.

## Rejected / corrected candidates

No PASS claim attaches to intermediate candidates:

- `beee613f7b4e76eb73de041bf931b36fff13e29d` — MVP canonical Dart formatting gate failed; canonical formatter output was applied instead of weakening the gate.
- `c70d3ba979d9e3a2fd3757755e68a8c75b1d04f9` — format/analyzer/API/PostgreSQL were healthy, but mobile regressions exposed a stale Slice 5 source guard plus brittle locale/lazy-list assumptions in the new test harness. Those test assumptions were corrected to the actual extracted globe-renderer architecture and supported locale setup.
- `4da9eb112098ec919c4796f4dcd3d9aedb6327e3` — the strengthened tests then exposed genuine 1.6× text-scale overflows and one scroll-lifecycle assertion error. The runtime layout was fixed for enlarged text and globe-marker assertions were scoped to the globe-visible state; tests were not weakened around the actual overflow.

## Phone artifact evidence

From Global Readiness #281 / run `30662659954`:

- artifact name: `kefe-internal-alpha-phone-preview`
- artifact ID: `8805865777`
- archive digest: `sha256:22a8398227c94e7b4ed98ab72c3fe1e6f220f806131d7f07a4f35b5b80c26f1a`
- runtime SHA: `db514fe61768f0a3cf7b0c4fe1ac4fa525be9edc`
- payload: `app-debug.apk`
- APK size: `160536866` bytes
- APK SHA-256: `2c394ba66269f178c74dc95cad8cd42e36d9bffa89060f55eb9d82f5d33332ee`
- `beta-api.invalid`: NOT FOUND in raw APK
- `beta-api.invalid`: NOT FOUND in unpacked APK

This artifact is an isolated internal Product Preview candidate, not a production/public-beta/store release.

## Not claimed

Slice 19 does not claim:
- real or nationally representative country results;
- validated cross-country methodology;
- live Atlas data;
- Signal/Impact readiness;
- production Atlas readiness;
- human visual approval or human usability PASS;
- production OTP/provider/store/SLO/rollback readiness.

## Next visual slice

With the Signature Balance and Atlas World adoptions repo-verified, the planned next high-fidelity adoption is **Perspective Landscape Convergence**, reusing the Slice 17 visual-composition foundation while preserving post-Commit Perspective methodology and all non-inference boundaries.
