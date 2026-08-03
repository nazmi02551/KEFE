# ADR-0093: Secured Admin FEED_ITEM materialization HTTP operation

- Status: Accepted
- Date: 2026-08-03
- Slice: 57

## Context

KEFE can materialize an accepted `FEED_ITEM` proposal into an immutable `NormalizedArtifact`, but that capability is only composed inside the backend. Human review already has a separate internal Admin HTTP operation. Materialization must become explicitly invokable without merging review and materialization, exposing arbitrary target selection or weakening Admin session/CSRF/capability controls.

## Decision

Add a narrow internal operation:

`POST /internal/admin/v1/feed-item-proposals/{proposal_id}/materialization`

1. The strict request body contains only `proposal_review_decision_id`.
2. The endpoint uses `WritePrincipalDep`, preserving Admin session authentication, CSRF verification and session touch behavior.
3. The secured facade authorizes `AdminCapability.SOURCE_VERIFY`.
4. Before any target write, the facade loads the proposal and stored terminal review, verifies proposal ID, supplied review decision ID and stored review identity, requires `ACCEPTED`, and requires exact `FEED_ITEM` / `kefe.feed-item` / `1.0.0` identity.
5. The facade delegates target creation to `IngestionOrchestrationService.materialize_accepted_proposal` using the composed `FeedItemProposalMaterializer`. It does not repeat payload, source-lineage, UUID, hash or metadata rules.
6. The response contains materialization ID, proposal ID, review decision ID, target kind, target ID and `replayed`.
7. The operation always returns HTTP 200. First creation has `replayed=false`; exact replay has `replayed=true`. A stable status avoids making idempotent retry semantics depend on whether the first response reached the client.
8. Review remains a separate endpoint. Materialization never creates, changes or replaces a review decision.
9. Error mapping is bounded: proposal missing is 404; review missing/mismatched/not accepted and target conflict are 409; FEED_ITEM schema mismatch is 422. Raw payloads, raw storage references and underlying exception text are never returned.
10. Production composition exposes the secured service and router but invokes neither automatically.

## Security boundary

`SOURCE_VERIFY` is already granted to the Reviewer role and is distinct from authoring projection or publication. The operation does not grant review, projection, publishing, provider, network, secret or object-storage authority.

## Consequences

An authorized source verifier can explicitly continue an already accepted feed item into normalized evidence. The proposal queue remains read-only, review remains terminal and separate, and exact replay is observable without duplicate records.

This ADR does not add bulk operations, automatic review, Claim/Case creation, editorial projection, publication, Admin UI, provider activation or phone-facing behavior.