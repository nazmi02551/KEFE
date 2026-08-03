# ADR-0091 — Secured Admin feed item materialization command

- **Status:** Accepted
- **Date:** 2026-08-03
- **Slice:** 55

## Context

Slice 54 added the canonical, deterministic `FEED_ITEM → NORMALIZED_ARTIFACT` materializer, but it is available only through the application service boundary. Admin reviewers can already list proposal queue records, inspect payloads and record one terminal review decision through secured HTTP. There is no explicit HTTP command that turns an already accepted feed item into its immutable normalized artifact.

Combining review and materialization into one endpoint would weaken the existing lifecycle separation. Exposing the generic proposal materializer would also make unrelated Claim/Argument proposal kinds remotely materializable without an explicit product decision.

## Decision

### 1. One exact internal command

Add one internal Admin endpoint:

`POST /internal/admin/v1/proposals/{proposal_id}/feed-item-materialization`

The request contains only the exact `proposal_review_decision_id`. The endpoint is idempotent and always returns the canonical proposal materialization record.

### 2. Review remains a separate prior command

The endpoint never creates or changes a review decision. The proposal must already have one terminal `ACCEPTED` review. The supplied review decision ID must exactly match the persisted review for the proposal. Pending, rejected, changes-requested, stale or unrelated review bindings fail closed.

### 3. Security boundary

The route uses the existing Admin write principal dependency, therefore an authenticated Admin session and valid CSRF token are mandatory. The secured application service separately requires both:

- `CONTENT_REVIEW`;
- `SOURCE_VERIFY`.

The existing Reviewer role has both capabilities. Editor-only, publisher-only and unauthenticated callers cannot execute the command. Materialization does not require publication authority because it creates no CaseVersion and publishes nothing.

### 4. Exact FEED_ITEM scope

The secured service accepts only:

- proposal kind `FEED_ITEM`;
- payload schema `kefe.feed-item`;
- payload schema version `1.0.0`;
- risk code `UNREVIEWED_EXTERNAL_FEED_ITEM`;
- no AI execution reference.

No generic Claim, Argument, Candidate Case or unknown proposal kind is exposed through this endpoint.

### 5. Existing materializer remains authoritative

The secured service performs lifecycle and scope checks, then delegates target construction to the Slice 54 `KnowledgeProposalMaterializer` through `IngestionOrchestrationService.materialize_accepted_proposal`. The router and secured service do not construct, hash or persist `NormalizedArtifact` directly.

### 6. Idempotent replay and conflict handling

If a `NORMALIZED_ARTIFACT` materialization already exists for the proposal and references the same accepted review, the exact record is returned. A mismatched review binding or target-kind conflict is rejected. Partial target persistence recovery remains owned by the Slice 54 materializer.

### 7. Bounded HTTP contract

The response contains only:

- proposal materialization ID;
- proposal ID;
- proposal review decision ID;
- target kind;
- target ID;
- materialized timestamp.

It never returns proposal payloads, raw XML, evidence bytes, credentials, headers or backend object keys. Domain errors use fixed codes for not-found, unsupported proposal, review-required, review-binding mismatch and materialization conflict/invalidity.

### 8. Production boundaries

The command is explicit and synchronous. Slice 55 adds no queue consumer, cron, worker, bulk operation, automatic review, automatic materialization, provider activation, Case creation, editorial projection or publication.

## Consequences

- Human reviewers can complete the feed-item normalization lifecycle through the secured Admin API.
- Review and materialization remain independently auditable through immutable review and materialization records.
- Replays are safe and do not duplicate normalized artifacts.
- Generic knowledge proposal materialization is not accidentally exposed.

## Rejected alternatives

- **Review and materialize in one request:** rejected because review must remain a distinct terminal human decision.
- **Expose a generic `/materialize` endpoint:** rejected because each proposal kind needs an explicit product/security decision.
- **Require `CONTENT_PUBLISH`:** rejected because normalized evidence is not published content.
- **Return the full normalized artifact or proposal payload:** rejected because the command response should expose only operational identity.
- **Run materialization automatically after acceptance:** rejected because explicit operational control remains required.