# Secured Admin Editorial Projection HTTP — Slice 34 Candidate

**Issue:** #186  
**Capabilities:** CAP-061, CAP-062, CAP-065  
**Base:** `feature/reviewed-proposal-source-slice33`  
**Status:** candidate; exact-head CI and OpenAPI reconciliation pending

## Candidate boundary

This slice exposes the verified reviewed Candidate Case -> existing Content Authoring DRAFT projection through the existing internal Admin session and CSRF boundary.

Included:

- `POST /internal/admin/v1/candidate-proposals/{candidate_proposal_id}/projection`;
- existing `kefe_admin_session` cookie resolution;
- existing `X-KEFE-CSRF` same-session verification before mutation;
- dedicated `CONTENT_PROJECT` authorization through `SecuredEditorialProjectionService`;
- strict request schema with no actor/admin/role/capability/lifecycle fields;
- paired explicit Flow code/version validation;
- server-derived audit actor from `AdminPrincipal`;
- immutable projection lineage response with `DRAFT` and `replayed`;
- same-input idempotent replay;
- memory security/replay tests;
- PostgreSQL session + reviewed Proposal + projection + DRAFT/no-consumer-materialization test;
- Admin HTTP architecture fitness.

## Exclusions

No Admin UI, Proposal review HTTP, external provider/AI call, automatic projection, automatic authoring lifecycle transition, Case Builder, Flow Composer or phone-facing behavior is included.

Do not call PASS until exact-head OpenAPI reconciliation, API CI, PostgreSQL HTTP integration and active-stack regression gates succeed.
