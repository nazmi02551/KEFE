# Active Reviewed Proposal Source — Slice 33 Candidate

**Issue:** #184  
**Capabilities:** CAP-055, CAP-061, CAP-062, CAP-065  
**Base:** `feature/editorial-projection-runtime-slice32`  
**Status:** candidate; exact-head CI pending

## Candidate boundary

This slice adopts the provider-neutral ADR-0028 run/stage/Proposal/review core into the active stacked line and connects it to the verified ADR-0029 Editorial Projection service.

Included:

- replay-safe `IngestionRun` identity;
- append-only stage attempts and bounded retry state;
- immutable, payload-hashed Proposal records;
- one terminal review decision per Proposal;
- explicit `dependency_proposal_ids` for Candidate Case bundles;
- `IngestionReviewedProposalSource` adapter;
- dedicated `CONTENT_PROJECT` capability;
- secured projection facade deriving actor identity from `AdminPrincipal`;
- memory and PostgreSQL persistence;
- linear migration `20260802_0019 -> 20260802_0020`;
- application composition without HTTP exposure;
- unit/security and PostgreSQL end-to-end tests.

## Exclusions

No external provider or AI calls, HTTP route, Admin UI, automatic projection, automatic authoring lifecycle transition, knowledge materialization change, Case Builder, Flow Composer or wholesale PR #68 merge is included.

Do not call this slice PASS until exact-head API CI, one-head migration, architecture fitness, unit/security tests and PostgreSQL reviewed-Proposal-to-DRAFT integration succeed.
