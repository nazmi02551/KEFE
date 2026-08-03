# ADR-0092: Human-approved FEED_ITEM materialization into immutable NormalizedArtifact

- Status: Accepted
- Date: 2026-08-03
- Slice: 56

## Context

RSS/Atom extraction now ends at review-required `FEED_ITEM` proposals. The existing `KnowledgeProposalMaterializer` intentionally handles Claim and Argument graph records. Adding feed items to that handler map would conflate editorial source normalization with semantic knowledge assertions.

KEFE needs a human-gated bridge from an accepted external feed item into the immutable normalized-artifact layer before any later claim or Case work.

## Decision

Introduce a dedicated `FeedItemProposalMaterializer` implementing the existing `ProposalTargetMaterializer` port.

1. Materialization remains callable only through `IngestionOrchestrationService.materialize_accepted_proposal`, which requires a terminal `ACCEPTED` review.
2. The materializer accepts only proposal kind `FEED_ITEM`, schema `kefe.feed-item`, version `1.0.0`, and the exact ten-field payload emitted by the feed-item extraction stage.
3. The referenced `SourceArtifact` must exist. Proposal source ID, feed content hash and raw storage reference must exactly match the source artifact.
4. The target ID is deterministic UUIDv5 over proposal ID and target kind `NORMALIZED_ARTIFACT`.
5. Canonical text is the normalized item title followed by two line breaks and the optional normalized summary. Text budgets remain bounded.
6. Content hash is lowercase SHA-256 over the exact UTF-8 canonical text and is formatted `sha256:<64 hex>`.
7. The created artifact uses `ArtifactKind.EXTERNAL_EVIDENCE`, `normalized_at=review.decided_at`, and inherits language and jurisdiction only from the source artifact.
8. Bounded metadata preserves feed/item identity, canonical item URL, published timestamp, feed title/format, proposal ID, review ID, reviewer reference and provenance reference. Raw feed bytes, credential material and backend object keys are never copied.
9. Existing target records are accepted only when they exactly equal the deterministic artifact; conflicting UUID reuse fails closed.
10. The Claim/Argument `KnowledgeProposalMaterializer` remains unchanged and cannot materialize `FEED_ITEM`.
11. Production composition may construct the materializer but performs zero automatic review or materialization.

## Review and publication boundary

This slice does not accept proposals, create Claims, generate Cases, project editorial content or publish. Human review remains mandatory and semantically separate from materialization.

## Consequences

Accepted feed items gain stable lineage into `NormalizedArtifact`, enabling later explicit claim extraction or candidate-authoring stages without treating feed text as verified truth. Rejected, changes-requested, unreviewed, schema-drifted and source-mismatched proposals fail closed.

This ADR does not introduce AI summarization, semantic classification, automatic Case creation, editorial projection, publication, Admin UI changes or phone-facing feed behavior.