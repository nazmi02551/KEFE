# ADR-0139 — Saved Case lifecycle updates in Activity

Status: IMPLEMENTATION CANDIDATE  
Date: 2026-08-30  
Issue: #389  
Capability: CAP-079  
Parent: PR #388 / `9e4f5bcf24fd75dd0897529d5c5ea66486f08ae2`

## Context

KEFE already lets a person save a Case as a device-local, CaseVersion-pinned
presentation snapshot and resume it from Activity. The snapshot is truthful
offline continuity, but it cannot currently tell the person that the canonical
published Case has moved to another version. CAP-079 therefore remains partial.

This gap does not require a push provider, background process or account-level
notification store. Activity already owns saved-Case continuity, and the
canonical Explore collection already returns the current published CaseVersion
identity needed for a bounded foreground comparison.

## Decision

Activity checks saved snapshots against a successfully fetched canonical
Explore collection. A saved Case has a foreground lifecycle update only when:

- the catalog contains the same exact Case id; and
- its current `case_version_id` differs from the stored snapshot version.

The update is presentation state, not a persisted notification object. Activity
shows an update count and a localized update marker on the affected saved Case.
Opening that Case continues through `/case/:caseId` and acknowledges the
observed version by replacing the saved presentation snapshot with the current
catalog summary while preserving the original `saved_at` value.

The existing SharedPreferences payload remains backward compatible. No key,
schema version or migration changes. Existing entries already contain every
field required for comparison and acknowledgement.

## Truthfulness and failure behavior

Only a successful foreground catalog response can create an update marker.
Catalog loading, failure or absence of a saved Case is unknown state. It must
not be described as deletion, unpublication or an update and must not remove or
rewrite the saved snapshot. Existing saved entries remain usable when the
catalog cannot be refreshed.

The comparison is identity-only. It does not interpret why editorial content
changed, calculate importance or rank Cases. It performs no background polling.

## User experience

Activity remains the sole primary surface for saved-Case continuity. The shared
production/Product Preview implementation provides:

- a bounded update count in the Saved Cases header;
- a clear update marker and current-Case action per changed entry;
- Turkish and English copy, semantic disclosure and theme-adaptive visuals;
- compact-phone and enlarged-text support;
- pull-to-refresh of progress, saved snapshots and the foreground catalog.

Explore save/unsave, saved-only filtering and the canonical decision journey
remain unchanged.

## Privacy and product boundary

The slice stores no actor identity, response, private reason, inferred trait or
notification history. Device-local saves remain actor-neutral and may not be
used for targeting or recommendation.

The following remain deferred: server synchronization, account migration,
cross-device restore, background polling, push/email notification, notification
inbox, recommendation, ranking, social graph and production provider evidence.
CAP-079 remains `IMPLEMENTED_PARTIAL`.

## Preserved invariants

- Commit First and Blind First;
- immutable published CaseVersion and generic Case flow;
- canonical `/case/:caseId` continuation;
- Activity/My KEFE responsibility split;
- Product Preview/production isolation;
- device-local saved-Case privacy boundary;
- raw backend and stored snapshot values are not changed by localization.

## Evidence

The executable contract and Flutter tests bind version comparison,
acknowledgement, backward-compatible persistence, catalog-failure behavior,
localization, accessibility and compact presentation. API CI, Mobile CI, MVP
Beta Gates and Global Readiness must pass on one exact candidate SHA before this
slice is considered a verified checkpoint.

