# ADR-0090 — Human-reviewed feed item normalization materialization

- **Status:** Accepted
- **Date:** 2026-08-03
- **Slice:** 54

## Context

Slice 53 produces deterministic, review-required `FEED_ITEM` proposals from immutable RSS/Atom evidence. Those proposals are not yet part of the canonical knowledge artifact graph. Moving them into that graph must not bypass human review, trust proposal-supplied provenance blindly, create duplicate artifacts after partial failures, or turn feed content directly into a Case or published product surface.

The existing ingestion orchestration already separates proposals, terminal review decisions and materialization records. `KnowledgeProposalMaterializer` already provides deterministic proposal-to-target identities for canonical knowledge records. Slice 54 extends that boundary rather than introducing a parallel lifecycle.

## Decision

### 1. ACCEPTED review remains mandatory

`IngestionOrchestrationService.materialize_accepted_proposal` remains the lifecycle authority. It refuses missing, rejected or changes-requested reviews. The FEED_ITEM handler also verifies that the supplied review belongs to the proposal and is exactly `ACCEPTED` as a defense-in-depth contract for direct calls and tests.

### 2. Exact proposal contract

Only this exact proposal shape is materializable:

- proposal kind: `FEED_ITEM`
- payload schema: `kefe.feed-item`
- payload schema version: `1.0.0`
- risk code: `UNREVIEWED_EXTERNAL_FEED_ITEM`
- no AI execution reference
- exact payload key set emitted by Slice 53

Unknown fields, noncanonical text, unbounded values, malformed URLs, non-UTC timestamps or type drift fail closed.

### 3. Persisted SourceArtifact is authoritative

The materializer loads the referenced `SourceArtifact` and requires exact agreement for:

- source artifact UUID;
- feed content hash;
- canonical evidence storage reference;
- proposal provenance reference.

The proposal cannot replace the source language or jurisdiction, invent another evidence reference, or smuggle backend object keys or raw XML into the normalized record.

### 4. Deterministic immutable target

A reviewed feed item becomes one `NormalizedArtifact` with:

- target kind `NORMALIZED_ARTIFACT`;
- artifact kind `EXTERNAL_EVIDENCE`;
- deterministic UUIDv5 derived from proposal UUID and target kind;
- deterministic text consisting only of the reviewed title and optional reviewed summary;
- deterministic lowercase SHA-256 over canonical approved item fields;
- `normalized_at` equal to the human review timestamp;
- language and jurisdiction inherited from the persisted SourceArtifact.

No generated interpretation, semantic label, fact-check result, Claim, Argument, Case or publication action is added.

### 5. Bounded provenance metadata

The normalized artifact records bounded, JSON-safe metadata for proposal, review, source artifact, feed, item URL/timestamp and immutable evidence references. It excludes raw XML, response headers, credentials, provider secrets and backend object keys.

### 6. Retry and conflict semantics

Materialization may partially succeed if the normalized artifact is written before the orchestration materialization row. Therefore the target UUID is deterministic. On retry:

- an exact existing artifact is accepted and reused;
- an existing artifact with the same deterministic UUID but different content or provenance is rejected as a conflict;
- a repository uniqueness race is reread and accepted only when the persisted artifact is exactly equal.

This makes recovery idempotent without silently accepting corruption.

### 7. Production boundaries

Slice 54 does not activate a provider, ingestion worker plan, scheduler or automatic materialization loop. Materialization occurs only through the existing explicit reviewed-proposal command path. No Case Builder, Flow Composer, editorial projection or consumer-facing feed surface is introduced.

## Consequences

- Human-reviewed feed items can enter the canonical normalized artifact graph safely.
- Later Claim/Argument extraction can reference a stable normalized artifact instead of reparsing raw feed XML.
- Review provenance and immutable evidence lineage remain inspectable.
- Production still has zero concrete feed providers and zero automatically active feed pipelines.

## Rejected alternatives

- **Create a Case directly from a feed item:** rejected because editorial modeling and product publication require separate human-authoring decisions.
- **Use random target UUIDs:** rejected because retry after partial persistence would duplicate artifacts.
- **Trust proposal hash/reference without loading SourceArtifact:** rejected because proposal payload is not an authority boundary.
- **Include raw XML in metadata:** rejected because the immutable evidence store already owns raw bytes and metadata must remain bounded.
- **Automatically materialize every accepted proposal:** rejected because explicit operational control remains required.