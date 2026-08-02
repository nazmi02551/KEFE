# ADR-0089 — Immutable feed evidence reading and bounded item extraction

Status: Accepted
Date: 2026-08-03

## Context

Slice 52 captures one strict RSS/Atom feed snapshot as an immutable `SourceArtifact` and seals the exact response bytes before metadata parsing. Individual feed items are intentionally not projected during capture. The ingestion runtime can execute deterministic stage processors and persist reviewable proposals, but it currently has no provider-neutral evidence-read contract and no bounded feed-item extraction stage.

A worker must not derive content from an external URL again, trust an opaque storage reference without integrity verification or bypass the existing strict RSS/Atom validator. It must also avoid turning unreviewed feed entries directly into Claims, Cases or published content.

## Decision

1. Extend the raw-evidence boundary with an explicit read capability returning an owned immutable byte copy, canonical content hash, canonical storage reference and canonical media type.
2. A read request supplies both exact `storage_ref` and expected `content_hash`. They must derive from one another before backend access.
3. In-memory and durable evidence implementations recompute SHA-256 over the returned bytes and fail closed on reference, key, body or media-type mismatch.
4. Unconfigured evidence reading fails with one bounded retryable code and never falls back to preview fixtures, filesystem guesses or network retrieval.
5. Add a deterministic `FeedItemExtractionStageProcessor` for one exact pipeline/stage version.
6. The stage accepts only a `SOURCE_ARTIFACT` run whose artifact id and input content hash exactly match the persisted SourceArtifact.
7. The SourceArtifact must contain a canonical raw-evidence reference. The stage reads only through `RawSourceEvidenceReader`; backend object keys never enter the stage, proposal payload or operational output.
8. Before extracting entries, the stage invokes the Slice 52 `StrictRssAtomCaptureDefinition` over the evidence bytes using the artifact adapter code, external locator and the same immutable parser profile. No second permissive XML acceptance path is introduced.
9. After strict validation succeeds, the stage performs a bounded deterministic traversal of the validated tree and emits one proposal draft per feed item/entry.
10. Item identity is exact and deterministic: RSS uses `guid` when present, otherwise validated item link; Atom uses required entry `id`.
11. Duplicate item identities inside one snapshot fail closed.
12. Proposal payloads may contain only bounded item id, title, optional canonical HTTP(S) URL, optional UTC timestamp, optional bounded summary text and source snapshot references. No HTML execution, AI summarization, semantic classification or truth inference occurs.
13. Proposal order is deterministic by exact item identity. Payload hashes and the immutable run key provide cross-run idempotency.
14. The stage emits proposals only. Human review remains mandatory before any later materialization. No automatic Claim, Argument, Case, Flow or publication action is added.
15. Production ingestion runtime registry remains empty by default. The processor and plan factory are exposed for a later explicit pipeline activation decision, but no live provider or scheduled feed pipeline is registered.

## Consequences

- Feed snapshots can become bounded review-queue inputs without re-fetching the internet.
- Evidence integrity is revalidated at read time, including durable backend reads.
- Item extraction is deterministic, case-agnostic and independent of provider SDKs.
- A later activation slice can register the exact plan after editorial schema and operational ownership are approved.

## Rejected alternatives

- Re-fetching each feed URL from the ingestion worker.
- Reading backend object keys directly from SourceArtifact metadata.
- Trusting storage references without recomputing the body digest.
- Adding a separate permissive RSS library/parser path.
- Creating Claims or Cases directly from feed entries.
- Registering the pipeline in production by default.

## Non-claims

This ADR does not introduce a concrete provider, scheduled live feed capture, provider compliance approval, deployed object-storage capability proof, semantic classification, claim extraction, AI summarization, automatic review/materialization/publication, Admin UI, Case Builder, Flow Composer or phone-facing feed behavior.
