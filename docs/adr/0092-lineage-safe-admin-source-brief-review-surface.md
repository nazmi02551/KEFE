# ADR-0092 — Lineage-safe Admin Source Brief review surface

- Status: Accepted
- Date: 2026-08-03
- Slice: 56

## Context

Slice 55 creates deterministic `SOURCE_BRIEF` Proposals from an immutable normalized feed item after its parent `FEED_ITEM` has been explicitly accepted. The generic Proposal queue exposes arbitrary payloads; reviewers need a typed contract that verifies the complete stored lineage.

## Decision

KEFE adds an additive API 0.23 Admin read surface:

- `GET /internal/admin/v1/source-briefs`
- `GET /internal/admin/v1/source-briefs/{proposal_id}`

The surface reuses existing `CONTENT_REVIEW` authorization, keyset pagination and the generic Proposal review command. It adds no review state or persistence table.

Only the exact Slice 55 identity is accepted: `SOURCE_BRIEF`, schema `kefe.source-brief` version `1.0.0`, pipeline `FEED_ITEM_SOURCE_BRIEF` version `1.0.0`, risk `UNREVIEWED_SOURCE_BRIEF`, the fixed configuration hash and `NORMALIZED_ARTIFACT` run input.

The payload key set is exact. UUID, SHA-256, evidence reference, URL, UTC timestamp and bounded text fields are validated. Proposal provenance and run input must agree.

The normalized artifact is loaded and its canonical metadata hash/schema are validated again. The parent `FEED_ITEM` is read through the Slice 54 typed service and its exact review decision must remain `ACCEPTED`. Parent Proposal/review/source/hash/reference and normalized metadata must all agree with the Source Brief.

List responses omit synopsis, evidence reference and arbitrary payload. Detail responses expose only bounded typed metadata and the opaque evidence reference. No evidence download endpoint is introduced.

API 0.22 remains unchanged. The existing generic Proposal review endpoint remains the only mutation. This surface cannot automatically accept, materialize, project, create a Case or publish content.

## Failure behavior

A non-Source-Brief Proposal requested through the typed route returns `ADMIN_SOURCE_BRIEF_NOT_FOUND`. Any malformed or lineage-inconsistent record fails closed with `ADMIN_SOURCE_BRIEF_CONTRACT_INVALID` without payload or exception leakage.

## Consequences

Review clients receive a stable typed Source Brief queue tied back to the accepted feed item, normalized artifact and immutable source reference. A later Candidate Case workflow can depend on an accepted Source Brief without parsing arbitrary Proposal payloads.

## Non-goals

Admin web UI, evidence viewer, provider activation, live scheduling, AI enrichment, semantic or causal classification, Candidate Case generation, automatic editorial action, publication and mobile feed UI are outside this decision.
