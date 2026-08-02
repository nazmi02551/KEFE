# Active Reviewed Proposal Source — Slice 33 Verification

**Issue:** #184  
**Capabilities:** CAP-055, CAP-061, CAP-062, CAP-065  
**Base:** `feature/editorial-projection-runtime-slice32`  
**Verified runtime SHA:** `1295ccabbd2ee33bcfd1cd10d062528091e91920`  
**Status:** bounded active-line reviewed Proposal source + secured facade — PASS

## Verified boundary

This slice adopts the provider-neutral ADR-0028 run/stage/Proposal/review core into the active stacked line and connects terminally reviewed Proposal bundles to the verified ADR-0029 Editorial Projection service.

Verified runtime behavior:

- replay-safe `IngestionRun` identity from input/pipeline/configuration/version context;
- append-only, uniquely numbered stage attempts and bounded retry state;
- immutable, payload-hashed Proposal records with run/stage provenance;
- one terminal review decision per Proposal;
- explicit Candidate Case `dependency_proposal_ids`;
- `IngestionReviewedProposalSource` resolution of Candidate and reviewed dependencies;
- dedicated `CONTENT_PROJECT` capability granted to Editor role;
- secured projection facade deriving audit actor from `AdminPrincipal.audit_actor_ref`;
- request-supplied actor identity absent from the facade;
- memory and PostgreSQL persistence;
- linear migration `20260802_0019 -> 20260802_0020`;
- memory/PostgreSQL application composition without HTTP exposure;
- reviewed Proposal -> accepted dependency bundle -> existing Content Authoring DRAFT end-to-end evidence;
- no consumer materialization before the existing publication lifecycle.

## Exact-SHA evidence

### API CI — SUCCESS

Run `30725000629`:

- lint/unit job `91434903725` — SUCCESS;
- PostgreSQL integration job `91434952412` — SUCCESS;
- Ruff, contract sync and OpenAPI drift — SUCCESS;
- existing architecture fitness gates — SUCCESS;
- Slice 33 reviewed Proposal source fitness — SUCCESS;
- unit/security tests — SUCCESS;
- one-head migration and PostgreSQL end-to-end test — SUCCESS.

### MVP Beta Gates — SUCCESS

Run `30725000689`:

- API contract job `91434903966` — SUCCESS;
- mobile job `91434903940` — SUCCESS;
- PostgreSQL job `91434964956` — SUCCESS;
- API behavior/performance regression, mobile analyze/tests/APK build and one-head PostgreSQL continuity — SUCCESS.

### Global Readiness — SUCCESS

Run `30725000635`:

- API global job `91434903797` — SUCCESS;
- phone candidate job `91434903816` — SUCCESS;
- PostgreSQL global job `91434903787` — SUCCESS;
- production-copy boundary, phone acceptance, mobile regressions, global-head migration and existing PostgreSQL regression — SUCCESS.

The generated phone artifacts are regression evidence only. This backend/application slice does not add phone-facing behavior and is not a new user APK release.

## Rejected candidate

`57fec33cec991b3dd1a5d11e40f9bbc3026a7604` is not PASS. It failed Ruff because of an unused test import; subsequent checks were skipped.

## Explicit exclusions and remaining gates

This slice does not include:

- external provider or AI calls;
- production source adapters, schedulers or worker deployment;
- HTTP projection route or Admin UI;
- automatic projection after Proposal acceptance;
- automatic authoring submit/review/approval/publication;
- knowledge materialization changes;
- Case Builder or Flow Composer;
- atomic worker transaction covering a stage result and every emitted Proposal as one production queue operation;
- human editorial usability/acceptance;
- production provider/SLO/rollback evidence.

Therefore this record proves a durable active-line reviewed Proposal source and secured application facade. It does not claim the full F1/F2/F3 foundation or production editorial operation is complete.
