# ADR-0034 — Mobile Discovery, Activity Continuity and APK Promotion

- Status: Accepted
- Date: 2026-07-30
- Extends: ADR-0030, ADR-0032, ADR-0033
- Tracks: Issue #89
- Product authority: KEFE Documentation Ecosystem v3.4 CURRENT
  - Master Product Document v1.3.0
  - Product Bible v1.5.0
  - Documentation Governance v1.5.0
  - Analytics Event Dictionary v1.2.0

## Context

The Product Preview has reached a useful multi-screen baseline, but recent phone-test versions were promoted after narrow implementation slices. Continuous APK generation remains valuable as CI evidence, yet presenting every internal artifact as a new numbered user build creates release noise and makes version numbers less meaningful.

The Drive v3.4 canonical product documents define four primary consumer destinations: Explore, Weigh, Activity and My KEFE. Search belongs inside Explore; Activity owns decision-history and return-later continuity; My KEFE remains a descriptive progress and insight surface. Radar and Atlas are supporting product capabilities, not separate primary navigation destinations.

The next milestone should materially improve how a person finds a relevant Case and returns to it later while correcting the Product Preview shell to the canonical navigation model. Search, domain filtering, saved Cases and Activity continuity form one coherent user journey and can be shared by production and Product Preview without changing Commit-before-Reveal or introducing preview fallback.

## Decision

### 1. CI artifact generation and APK promotion are separate

Mobile CI may continue to generate an Android artifact for every relevant branch or main build. A numbered phone-test APK is promoted to the user only after a milestone acceptance gate is complete.

The next promoted version is v9. Documentation-only, navigation-only or single-control changes do not independently justify a new numbered APK.

### 2. v9 is the Discovery, Activity and Continuity milestone

The milestone contains all of the following:

1. client-side Explore search across the currently fetched Case title and summary;
2. domain filtering with an explicit All state, reset behavior and no-result presentation;
3. save and unsave actions on Explore Case cards;
4. durable device-local saved-Case storage;
5. a saved-Cases continuation surface in Activity;
6. recent committed-decision continuity in Activity;
7. saved and historical Case navigation through the canonical `/case/:caseId` route;
8. one shared four-tab shell: Explore, Weigh, Activity and My KEFE;
9. Radar and Atlas remain secondary surfaces and are not primary tabs;
10. shared production/Product Preview implementation with no preview fallback;
11. accessibility semantics, privacy-safe analytics schema, store tests and widget coverage.

### 3. Saved Case identity is CaseVersion-pinned

A saved entry stores a small presentation snapshot:

- Case id;
- CaseVersion id;
- title and summary;
- domain, format and risk;
- saved timestamp.

The snapshot supports device-local continuity presentation and is never Claim truth or publication authority. Opening the saved entry still resolves the canonical Case route and runtime.

### 4. Storage is device-local and actor-neutral in this slice

Saved Cases use a dedicated `SavedCaseStore` backed by SharedPreferences in production and an injectable memory implementation in tests. This slice does not claim account synchronization, cross-device persistence or server-side recommendation behavior.

Saved Cases are not private rationale, ideology, psychometric data or a behavioral profile. They must not be used for targeting or sensitive inference.

### 5. Search and filters are presentation concerns

Search and domain filters operate over the currently fetched Explore collection. They do not alter API contracts, ranking authority, publication status or Case semantics. Server-side search, pagination and ranking remain deferred.

The analytics schema may record only bounded metadata such as query-length and result-count buckets. Raw query text, Case title/summary and private rationale are forbidden.

### 6. Activity and My KEFE have separate responsibilities

Activity owns saved Cases, recent committed decisions, revision markers and Reflection completion markers. Saving a Case does not count as a weigh, revisit or Reflection.

My KEFE remains a descriptive progress and insight surface. It may show observed counts and domain activity but does not host saved-Case continuity and does not infer personality, ideology, psychometrics or causality.

### 7. Navigation is canonical and shared

Production and Product Preview use the same four primary destinations and shell boundary:

1. Explore;
2. Weigh;
3. Activity;
4. My KEFE.

Product Preview may expose Radar and Atlas through clearly secondary controls for evaluation. Production does not expose preview-only Radar or Atlas data.

## Analytics contract

`docs/contracts/mobile-discovery-analytics.v1.yaml` defines the versioned event vocabulary for search, filters, save/unsave, Activity opening and saved-Case continuation. A provider-neutral delivery adapter is deferred, but no non-noop analytics delivery may be added without schema validation and the stated privacy constraints.

## APK promotion gate

v9 is promoted only when:

- all eleven milestone capabilities are complete;
- Mobile CI analysis, tests and Android build pass;
- production preview-isolation checks pass;
- the Drive v3.4 alignment checkpoint and phone-test checklist are recorded;
- the resulting artifact identity and SHA-256 are captured.

Until then, generated artifacts remain internal CI outputs and are not presented as a new numbered APK.

## Deferred

- server-synchronized saved Cases;
- account migration and cross-device restore;
- server-side search, pagination and ranking;
- personalized recommendations or targeting;
- notifications for saved Cases;
- production Radar and Atlas data contracts;
- non-noop analytics delivery infrastructure;
- consensus-card participation, which requires its own product and methodology contract.

## Consequences

- release versions represent meaningful user-visible milestones;
- CI remains frequent without forcing frequent public APK delivery;
- users can find and resume Cases with durable device-local continuity;
- Activity becomes the canonical place for return-later and decision-history behavior;
- My KEFE remains methodologically clean and descriptive;
- Product Preview no longer carries a competing primary navigation model;
- future consensus-card work remains explicitly separate and can later require a completed weigh before participation.
