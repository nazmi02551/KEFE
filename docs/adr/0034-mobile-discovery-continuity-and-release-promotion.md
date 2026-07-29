# ADR-0034 — Mobile Discovery, Saved-Case Continuity and APK Promotion

- Status: Accepted
- Date: 2026-07-30
- Extends: ADR-0030, ADR-0032, ADR-0033
- Tracks: Issue #89

## Context

The Product Preview has reached a useful multi-screen baseline, but recent phone-test versions were promoted after narrow implementation slices. Continuous APK generation remains valuable as CI evidence, yet presenting every internal artifact as a new numbered user build creates release noise and makes version numbers less meaningful.

The next milestone should materially improve how a person finds a relevant Case and returns to it later. Search, domain filtering and saved Cases form one coherent user journey and can be shared by production and Product Preview without changing Commit-before-Reveal or introducing preview fallback.

## Decision

### 1. CI artifact generation and APK promotion are separate

Mobile CI may continue to generate an Android artifact for every relevant branch or main build. A numbered phone-test APK is promoted to the user only after a milestone acceptance gate is complete.

The next promoted version is v9. Documentation-only, navigation-only or single-control changes do not independently justify a new numbered APK.

### 2. v9 is the Discovery and Continuity milestone

The milestone contains all of the following:

1. client-side Explore search across the currently fetched Case title and summary;
2. domain filtering with an explicit All state, reset behavior and no-result presentation;
3. save and unsave actions on Explore Case cards;
4. durable device-local saved-Case storage;
5. a saved-Cases continuation surface in My KEFE;
6. saved Case navigation through the canonical `/case/:caseId` route;
7. shared production/Product Preview implementation with no preview fallback;
8. accessibility semantics plus store and widget coverage.

### 3. Saved Case identity is CaseVersion-pinned

A saved entry stores a small presentation snapshot:

- Case id;
- CaseVersion id;
- title and summary;
- domain, format and risk;
- saved timestamp.

The snapshot supports offline continuity presentation and is never Claim truth or publication authority. Opening the saved entry still resolves the canonical Case route and runtime.

### 4. Storage is device-local and actor-neutral in this slice

Saved Cases use a dedicated `SavedCaseStore` backed by SharedPreferences in production and an injectable memory implementation in tests. This slice does not claim account synchronization, cross-device persistence or server-side recommendation behavior.

Saved Cases are not private rationale, ideology, psychometric data or a behavioral profile. They must not be used for targeting or sensitive inference.

### 5. Search and filters are presentation concerns

Search and domain filters operate over the currently fetched Explore collection. They do not alter API contracts, ranking authority, publication status or Case semantics. Server-side search, pagination and ranking remain deferred.

### 6. My KEFE remains descriptive

The saved-Cases continuation section is visually separate from the observed decision-journey metrics. Saving a Case does not count as a weigh, revisit or reflection and does not change readiness metrics.

## APK promotion gate

v9 is promoted only when:

- all eight milestone capabilities are complete;
- Mobile CI analysis, tests and Android build pass;
- production preview-isolation checks pass;
- the durable engineering checkpoint and phone-test checklist are recorded;
- the resulting artifact identity and SHA-256 are captured.

Until then, generated artifacts remain internal CI outputs and are not presented as a new numbered APK.

## Deferred

- server-synchronized saved Cases;
- account migration and cross-device restore;
- server-side search, pagination and ranking;
- personalized recommendations or targeting;
- notifications for saved Cases;
- consensus-card participation, which requires its own product and methodology contract.

## Consequences

- release versions represent meaningful user-visible milestones;
- CI remains frequent without forcing frequent public APK delivery;
- users can find and resume Cases with durable device-local continuity;
- My KEFE gains a practical continuation function without contaminating decision-history semantics;
- future consensus-card work remains explicitly separate and can later require a completed weigh before participation.