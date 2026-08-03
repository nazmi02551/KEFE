# Source Brief Ingestion — Slice 55 Candidate

- Date: 2026-08-03
- Branch: `feature/source-brief-ingestion-slice55`
- Parent: Slice 54 / PR #260 / `ee8a7e77df581b77b53cc726f46bb3de96fb6bc2`
- Status: Candidate; exact-head CI pending

## Candidate scope

This slice adds an API 0.22-only explicit Admin command that converts an already accepted `FEED_ITEM` Proposal into one immutable normalized feed-item artifact and one deterministic review-required `SOURCE_BRIEF` Proposal.

The normalized artifact reuses the established `NORMALIZED_ARTIFACT` ingestion input boundary. No new Proposal input kind or database migration is introduced. Parent Proposal/review/run/source/hash/evidence lineage is revalidated before normalization and before Source Brief assembly.

The Source Brief has its own ingestion run and stage execution. Deterministic UUID identities and the existing atomic successful-stage batch provide sequential idempotency and recovery after a successful batch whose run state was not yet finalized.

## Preserved boundaries

The command never reads raw evidence, accesses a provider, calls a network, uses AI, accepts the Source Brief, materializes it into a Case, projects or publishes content. The generated `SOURCE_BRIEF` remains `PENDING` with risk code `UNREVIEWED_SOURCE_BRIEF` and requires a second human review.

API 0.21 remains unchanged. No mobile files are modified.

## Candidate evidence

Planned exact-head evidence:

- dedicated Source Brief Ingestion CI;
- architecture and dynamic 0.21→0.22 additive OpenAPI gate;
- parent Admin feed item review, ingestion orchestration and atomic stage batch gates;
- memory HTTP authorization, CSRF, review precondition, normalization, separate run/stage/proposal and repeated-command idempotency;
- PostgreSQL durable normalized artifact/materialization/run/stage/proposal evidence;
- general API, MVP and Global regression/candidate gates.

No PASS statement is valid until all required workflows complete successfully on one exact runtime SHA.
