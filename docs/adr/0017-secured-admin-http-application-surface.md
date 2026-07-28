# ADR-0017 — Secured Admin HTTP application surface

**Status:** Accepted  
**Date:** 2026-07-28

## Context

KEFE now has four separate layers that must remain distinct:

1. consumer identity and decision APIs,
2. mutable editorial authoring state,
3. a capability-gated `SecuredContentAuthoringService`, and
4. durable opaque Admin sessions with MFA/session assurance and session-bound CSRF verification.

The next step is to expose an internal browser-facing Admin application surface without allowing HTTP handlers to bypass authorization, invent audit identity, reuse consumer credentials, or turn CSRF/session protection into a UI convention.

External SSO/login integration is intentionally still provider-neutral and outside this slice. An upstream/future authentication adapter may issue a durable Admin session through `AdminSessionIssuer`; the authoring HTTP surface only consumes the opaque session.

## Decision

### Route boundary

- Admin authoring routes live under `/internal/admin/v1`.
- No consumer route accepts Admin credentials and no Admin route accepts consumer credentials.
- No Admin login/SSO endpoint is introduced by this ADR.
- The HTTP layer calls authoring commands only through `SecuredContentAuthoringService`.
- HTTP handlers never accept `actor_ref`, Admin subject ID, roles or capabilities from request bodies.

### Browser session contract

- Admin authentication is carried by the opaque `kefe_admin_session` cookie.
- The cookie value is treated as a secret and is never logged, echoed or returned by authoring endpoints.
- Deployment/authentication adapters must set the cookie `Secure`, `HttpOnly` and `SameSite=Strict` and scope it to the Admin application path.
- Read-only Admin requests require a valid Admin session.
- Every state-changing Admin request additionally requires the `X-KEFE-CSRF` header bound to the same opaque session.
- CSRF verification occurs before the request is allowed to execute a state change.

### Assurance and authorization

- `AdminSecurityService.authenticate()` remains the single session-assurance boundary for revocation, subject state, MFA, absolute expiry and idle expiry.
- Capability checks stay inside `SecuredContentAuthoringService`; route declarations do not replace domain/application authorization.
- `CONTENT_PUBLISH` and `CONTENT_WITHDRAW` continue to require recent step-up authentication through the existing policy.
- Reviewer/submitter separation remains enforced by the secured facade.

### Exposed first-slice operations

The initial HTTP surface exposes:

- session introspection,
- create Case + initial DRAFT CaseVersion,
- create correction/revision DRAFT,
- save DRAFT,
- submit for review,
- approve,
- reject with rationale,
- publish,
- withdraw with rationale,
- read lifecycle audit trail.

No taxonomy/access-management/SSO configuration endpoint is part of this slice.

### Serialization

- HTTP DTOs are explicit Pydantic models and map to provider-neutral authoring dataclasses.
- Published lifecycle state cannot be set through draft-save payloads; the authoring service remains authoritative for transitions.
- Server responses may return Admin workflow state and audit metadata, but never session or CSRF secrets.

## Consequences

- Browser UI code cannot mutate editorial tables directly.
- A stolen/forged consumer credential cannot authenticate Admin commands.
- A cross-site request without the session-bound CSRF secret cannot execute Admin mutations.
- A valid session without the required capability still receives a server-side denial.
- Step-up, separation-of-duties and publication validation remain independent of the transport layer.
- Future SSO providers can be integrated through session issuance without rewriting authoring authorization or HTTP workflow semantics.
