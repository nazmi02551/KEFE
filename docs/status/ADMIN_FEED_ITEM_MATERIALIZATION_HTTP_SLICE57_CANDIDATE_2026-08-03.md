# Admin FEED_ITEM Materialization HTTP Slice 57 Candidate — 2026-08-03

## Candidate scope

Slice 57 exposes an explicit internal Admin operation for materializing an already accepted FEED_ITEM proposal:

`POST /internal/admin/v1/feed-item-proposals/{proposal_id}/materialization`

The strict request body contains only `proposal_review_decision_id`. The operation uses the existing Admin session, CSRF, `WritePrincipalDep` and `SOURCE_VERIFY` capability boundary.

Before any write it verifies:

- the proposal exists;
- the proposal is exact FEED_ITEM / `kefe.feed-item` / `1.0.0`;
- a terminal review exists;
- the supplied review decision ID exactly matches the stored review;
- the stored decision is ACCEPTED.

Target creation is delegated to `IngestionOrchestrationService.materialize_accepted_proposal` and the existing `FeedItemProposalMaterializer`. The HTTP layer does not duplicate payload, source-lineage, UUID, hash or metadata logic.

## Idempotency

The operation always returns HTTP 200:

- first creation: `replayed=false`;
- exact replay: `replayed=true` and the same materialization/target IDs.

Review remains a separate explicit endpoint.

## Production boundary

The secured service and router are composed, but production performs:

- zero automatic reviews;
- zero automatic materializations;
- zero Claim or Case creation;
- zero editorial projection or publication.

The response and bounded errors never include proposal payloads, raw storage references or underlying exception text.

## Candidate validation

Pending exact-head CI. Required evidence:

- Admin Feed Item Materialization CI memory and PostgreSQL jobs;
- Admin session/CSRF/capability tests;
- accepted/replay/wrong-review/negative-review/wrong-schema/no-partial-write tests;
- additive OpenAPI overlay exact gate;
- parent Admin/ingestion/feed-materialization gates;
- API CI;
- MVP Beta Gates;
- Global Readiness.

Do not call PASS or mark ready until every required workflow is green on one exact runtime SHA. Do not merge before the active parent stack.