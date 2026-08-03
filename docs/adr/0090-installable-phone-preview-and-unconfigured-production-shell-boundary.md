# ADR-0090 — Installable phone preview and unconfigured production shell boundary

- Status: Accepted
- Date: 2026-08-03
- Decision owners: Product, Mobile, Platform

## Context

KEFE currently produces two Android builds in CI:

1. a production-entry compile candidate from `lib/main.dart`; and
2. an internal phone preview from `lib/main_preview.dart`.

The production-entry candidate is intentionally compiled with the placeholder endpoint `https://beta-api.invalid/` because no deployed beta API has been approved or configured. Uploading that APK with a user-installable-looking artifact name allowed it to be mistaken for the phone preview. A user could complete the locally rendered onboarding interaction, but the first commit/reveal network operation necessarily failed.

The preview application also used the production `SecureDecisionDraftStore`. Installing a preview over a previous production-entry debug build could therefore expose the preview runtime to a stale production draft, even though preview repositories themselves remained isolated.

## Decision

### 1. Exactly one installable phone-test artifact

While no real beta API endpoint is configured, the only APK published for installation is the explicit preview build from `lib/main_preview.dart`.

Its workflow artifact name is `kefe-installable-phone-preview`, and the APK filename includes `KEFE-phone-preview` plus the exact candidate SHA.

### 2. Production-entry build remains compile proof only

CI continues compiling `lib/main.dart` with the placeholder endpoint so production-entry compilation remains covered. The resulting APK is not uploaded and must not be presented as an installable candidate.

This does not authorize the placeholder endpoint for runtime use and does not claim a deployed beta backend.

### 3. Preview draft state is process-local

`main_preview.dart` must override `decisionDraftStoreProvider` with `MemoryDecisionDraftStore`.

Preview state therefore cannot read or mutate secure production decision drafts. This is an explicit preview-only composition rule; production composition continues using `SecureDecisionDraftStore`.

### 4. No preview fallback in production

Production `main.dart` must not import or register preview repositories, preview stores, or preview application composition. A missing or invalid production endpoint is a configuration/deployment problem, not a reason to fall back to preview fixtures.

### 5. Executable artifact-boundary gate

CI must fail if any of the following occurs:

- the unconfigured production shell APK is uploaded;
- the installable artifact does not build from `main_preview.dart`;
- the installable artifact name or APK filename becomes ambiguous;
- preview composition stops overriding the decision draft store with memory storage;
- production composition imports preview implementations.

## Consequences

- Phone testers receive a working, clearly identified local preview APK.
- Production compile coverage remains intact without creating a misleading downloadable package.
- Existing production/preview isolation is strengthened.
- A real network-backed beta APK remains blocked until an approved endpoint and deployment evidence exist.

## Non-goals

This ADR does not deploy an API, approve a provider, create production credentials, change Commit First / Blind First semantics, or authorize preview fixtures as production fallback.
