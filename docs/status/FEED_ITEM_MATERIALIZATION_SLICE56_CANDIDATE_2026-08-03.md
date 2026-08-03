# Feed Item Materialization Slice 56 Candidate — 2026-08-03

## Candidate scope

Slice 56 adds a dedicated human-gated `FeedItemProposalMaterializer`.

The materializer accepts only an exact `FEED_ITEM` proposal using schema `kefe.feed-item` version `1.0.0` after a terminal `ACCEPTED` review. It verifies SourceArtifact identity, content hash and raw evidence reference before creating one deterministic `NormalizedArtifact`.

The target artifact:

- uses `ArtifactKind.EXTERNAL_EVIDENCE`;
- derives a deterministic UUIDv5 from proposal ID and target kind;
- stores canonical title plus optional summary text;
- computes lowercase SHA-256 over exact UTF-8 canonical text;
- inherits language and jurisdiction from SourceArtifact;
- preserves bounded feed/item/review/provenance metadata;
- excludes raw feed bytes, raw storage reference, credential material and backend object keys.

## Preserved boundaries

The Claim/Argument `KnowledgeProposalMaterializer` remains unchanged and rejects `FEED_ITEM`.

Production composition constructs the feed-item materializer but performs:

- zero automatic reviews;
- zero automatic materializations;
- zero Claim or Case creation;
- zero editorial projection or publication.

No schema migration is introduced.

## Candidate validation

Pending exact-head CI. Required evidence:

- Feed Item Materialization CI memory and PostgreSQL jobs;
- parent ingestion, feed extraction and RSS/Atom route gates;
- accepted/rejected/schema/source-lineage/idempotency tests;
- API CI;
- MVP Beta Gates;
- Global Readiness.

Do not call PASS or mark ready until every required workflow is green on one exact runtime SHA. Do not merge before the active parent stack.