# ADR-0054 — Premium First-Use Journey Visual Convergence

Date: 2026-07-31
Status: Accepted for stacked implementation; amended after phone-preview reachability finding
Tracks: #127

## Context

The verified premium slices have improved core decision, Reveal, Perspective, Radar, Atlas, localization, Activity/My KEFE, shell, trust controls, sharing and post-Commit social participation. The first-use entry remains visually behind that system: onboarding still uses plain text, generic theme colors and a continuous loading spinner, while the first-Reveal completion surface remains a generic Card.

Because this is the first experience a new user sees, the remaining mismatch materially weakens the perceived product quality even though the underlying flow is already correct.

## Decision

Slice 16 is a presentation-only convergence of the existing first-use journey.

Authorized runtime scope:

- `OnboardingGateScreen` loading state, two existing promise pages, page progress affordance and primary CTA presentation;
- the existing first-use completion surface shown after the first Reveal and before continuing to Explore;
- shared theme-adaptive KEFE semantic surfaces and existing visual tokens;
- deterministic, non-continuous loading presentation;
- Reduce Motion-aware page/progress motion;
- TR/EN light/dark and accessibility regression coverage.

## Behavioral invariants

The slice must preserve all of the following:

1. The onboarding flow contains exactly the same two promise pages and the same localized wording.
2. `onboarding-pages`, `onboarding-promise-1`, `onboarding-promise-2`, `onboarding-primary-button`, `first-use-completion` and `continue-as-guest` remain stable interaction keys/semantics.
3. Page one advances to page two; page two still opens the existing demo Case with `firstUse=1`.
4. The first real Case is not fetched before the user advances through the two promises.
5. Onboarding completion remains persisted by the existing Decision flow only after the first Reveal transition.
6. Continue-as-guest still routes to `/explore`.
7. No authentication requirement or account coercion is introduced.
8. Commit First, Blind First, immutable CaseVersion, case-agnostic generic runtime and preview/production isolation remain unchanged.

## Phone-preview reachability finding

The first repo-verified Slice 16 runtime (`86b75bb621b866770371f34500a2fc7148bac484`) changed the production `OnboardingGateScreen` and first-use completion presentation, but the distributed `kefe-internal-alpha-phone-preview` artifact is built from `main_preview.dart` / `ProductPreviewApp`. That preview composition intentionally started at `/explore` and did not define a `/welcome` route. Therefore the visual work was not reachable from the distributed phone-preview artifact even after app-data clearing.

The CI evidence on that runtime remains valid for the code it exercised, but that runtime must not be treated as a sufficient human first-use visual-review checkpoint.

## Amendment — preview-only first-use review path

Slice 16 may add a Product Preview-only review path so the governed first-use presentation can be exercised on the same internal phone artifact without altering production onboarding semantics.

Authorized amendment:

- `ProductPreviewApp` keeps its normal initial location at `/explore` so existing preview navigation and repeated test workflows are not disrupted.
- Product Preview adds `/welcome?review=1`, rendered by the same `OnboardingGateScreen` in explicit review mode.
- Explore exposes one secondary Product Preview action with stable key `open-preview-first-use` that opens the review route.
- Review mode bypasses only the persisted-completion gate; it does not add, remove or reorder onboarding promises.
- `main_preview.dart` supplies an in-memory onboarding store so review activity cannot mutate production/shared onboarding persistence.
- Product Preview Case routing preserves the existing `firstUse=1` query so the first-Reveal completion surface is reachable in the review journey.
- Production `main.dart`, production `KefeApp` routing and default `OnboardingGateScreen` behavior remain unchanged.

The amendment is preview tooling, not a new product onboarding route or a production replay feature.

## Explicit exclusions

This ADR does not authorize:

- a third onboarding page, new onboarding product claim or altered onboarding copy;
- a different demo Case or Case-selection policy;
- backend, API or schema changes;
- production route changes or a production onboarding replay control;
- pre-Commit collective/result information;
- Signal or Impact expansion;
- personality, ideology, psychometric, bias or causal inference;
- production/store/provider/SLO/operator-rollback readiness claims;
- a human real-device usability PASS claim from automated evidence.

## Verification

A corrected Slice 16 phone checkpoint is acceptable only when:

- the v2 executable contract and runtime are on the same candidate line;
- production-path regression proves the default persisted onboarding behavior is unchanged;
- Product Preview regression proves `open-preview-first-use` reaches the two promise pages without relying on persisted production state;
- Product Preview Case routing preserves `firstUse=1` and exposes the existing first-Reveal completion surface;
- API CI, Mobile CI, MVP Beta Gates and Global Readiness succeed on the same exact runtime SHA;
- the phone artifact is produced from that exact verified SHA.
