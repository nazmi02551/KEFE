# ADR-0072 — Durable Admin Proposal Review Queue and Query Semantics

**Status:** Accepted for Slice 36 implementation  
**Date:** 2026-08-02  
**Issue:** #196  
**Parent runtime:** PR #195 / Slice 35  
**Capabilities:** CAP-061, CAP-065  
**Foundation waves:** F1 → F3 operational bridge

## Context

KEFE now has a durable provider-neutral Proposal store, terminal human review decisions and a secured Admin command for recording one review decision. Reviewers still lack a production-shaped read boundary for discovering pending work and inspecting immutable Proposal details.

A naive offset-paginated endpoint would be unstable while new Proposals arrive or reviews are recorded. Exposing the full payload in every queue row would also make the operational list unnecessarily heavy and couple list performance to arbitrary Proposal schemas.

## Decision

KEFE will expose two authenticated Admin read operations under `/internal/admin/v1`:

1. `GET /proposals`
   - requires `CONTENT_REVIEW`;
   - returns lightweight immutable Proposal metadata and terminal review summary;
   - orders oldest first by `(created_at, proposal_id)`;
   - uses opaque keyset cursor pagination only;
   - supports exact filters for review state, Proposal kind, risk code, run ID and pipeline code;
   - accepts page sizes from 1 to 100 and fetches one extra row to determine continuation.

2. `GET /proposals/{proposal_id}`
   - requires `CONTENT_REVIEW`;
   - returns the same metadata plus the immutable Proposal payload;
   - returns the durable terminal review summary when one exists.

Review state is a query projection:

- no `ProposalReviewDecision` → `PENDING`;
- terminal decision → `ACCEPTED`, `REJECTED` or `CHANGES_REQUESTED`.

## Cursor contract

The cursor encodes only the last visible `(created_at, proposal_id)` key. It is URL-safe, opaque to clients, strictly validated and not interpreted as authorization. Invalid or malformed cursors fail with `ADMIN_PROPOSAL_QUEUE_CURSOR_INVALID` and do not silently restart at page one.

No offset parameter is supported.

## Data boundary

Queue records are assembled from the existing ingestion `Proposal`, `IngestionRun` and optional `ProposalReviewDecision`. No duplicate queue table, second CMS or derived truth store is introduced.

The list response does not include arbitrary Proposal payloads. The detail response may expose the immutable payload to an authorized reviewer. Neither response treats provider/AI output as accepted truth.

## Preserved lifecycle separation

- reading the queue does not claim, assign, lock or mutate a Proposal;
- terminal Proposal review remains the existing explicit write command;
- an accepted Proposal does not automatically project;
- projection remains separate from Content Authoring review, approval and publication;
- no automatic prioritization or AI ranking is introduced.

## Evidence required

Slice 36 is not PASS until the same exact runtime SHA proves:

- memory/PostgreSQL filter and ordering parity;
- stable keyset pagination while additional rows exist;
- invalid cursor failure;
- payload excluded from list and present in authorized detail;
- terminal review immediately reflected in subsequent queue reads;
- unauthorized Admin roles fail closed;
- additive OpenAPI and architecture fitness;
- API CI, MVP Beta Gates and Global Readiness success.

Automated evidence does not establish human usability, queue assignment/lease concurrency, external provider operation or production SLO.
