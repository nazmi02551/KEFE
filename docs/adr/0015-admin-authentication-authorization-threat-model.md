# ADR-0015 — Admin authentication, authorization and threat-model boundary

**Status:** Accepted  
**Date:** 2026-07-28

## Context

KEFE now has a durable Content Authoring core and PostgreSQL publication boundary, but no Admin HTTP surface. Exposing create/edit/review/publish commands before defining the trust boundary would allow consumer identity, client-provided actor references or future vendor SDK choices to leak into authorization rules.

Admin access can change public content, source/claim status, risk controls and publication state. A compromised or over-privileged Admin session therefore has materially higher impact than a consumer session.

## Decision

### Separate principal and session domain

- Admin identity is a separate security domain from consumer `ActorPrincipal`.
- A consumer guest/account bearer token can never authenticate an Admin command.
- Admin authorization keys on an immutable internal `admin_subject_id`, never email, display name or external-provider username.
- External identity providers and SSO are adapters. Domain/application code does not import an IdP SDK.
- Every active Admin session must be backed by an authenticated subject, explicit role/capability assignments and MFA assurance.

### Capability-first authorization

Authorization is capability-based. Roles are named bundles for administration convenience; there is no implicit role hierarchy and no wildcard/superuser capability in the normal model.

Initial roles:

- `EDITOR`
- `REVIEWER`
- `PUBLISHER`
- `TAXONOMY_MANAGER`
- `ACCESS_ADMIN`

Initial capabilities:

- `CONTENT_CREATE`
- `CONTENT_EDIT`
- `CONTENT_SUBMIT_REVIEW`
- `CONTENT_REVIEW`
- `CONTENT_PUBLISH`
- `CONTENT_WITHDRAW`
- `SOURCE_VERIFY`
- `RISK_REVIEW`
- `TAXONOMY_MANAGE`
- `ADMIN_ACCESS_MANAGE`
- `AUDIT_READ`

All authorization is enforced server-side at the application boundary. UI visibility is not authorization.

### Session assurance

- MFA is mandatory for every Admin session.
- Publish, withdraw and access-management commands require a recent step-up assertion.
- The initial step-up freshness window is 15 minutes and is configuration, not domain code.
- Admin sessions have an absolute lifetime and idle timeout enforced by the session adapter. Initial defaults are 12 hours absolute and 30 minutes idle; deployment policy may tighten them.
- Revocation must take effect server-side without waiting for client token expiry.
- Browser Admin clients should use an opaque server-side session represented by `Secure`, `HttpOnly`, `SameSite` cookies; state-changing browser requests require CSRF protection. Raw long-lived bearer credentials must not be persisted in browser JavaScript storage.

### Separation of duties

- The reviewer approving a CaseVersion must be different from the subject that submitted that version for review.
- Publication requires `CONTENT_PUBLISH` and recent step-up. It may be performed by the reviewer in the initial operational model; higher-risk content may add stricter review-mode requirements through existing content policy.
- Access-management capability does not implicitly grant content publication.
- Capability assignment changes are themselves audited.

### Audit identity

- Authoring audit `actor_ref` is derived from the authenticated Admin principal as `admin:<admin_subject_id>`.
- HTTP clients will never be allowed to supply or override the audit actor reference.
- Authorization denials and privileged command attempts produce security audit signals without logging secrets or raw session tokens.

## Threat model

Primary threats and required controls:

- **Phishing / credential theft:** mandatory MFA, short sessions, step-up for high-impact commands.
- **Session theft:** opaque server-side sessions, secure cookie controls for web, revocation, idle/absolute expiry.
- **CSRF:** same-site session cookies plus anti-CSRF control on state-changing browser requests.
- **XSS credential extraction:** no Admin bearer credentials in JavaScript storage; CSP and output encoding remain deployment/UI requirements.
- **Privilege escalation:** explicit capability checks, no role inheritance, no wildcard capability, access changes audited.
- **Confused deputy / forged actor identity:** server-derived AdminPrincipal and audit identity; client actor references ignored.
- **IDOR:** every command authorizes capability and resolves resource server-side; possession of a CaseVersion ID grants no permission.
- **Self-review:** submitter cannot approve the same CaseVersion.
- **Draft leakage:** editorial and consumer schemas remain separated; Admin authorization does not change consumer visibility rules.
- **Audit tampering:** lifecycle audit remains append-only and database ordered; audit mutation is not an application capability.
- **Insider misuse:** least privilege, separate access-management role, audit-read capability and step-up for high-impact commands.

## Consequences

- The next Admin application layer can be built without selecting an SSO vendor first.
- Consumer authentication code cannot be reused as a shortcut for Admin authorization.
- Authoring commands gain a secured facade that derives audit identity and applies capabilities/step-up/separation-of-duties before calling the existing authoring service.
- No Admin HTTP endpoint is authorized by this ADR alone; the secured application facade and tests are established first, then an internal HTTP surface can be added in a subsequent slice.
