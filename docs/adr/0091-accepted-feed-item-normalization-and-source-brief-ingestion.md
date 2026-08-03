# ADR-0091 — Accepted feed item normalization and deterministic Source Brief ingestion

- Status: Accepted
- Date: 2026-08-03
- Slice: 55

## Context

Slice 53 creates deterministic `FEED_ITEM` Proposals from immutable RSS/Atom evidence. Slice 54 gives reviewers a typed, evidence-safe read surface. An accepted feed item must not jump directly into a Case or reuse the extraction stage as provenance for downstream editorial work.

The ingestion model already defines `NORMALIZED_ARTIFACT` as the provider-neutral downstream input. Adding a new Proposal input kind would duplicate an established boundary and require unnecessary schema migration.

## Decision

An explicitly accepted `FEED_ITEM` is materialized into one immutable `NormalizedArtifact` of kind `EXTERNAL_EVIDENCE`. Its identity is deterministic from the parent Proposal, review decision and normalized schema version. Its content hash is lowercase SHA-256 over canonical JSON metadata.

The normalized metadata contains only bounded typed feed-item fields, parent Proposal/review lineage, SourceArtifact identity, immutable source content hash and opaque evidence reference. Raw evidence bytes, backend object keys, HTTP headers and provider credentials are never read or copied.

The materialized artifact becomes the input of a separate ingestion run:

- pipeline `FEED_ITEM_SOURCE_BRIEF` version `1.0.0`;
- stage `BUILD_SOURCE_BRIEF` version `1.0.0`;
- executor kind `DETERMINISTIC`;
- fixed configuration hash;
- input kind `NORMALIZED_ARTIFACT`.

The explicit Admin command is API 0.22-only and CSRF protected. It requires the existing `CONTENT_REVIEW` capability through the typed feed-item service. It executes a single deterministic stage batch with deterministic stage and Proposal identities. Repeated calls recover and return the same normalized artifact, run, stage and `SOURCE_BRIEF` Proposal.

A `SOURCE_BRIEF` is only another Proposal. It has risk code `UNREVIEWED_SOURCE_BRIEF` and requires a second human review. No acceptance, projection, Case creation or publication occurs automatically.

## Failure and recovery

If normalization, lineage or source integrity is inconsistent, the command fails closed with bounded Admin errors. A deterministic stage validation failure is persisted as a final failed execution without exception text. If a successful stage batch exists but the run was not marked successful, a repeated command validates the exact history and completes the run.

## API compatibility

API 0.21 remains unchanged. API 0.22 adds one POST path:

`/internal/admin/v1/feed-items/{proposal_id}/source-brief`

No request body is accepted. The response contains only normalized artifact id, ingestion run id, Source Brief Proposal id and states.

## Consequences

Downstream editorial derivation now has explicit immutable lineage and its own run/stage evidence. The design reuses existing normalization, ingestion and review primitives rather than introducing a parallel Proposal-input model.

## Non-goals

Provider activation, live scheduling, raw evidence viewing, AI summarization, semantic or causal classification, Candidate Case materialization, automatic editorial action, publication, Admin web UI and mobile feed UI are outside this decision.
