# ADR-0090 — Evidence-safe Admin feed item review surface

- Status: Accepted
- Date: 2026-08-03
- Slice: 54

## Context

Slice 53 produces deterministic `FEED_ITEM` Proposals from immutable RSS/Atom evidence. The generic Admin Proposal queue can expose arbitrary Proposal payloads in its authorized detail endpoint, but it does not provide a typed feed-review contract or verify that feed fields still match the immutable SourceArtifact and IngestionRun.

A reviewer needs a bounded surface that shows the feed/item metadata needed for a human decision without opening raw evidence bytes, leaking backend object keys, or creating a second review mutation path.

## Decision

KEFE adds an additive API 0.21 Admin read surface:

- `GET /internal/admin/v1/feed-items`
- `GET /internal/admin/v1/feed-items/{proposal_id}`

The surface reuses the existing `CONTENT_REVIEW` authorization, Proposal queue repository, keyset cursor and generic Proposal review mutation. It introduces no new review state or persistence table.

The read adapter accepts only the exact Slice 53 identity:

- Proposal kind `FEED_ITEM`;
- payload schema `kefe.feed-item` version `1.0.0`;
- pipeline `RSS_ATOM_FEED_ITEM_EXTRACTION` version `1.0.0`;
- risk code `UNREVIEWED_EXTERNAL_FEED_ITEM`;
- SourceArtifact input kind.

The payload key set is exact. UUID, canonical SHA-256, canonical evidence reference, feed format, URL, UTC timestamp and bounded canonical text are validated. The payload source id/hash/reference must match the IngestionRun, Proposal provenance and persisted immutable SourceArtifact.

List responses omit summary text, evidence reference and arbitrary payload. Detail responses expose only typed metadata and the opaque content-addressed evidence reference. The reference is not a raw object key and no dereference endpoint is introduced.

The API is gated at version 0.21. Runtime versions 0.19 and 0.20 do not expose these routes.

Human review remains mandatory through the existing generic Proposal review command. This slice cannot accept, materialize, project, create a Case or publish content.

## Security and privacy boundaries

The surface never reads or returns raw evidence bytes. It does not expose backend object keys, provider credentials, HTTP headers, URL query secrets, exception text, preview fixtures or provider SDK objects.

Malformed or internally inconsistent feed-item records fail closed with bounded error code `ADMIN_FEED_ITEM_CONTRACT_INVALID`. A non-feed Proposal requested through the typed detail route is reported as `ADMIN_FEED_ITEM_NOT_FOUND`.

## Consequences

Review clients receive a stable typed contract and can filter/paginate feed work without parsing arbitrary Proposal payloads. Existing 0.19/0.20 OpenAPI contracts remain unchanged. A later Admin UI can consume this surface, but no UI or automatic editorial workflow is claimed here.

## Non-goals

Raw evidence viewer, evidence dereference/download API, provider activation, live scheduling, semantic classification, AI summarization, Candidate Case generation, automatic review/materialization/publication, mobile feed UI and Store release are outside this decision.
