# MVP Dilemma Discovery — 2026-08-24

Status: DRAFT CANDIDATE / NO CAPABILITY PROMOTION

Issue: #371

Capabilities: CAP-015 (primary), CAP-095 (supporting)

Stack base: PR #370 / `feature/mvp-account-continuity-discovery` exact-green head `77a909c85e6b442dcac22968ea0e78cde680b023`.

## Why this slice exists

The horizontal-first MVP delivery strategy requires KEFE's principal consumer experiences to become directly demonstrable before another long hardening sequence. The canonical MVP product authority includes low-risk DILEMMA as a primary entry format, while the current experience hub exposed the general catalog, community participation, Sports CALL and bounded Atlas/Radar states but no first-class Dilemma entry.

## Delivered boundary

The existing KEFE Experiences hub now:

- discovers an actual Case only when its exact runtime `format` is `DILEMMA`;
- presents localized EN/TR Dilemma copy;
- displays the selected Case title so the lane is grounded in repository/runtime content;
- enters the existing `/case/:caseId` journey rather than creating a Dilemma-specific engine;
- preserves Blind First and Commit First because Result/participation surfaces remain behind the canonical Case journey;
- shows a truthful non-actionable empty state when no Dilemma is published;
- keeps Sports CALL, community participation, Radar/Atlas Preview boundaries and the general Explore catalog unchanged.

No backend, API, OpenAPI, schema, migration, Case model, Flow engine, fixture or analytics behavior changes in this slice.

## Stack convergence recovery

The historical PR #372 head `69c146380ab29b200ab4057c33b09f077189c129`
remains audit evidence on the pre-convergence PR #370 head `738aa0ee…`. The
candidate is rebuilt on the exact-green parent with only this slice's five owned
files.

The existing Experience Hub regression had advanced in the parent to explicit
persisted Turkish preferences, lazy-card reveal helpers and scoped card actions.
The Dilemma assertions are composed into those helpers instead of restoring the
historical global text/viewport assumptions. No parallel Case or Dilemma runtime
is introduced.

## KEFE Today truthfulness boundary

This slice deliberately does **not** infer KEFE Today from `format=CIVIC`, domain, risk or list order.

The current mobile `DecisionCaseSummary` exposes Case id/version, title, summary, format, domain and risk, but no trusted current-event/source/freshness discriminator. A Civic Case is not necessarily a current real-world event, and a current real-world Case is not necessarily Civic.

Therefore KEFE Today remains separate follow-up work that must first establish a trustworthy runtime classification/projection. No fake Today fixture or presentation claim is introduced merely to fill the MVP surface.

## Focused regression intent

`apps/mobile/test/experience_hub_test.dart` now checks that Product Preview:

- exposes the Dilemma lane from its existing real `format=DILEMMA` fixture;
- shows the actual selected Case title;
- enters the canonical Case screen through the Dilemma CTA;
- still has Commit available before post-Commit journey content;
- preserves existing community, Sports CALL and truthful production Atlas expectations.

## Evidence boundary

The consolidated `22962c06c6f9601bdc1ca89a84038e6babc68c27` candidate
reached PASS for formatting, analysis and the mobile regression suites in Mobile
CI, MVP Beta Gates and Global Readiness. Its Android compile/build steps were
still running when the final evidence-only commit was prepared.

The final commit changes no runtime behavior. It adds an explicit regression
intent comment and touches the existing API consolidation validator so API CI,
Mobile CI, MVP Beta Gates and Global Readiness execute against one exact SHA.
Those final runs remain required before any exact-head PASS or APK claim.

No claim is made for human usability approval, deployed Connected Alpha behavior, store readiness, production reachability, KEFE Today implementation or capability lifecycle promotion.
