# Secured Admin Editorial Projection HTTP — Slice 34 Verification

**Issue:** #186  
**Capabilities:** CAP-061, CAP-062, CAP-065  
**Base:** `feature/reviewed-proposal-source-slice33`  
**Verified runtime SHA:** `eb303403970505d989600c4217dea181f9475904`  
**Status:** secured Admin projection HTTP boundary — PASS

## Verified boundary

This slice exposes the reviewed Candidate Case → existing Content Authoring DRAFT projection through the established internal Admin session and same-session CSRF boundary.

Verified behavior:

- `POST /internal/admin/v1/candidate-proposals/{candidate_proposal_id}/projection`;
- `kefe_admin_session` cookie resolution through the existing Admin session store;
- `X-KEFE-CSRF` verification inside `WritePrincipalDep` before mutation;
- dedicated `CONTENT_PROJECT` authorization through `SecuredEditorialProjectionService`;
- strict request schema that rejects actor/admin/role/capability/lifecycle/target identity fields;
- explicit Flow code/version pair validation;
- audit actor derived only from `AdminPrincipal.audit_actor_ref`;
- immutable projection lineage response with DRAFT state and replay disclosure;
- first request and same-input idempotent replay both return HTTP 200 and the same projection/DRAFT identity;
- missing CSRF, invalid session and insufficient capability fail before projection mutation;
- PostgreSQL Admin session → reviewed Proposal bundle → projection lineage → existing Content Authoring DRAFT integration;
- no consumer CaseVersion materialization before the existing publication lifecycle;
- additive OpenAPI 0.19 Admin projection overlay composed consistently into base, MVP and Global 0.20 contracts.

## Exact-SHA evidence

### API CI — SUCCESS

Run `30726014741`:

- lint/unit job `91437755048` — SUCCESS;
- PostgreSQL integration job `91437807230` — SUCCESS;
- Ruff, contract sync and composed OpenAPI drift — SUCCESS;
- existing architecture fitness gates — SUCCESS;
- Admin Editorial Projection HTTP fitness — SUCCESS;
- memory CSRF/authorization/strict-request/replay tests — SUCCESS;
- PostgreSQL secured HTTP projection test — SUCCESS;
- one-head migration and existing PostgreSQL regressions — SUCCESS.

### MVP Beta Gates — SUCCESS

Run `30726014748`:

- API contract job `91437755031` — SUCCESS;
- mobile job `91437755002` — SUCCESS;
- PostgreSQL job `91437822004` — SUCCESS;
- exact 0.19 additive overlay and composed OpenAPI gates — SUCCESS;
- API behavior/performance, mobile analyze/tests/APK build and one-head PostgreSQL continuity — SUCCESS.

### Global Readiness — SUCCESS

Run `30726014742`:

- API global job `91437754999` — SUCCESS;
- phone-candidate job `91437755018` — SUCCESS;
- PostgreSQL global job `91437755003` — SUCCESS;
- exact 0.20 additive overlay, production-copy boundary, phone acceptance, mobile regressions and global-head PostgreSQL migration — SUCCESS.

The generated phone artifacts are regression evidence only. This backend/Admin API slice does not add phone-facing behavior and is not a new user APK release.

## Rejected or superseded candidates

The following SHAs are not PASS:

- `eb0ee6edb901573bfbdc55818fbc33e815c34b3a` — the new route was absent from the checked-in composed OpenAPI contract;
- `e2873358cf884e40be6b51a8a229da853f1ee562` — API CI passed but the MVP 0.19 additive overlay exact gate rejected the separate Admin overlay composition;
- `99acd71e4cd68aff35e636b71ba0d5c307017128` — API/MVP progressed but Global 0.20 overlay exact gate had not yet composed the Admin 0.19 overlay.

## Explicit exclusions and remaining gates

This slice does not include:

- an Admin UI;
- Proposal review/queue HTTP endpoints;
- external provider or AI calls;
- production workers, schedulers or provider delivery;
- automatic projection after Proposal acceptance;
- automatic authoring submit/review/approval/publication;
- Case Builder or Flow Composer;
- human editorial usability/acceptance evidence;
- production provider, deployed SLO or operator rollback evidence;
- phone-facing behavior.

Therefore this record proves the secured Admin HTTP command boundary for CAP-062. It does not claim the full F1/F2/F3 foundation or production editorial operation is complete.
