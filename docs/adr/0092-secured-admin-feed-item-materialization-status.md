# ADR-0092 — Secured Admin feed item materialization status

- **Status:** Accepted
- **Date:** 2026-08-03
- **Slice:** 56

## Context

Slice 55 added an explicit Admin command for materializing an already accepted `FEED_ITEM` proposal. Admin clients can list and inspect proposals, and can issue the command when they know the accepted review decision ID. They cannot currently observe whether a proposal still needs review, is ready for the materialization command, or has already been materialized without interpreting several separate records client-side.

Adding status fields to the existing proposal detail schema would modify an established OpenAPI component and path item. A separate read-only endpoint preserves additive API evolution and keeps feed-item lifecycle semantics explicitly scoped.

## Decision

### 1. Add one read-only additive endpoint

Add:

`GET /internal/admin/v1/proposals/{proposal_id}/feed-item-materialization-status`

The endpoint uses the existing Admin read-principal dependency. It requires an authenticated Admin session but no CSRF token because it performs no mutation.

### 2. Require review and source-verification authority

The secured status service requires both `CONTENT_REVIEW` and `SOURCE_VERIFY`. Reviewer-role principals can read the state; editor-only and publisher-only principals cannot. No publication step-up is required.

### 3. Exact FEED_ITEM scope

The endpoint accepts only proposals matching the Slice 55 scope:

- kind `FEED_ITEM`;
- schema `kefe.feed-item`;
- schema version `1.0.0`;
- risk code `UNREVIEWED_EXTERNAL_FEED_ITEM`;
- no AI execution reference.

Unsupported proposal kinds or schema drift return a bounded unsupported error rather than a misleading status.

### 4. Three persisted states

The service derives exactly one state from persisted proposal, review and materialization records:

- `REVIEW_REQUIRED`: there is no terminal `ACCEPTED` review. Rejected and changes-requested reviews remain review-required for materialization purposes. No target identity is returned.
- `READY`: an exact `ACCEPTED` review exists and no `NORMALIZED_ARTIFACT` materialization exists.
- `MATERIALIZED`: an exact `NORMALIZED_ARTIFACT` materialization exists and its review decision ID matches the accepted review.

The service does not predict future success, inspect raw evidence, or validate the proposal payload again. Command-time validation remains owned by Slice 55 and Slice 54.

### 5. Fail closed on inconsistent persisted state

A materialization without an accepted review, a mismatched review binding, an unexpected target kind, or inconsistent proposal identity is a persistence conflict. The endpoint returns a bounded conflict error and never guesses a best-effort state.

### 6. Bounded response

The response contains only:

- proposal ID;
- lifecycle status;
- terminal review decision ID and decision when present;
- proposal materialization ID when present;
- target kind and target ID when present;
- materialized timestamp when present.

It excludes proposal payloads, normalized text, artifact metadata, reviewer rationale, evidence references/bytes, credentials, response headers and backend object keys.

### 7. No mutation or automation

The status service never calls review, materialization, projection, publication or provider operations. It adds no polling worker, scheduler, bulk endpoint, UI or phone-facing feature.

## Consequences

- Admin clients can render a deterministic lifecycle state without reconstructing domain rules.
- The command remains separate and explicit.
- Existing proposal queue/detail and command OpenAPI contracts remain unchanged.
- Future Admin UI can use the status endpoint without receiving content or evidence data.

## Rejected alternatives

- **Add optional fields to proposal detail:** rejected because it changes an established component and couples generic queue records to one proposal kind.
- **Return 404 until materialized:** rejected because clients need to distinguish review-required from ready.
- **Return proposal payload or normalized artifact:** rejected because lifecycle observation does not require content disclosure.
- **Validate raw evidence during status reads:** rejected because status must remain a cheap persisted-state observation.
- **Automatically invoke the command when READY:** rejected because explicit human-operated materialization remains required.