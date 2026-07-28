# ADR-0017 — Separate Admin HTTP application boundary

**Status:** Accepted  
**Date:** 2026-07-28

## Context

KEFE now has immutable Content Authoring, PostgreSQL publication materialization, a secured Admin application facade, and durable opaque Admin sessions with session-bound CSRF. The next boundary is HTTP. Mounting Admin commands directly into the consumer API would mix authentication schemes, expand the consumer OpenAPI surface, and make it easier to accidentally accept consumer bearer credentials or omit browser CSRF controls.

## Decision

- Admin HTTP is implemented as a **separate FastAPI sub-application** mounted at `/admin` by the modular monolith.
- The consumer application OpenAPI contract does not include Admin routes. Admin routes have an independent machine-readable surface contract and can later publish a dedicated Admin OpenAPI artifact.
- Admin HTTP authenticates only from the opaque `kefe_admin_session` cookie. `Authorization` consumer bearer credentials are ignored for Admin authentication and never used as fallback.
- State-changing Admin requests require `X-KEFE-CSRF`; verification must bind that token to the same opaque session cookie before application commands execute.
- The Admin principal is resolved server-side through `AdminSecurityService`. HTTP clients cannot submit `actor_ref`, role, capability, subject ID, MFA state or step-up timestamp.
- Every Content Authoring command is executed only through `SecuredContentAuthoringService`; routers cannot reach the authoring repository/database directly.
- Initial HTTP surface exposes Content Authoring lifecycle operations and audit reads. Authentication enrollment/login, role assignment/access management, taxonomy management and source/risk review workflows remain separate slices.
- Cookie issuance remains outside this application surface. A future trusted SSO/auth adapter sets the cookie using `Secure`, `HttpOnly`, appropriate `SameSite` and path/domain controls. This slice never returns session secrets.
- Admin responses use `Cache-Control: no-store`.
- CSRF is required for POST/PUT/PATCH/DELETE routes; safe GET audit/version reads require only Admin authentication.
- Reject and withdraw require non-empty rationale through existing domain rules. Publish/withdraw inherit recent step-up enforcement from the secured application facade.

## Consequences

- Consumer and Admin authentication/openapi surfaces remain structurally separated.
- A future Next.js Admin client can use cookie sessions and a CSRF header without browser bearer storage.
- Server-side capability checks, separation-of-duties, immutable publication and audit identity remain centralized below HTTP.
- Selecting an SSO provider later does not change the Admin HTTP command contract.
