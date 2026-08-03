# Admin Source Brief Review — Slice 56 Candidate

- Date: 2026-08-03
- Branch: `feature/admin-source-brief-review-slice56`
- Parent: Slice 55 / PR #262 / `dd30c55ef3d07358920de2d4834537d389b048fd`
- Status: Candidate; exact-head CI pending

## Candidate scope

This slice adds an API 0.23-only typed Admin read surface for deterministic `SOURCE_BRIEF` Proposals:

- `GET /internal/admin/v1/source-briefs`
- `GET /internal/admin/v1/source-briefs/{proposal_id}`

The read adapter validates exact Proposal/schema/pipeline/risk/configuration identity, exact payload keys and bounded typed values. It revalidates the normalized artifact schema and canonical content hash, then reuses the typed Feed Item review service to confirm that the exact parent review decision remains `ACCEPTED` and that all SourceArtifact/content-hash/evidence-reference lineage agrees.

List responses intentionally omit synopsis, evidence reference and arbitrary payload. Detail responses expose bounded typed metadata and only the opaque evidence reference. Existing generic Proposal review remains the only mutation.

## Preserved boundaries

No raw evidence read or download route, backend object key, credential, provider activation, live scheduling, AI enrichment, semantic/causal inference, automatic review/materialization/projection, Case creation, publication, Admin web UI or mobile feed UI is introduced.

API 0.22 remains unchanged. No mobile files are modified.

## Candidate evidence

Planned exact-head evidence:

- dedicated Admin Source Brief Review CI;
- dynamic API 0.22→0.23 additive OpenAPI comparison;
- parent Source Brief Ingestion and Admin Feed Item Review architecture gates;
- memory HTTP authorization, pagination, typed detail, generic review refresh, non-kind hiding and malformed-record failure;
- PostgreSQL durable lineage/list/detail/review-refresh evidence;
- general API, MVP and Global regression/candidate gates.

No PASS statement is valid until all required workflows complete successfully on one exact runtime SHA.
