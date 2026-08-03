# Admin Feed Item Review — Slice 54 Candidate

- Date: 2026-08-03
- Branch: `feature/admin-feed-item-review-slice54`
- Parent: Slice 53 / PR #232 / `2bb18cd3cc34c2dc6bcb84559948b1231e8e2308`
- Status: Candidate; exact-head CI pending

## Candidate scope

This slice adds an API 0.21-only typed Admin read surface for deterministic RSS/Atom `FEED_ITEM` Proposals:

- `GET /internal/admin/v1/feed-items`
- `GET /internal/admin/v1/feed-items/{proposal_id}`

The surface reuses the existing `CONTENT_REVIEW` authorization, durable Proposal queue, keyset cursor and generic Proposal review mutation. It validates exact Proposal/schema/pipeline/risk identity, an exact payload key set, canonical UUID/hash/evidence-ref/URL/timestamp values and consistency with the IngestionRun and immutable SourceArtifact.

List records intentionally omit arbitrary payload, summary text and evidence reference. Detail records expose bounded typed metadata and only the opaque content-addressed evidence reference. No raw evidence bytes or backend object key can cross this surface.

## Preserved boundaries

No Admin web UI, raw evidence viewer or dereference endpoint is introduced. This slice does not activate providers, schedule live feeds, classify content, summarize with AI, create Candidate Cases, accept Proposals automatically, materialize, project or publish content. API 0.19 and 0.20 remain unchanged.

## Candidate evidence

Planned exact-head evidence:

- dedicated Admin Feed Item Review CI;
- architecture and dynamic 0.20→0.21 additive OpenAPI gate;
- parent Feed Item Extraction and Admin Proposal Queue architecture gates;
- memory HTTP authorization, pagination, typed detail, generic review refresh and fail-closed malformed-record tests;
- PostgreSQL migration, durable queue/knowledge join, pagination/detail and review refresh tests;
- general API, MVP and Global regression/candidate gates.

No PASS statement is valid until all required workflows complete successfully on one exact runtime SHA.
