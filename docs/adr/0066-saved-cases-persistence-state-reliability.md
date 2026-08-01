# ADR-0066 — Saved Cases Persistence-State Reliability

Date: 2026-08-01  
Status: Accepted for Slice 28 implementation  
Tracker: #164  
Stack parent: `feature/activity-history-convergence-slice27`

## Context

`SavedCasesController` already exposes distinct idle, loading, ready and error states and preserves the last known items while loading or after a read failure.

The current `SavedCasesSection` does not represent that contract truthfully:

- first-load loading uses an indeterminate `LinearProgressIndicator`;
- error with no items falls through to the successful empty-state message;
- error or refresh with existing items has no status disclosure;
- users cannot retry a failed read from the section.

## Decision

Slice 28 adds a feature-local deterministic Saved Cases state surface and updates the section's state composition.

### State rules

- Idle/loading with no items renders `saved-cases-loading`.
- Loading with existing items keeps those items visible and renders the same non-blocking loading disclosure above them.
- Error with no items renders `saved-cases-error` and `saved-cases-retry`; it must not render `saved-cases-empty`.
- Error with existing items keeps those items visible and renders the retryable error disclosure above them.
- Ready with zero items alone renders `saved-cases-empty`.
- Ready with items renders the existing tiles.

The loading surface contains no progress percentage, indeterminate spinner or continuously animated decoration. Retry invokes only `SavedCasesController.load()`.

### Localization

The existing Saved Cases catalog gains governed English and Turkish resources for loading, unavailable and retry copy. Display-time Case title and summary localization remains unchanged.

## Preserved behavior

Slice 28 does not change:

- `SavedCasesController` state machine or duplicate-load guard;
- `SavedCaseStore` interface, persistence key or serialized format;
- optimistic `toggle` and `remove` behavior;
- write-failure recovery through the existing load path;
- saved-item ordering or deduplication;
- open/remove routes and actions;
- visibility-triggered loading;
- display-time Case title/summary localization;
- production/Product Preview isolation;
- API, schema or migrations;
- Commit First, Blind First or immutable CaseVersion;
- My KEFE/Activity non-inference boundaries;
- Signal/Impact boundaries.

## Accessibility and layout

The state surface must provide live-region announcements, exclude decorative icons from independent semantics and support light/dark themes, 360 × 800 viewport and 1.6× text scale.

## Rejected alternatives

### Treat persistence failure as empty

Rejected. Failure to read saved data is not evidence that the user has no saved Cases.

### Hide stale items during refresh/failure

Rejected. The controller intentionally preserves last known items; presentation should not discard truthful local continuity.

### Change controller/store semantics

Rejected. The existing domain/application contract is sufficient; the defect is presentation-state handling.

## Verification

Before PASS, one exact runtime SHA must pass API CI, Mobile CI, MVP Beta Gates and Global Readiness. Coverage must include first-load loading, ready-empty, error-empty, retry, stale-items loading/error continuity, localization, existing open/remove behavior and compact/enlarged-text theme regressions.

Human usability, editorial, production provider/SLO, store and rollback evidence remain external.