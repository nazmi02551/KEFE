# KEFE UI + Localization Reality Audit — 2026-07-30

Status: Working evidence for PR #99 / Issue #98. This document does **not** promote a release or replace the canonical product baseline.

## Baseline authority

Engineering continuation stack at audit time:

`main → #90 → #92 → #94 → #95 → #97 → #99`

PR #97 retains the repo-verified Internal Alpha runtime checkpoint at:

`f7ab9b9d3db235bd9fdcc0c12950e5c181791018`

PR #99 is a stacked visual/localization continuation. It must earn fresh exact-head evidence before any new PASS claim.

## Real phone UI baseline

Human phone screenshots from the PR #97 Internal Alpha were compared directly with the current Flutter implementation. The screenshots are treated as baseline evidence. The premium dark mockups supplied alongside them are **directional references only**, not evidence of current implementation.

### Weigh hub

Current reality before PR #99:

- light-theme-dominant Material/card composition;
- dark gradient featured card inside light mode;
- featured title inherited the ambient light-theme foreground and became very low contrast on the dark gradient;
- remaining case cards were readable but visually generic compared with backend/runtime maturity.

### Decision flow

Current reality before PR #99:

- functionally correct generic Decision flow;
- simple CustomPaint scale visual;
- gray option tiles and standard Card hierarchy;
- confidence represented by ordinary chips;
- mixed English UI chrome with Turkish preview question/option content when English locale was selected.

### Context / sources

Current reality before PR #99:

- parent surface was a normal light card;
- inner information blocks used `surfaceElevatedDark` directly even in light mode;
- text inherited light-theme foreground, producing poor contrast on those dark blocks;
- preview content remained Turkish while English UI chrome could be active.

### Reveal / KEFE Gap

Current reality:

- Commit First / Blind First semantics are intact;
- distribution bars and methodology are functional;
- hierarchy remains basic and the KEFE Gap is still a simple inset surface;
- preview result option labels can remain in fixture language while UI chrome changes locale.

Advanced Reveal/KEFE Gap visualization is intentionally deferred from slice 1.

### Radar

Current reality:

- representative Product Preview ranking only, not live trend data;
- light card list with simple filter chips;
- visually coherent enough to demonstrate capability but still placeholder-like versus desired KEFE identity;
- preview chrome/content contains direct Turkish literals.

Premium Radar is intentionally deferred from slice 1; truthfulness must remain explicit.

### Atlas

Current reality:

- representative Product Preview values only, not real country outcomes;
- simple radial-gradient globe/icon hero and 0–10 country cards;
- capability is product-valid but visually reads as preview rather than a mature signature surface;
- preview chrome/country fixture labels contain direct Turkish literals.

Premium Atlas is intentionally deferred from slice 1; no globe-engine claim is authorized.

## Root mismatch

Runtime maturity exceeds visual maturity.

The backend/runtime already protects immutable CaseVersion, generic flow execution, Commit First, Blind First, preview/production isolation, PostgreSQL continuity and exact CI gates. The mobile presentation before PR #99 still relied on raw color constants and generic Material surfaces in several important places.

The highest-risk visual defect was not lack of decoration; it was **semantic theme mismatch**: dark-only surface tokens could be selected manually while foreground colors still came from a light ambient ThemeData.

## Localization debt

Two different concerns were previously conflated:

1. **UI chrome** — production presentation is already governed through `KefeStrings`/feature extensions and the PR #97 hardcoded-copy checker.
2. **preview/server-like content** — titles, summaries, questions, options, context blocks and result labels are domain content, not ordinary UI chrome. Product Preview fixtures were Turkish strings stored in preview repositories and were rendered directly regardless of selected UI locale.

PR #99 introduces a separate presentation-time `KefeContentLocalizer` boundary. Production defaults to pass-through localized/pinned content; Product Preview supplies a deterministic preview catalog. Display localization must never mutate raw decision values or CaseVersion identity.

The existing TR/EN getter implementation is still not the final multi-locale resource architecture. Slice 1 establishes the content/catalog boundary and regression tests; wider migration of legacy UI chrome to scalable locale resources remains explicit follow-up work and must not be falsely marked complete.

## Slice 1 implementation intent

ADR-0039 authorizes the Decision Journey Foundation only:

- semantic theme extension and reusable KEFE surfaces;
- Weigh hero/hierarchy;
- premium Case hero;
- generic signature binary balance;
- Decision / Confidence / Reasons hierarchy;
- Context/source contrast and hierarchy;
- shared FilledButton theme improves Commit CTA without changing Commit logic;
- Reduce Motion and screen-reader semantics;
- preview content localization for the migrated Decision Journey surfaces while preserving raw response values.

Deferred:

- advanced Reveal / Perspective Landscape;
- premium Radar;
- premium Atlas;
- full repository-wide locale-resource migration;
- production/store readiness.

## Invariants

PR #99 does not authorize changes to:

- Commit First;
- Blind First;
- immutable CaseVersion;
- case-agnostic runtime;
- preview/production repository isolation;
- preview fixtures as production fallback;
- My KEFE descriptive-only semantics;
- Signal/Impact scope;
- personality, ideology, psychometric, bias or causal inference.
