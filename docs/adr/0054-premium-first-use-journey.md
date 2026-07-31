# ADR-0054 — Premium First-Use Journey Visual Convergence

Date: 2026-07-31
Status: Accepted for stacked implementation
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

## Explicit exclusions

This ADR does not authorize:

- a third onboarding page, new onboarding product claim or altered onboarding copy;
- a different demo Case or Case-selection policy;
- backend, API, schema, route or controller changes;
- pre-Commit collective/result information;
- Signal or Impact expansion;
- personality, ideology, psychometric, bias or causal inference;
- production/store/provider/SLO/operator-rollback readiness claims;
- a human real-device usability PASS claim from automated evidence.

## Verification

A Slice 16 checkpoint is acceptable only when the executable contract and runtime are on the same candidate line and API CI, Mobile CI, MVP Beta Gates and Global Readiness succeed on the same exact runtime SHA. APK evidence is produced only for that meaningful exact-head checkpoint.
