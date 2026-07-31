# KEFE Signature Balance Hero Convergence — Slice 18

Date: 2026-07-31  
Status: REPO_VERIFIED / HUMAN_VISUAL_USABILITY_PENDING  
Issue: #137  
PR: #138  
ADR: ADR-0056  
Executable contract: `docs/contracts/signature-balance-hero-slice18.v1.json`

## Verified runtime

Exact runtime SHA:
`1035b769bcbd7059cc84a9680ef62f0113cc32e3`

Any later documentation-only commit on PR #138 must not redefine this verified runtime.

## Exact-head CI evidence

All four required workflows completed successfully on the exact same runtime SHA:

- API CI #852 — run `30659612084` — SUCCESS
- Mobile CI #650 — run `30659612079` — SUCCESS
- MVP Beta Gates #356 — run `30659612086` — SUCCESS
- Global Readiness #262 — run `30659612104` — SUCCESS

Verified gates include canonical Dart formatting, analyzer, full Flutter regressions, production-copy boundary, phone acceptance, generic runtime/API contracts, PostgreSQL MVP/global regressions and Android candidate builds.

## What Slice 18 implemented

### Generic two-option Signature Balance
The existing shared `KefeBalanceVisual` now renders a materially richer dimensional KEFE balance for the existing generic `SINGLE_CHOICE` question capability when exactly two canonical options exist.

Eligibility remains capability-driven. No Case ID, Case title or domain-specific branch was introduced.

### Truthfulness preserved
The hero has only three states:
- neutral;
- left option selected;
- right option selected.

The visual tilt/highlight reflects only the current user's own binary selection. No percentage, continuous coordinate, community distribution, consensus, Signal or Impact value is invented.

Canonical raw option values continue to be emitted through the existing explicit option controls unchanged.

### Visual treatment
The lightweight Flutter-native renderer now provides:
- layered metallic/gold pedestal and base;
- pivot medallion and crown detail;
- curved gold beam;
- chains and dimensional pans;
- Rules/Rights cyan treatment on the left;
- Empathy/Compassion warm treatment on the right;
- deterministic ambient glow/depth;
- selected-side emphasis;
- shared KEFE theme roles for dark/light validity.

No WebView, Three.js, mandatory live 3D or continuous particle/shader loop was introduced.

### Accessibility / motion / layout
- explicit option tiles remain the actual input controls;
- hero remains semantic visual feedback, not the sole control;
- Reduce Motion collapses the governed selection transition to zero;
- narrow layout remains compact;
- short decision viewports (<700 logical px) request the compact hero so existing option controls remain reachable without regressing the established phone flow;
- normal modern phone viewports retain the larger signature hero.

### Product Preview reachability
The existing Product Preview decision journey now proves the production Signature Balance widget is reachable before Commit on the real preview airline Case path:

Weigh → airline Case → Signature Balance neutral → select `Evet` → left-selected hero → Commit.

Reveal remains absent before Commit.

## Rejected candidates

These candidates are deliberately not accepted:

- `9e1e7ba098055f2530bde99b524bdfc32a4f0205` — Mobile CI analyzer failed due an unused `dart:math` import and invalid semantics finder argument; formatting also needed normalization.
- `08c173310b5ee1192eb3f9dff36066eba1d7dc91` — format/analyzer passed, but full regressions exposed a real compact-viewport UX regression: the taller hero pushed existing option controls below the 600px test viewport in Perspective/onboarding/flow journeys.

The final solution did not weaken tests. It made the product layout compact on short decision viewports.

## Phone artifact evidence

From Global Readiness #262 / run `30659612104`:

- artifact name: `kefe-internal-alpha-phone-preview`
- artifact ID: `8804739690`
- archive digest: `sha256:1d698475dea6ba262ca54c1ae0bafb2c605e8e4566ad185df73d62bf7601f239`
- runtime SHA: `1035b769bcbd7059cc84a9680ef62f0113cc32e3`
- payload: `app-debug.apk`
- APK size: `160529090` bytes
- APK SHA-256: `93ce2c5ffb9e07f787749e10218284b75283cf891e8a0fbaf37a9d66d7cb406f`
- `beta-api.invalid`: NOT FOUND in raw APK
- `beta-api.invalid`: NOT FOUND in unpacked APK

This artifact is an isolated internal Product Preview candidate, not a production/public-beta/store release.

## Not claimed

Slice 18 does not claim:
- pixel-exact reproduction of the concept artwork;
- human visual approval or human usability PASS;
- new decision methodology;
- continuous/percentage semantics for binary choices;
- Signal/Impact readiness;
- production OTP/provider/store/SLO/rollback readiness.

## Next visual slice

With the Signature Balance adoption verified, the planned next high-fidelity adoption is **Atlas World / Globe Convergence**, reusing Slice 17 composition/fallback/accessibility/performance rules and keeping Atlas methodology/data truthfulness separate from art direction.
