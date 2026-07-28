# ADR-0021 — Secured Admin HTTP for composable Content Configuration

**Status:** Accepted  
**Date:** 2026-07-28

## Context

ADR-0017 established the internal Admin HTTP boundary at `/internal/admin/v1`: opaque server-side Admin session cookie, same-session CSRF for state-changing browser requests, capability-first authorization, server-derived Admin/audit identity, no consumer-credential acceptance and no login/SSO provider coupling.

ADR-0018/ADR-0020 plus PR #49 now provide a versioned, immutable and durable Content Configuration aggregate containing Domain/Topic/Base Format/Modifier plus Primitive/Capability/FlowTemplateVersion registries. The next requirement is an Admin Studio application surface for reading and managing this aggregate without creating a second authentication/security model or exposing direct repository mutation.

## Decision

### Route boundary

Composable Content Configuration management is exposed only under:

`/internal/admin/v1/content-configuration`

It shares the existing Admin session and CSRF machinery. No configuration-specific login/token surface is introduced.

### Authorization

- All configuration read/manage operations require authenticated Admin assurance and `TAXONOMY_MANAGE`, except configuration audit read which requires `AUDIT_READ`.
- Mutating operations require same-session `X-KEFE-CSRF` verification before session activity touch or mutation, exactly as ADR-0017.
- The current approved Admin policy does **not** classify `TAXONOMY_MANAGE` as a recent-step-up capability. This ADR does not silently change that policy. A future requirement for step-up on configuration publication requires an explicit security-policy ADR/change.
- Request bodies cannot provide Admin subject, role, capability, actor_ref, audit identity, lifecycle metadata, version identity or created-by metadata.

### Application boundary

HTTP handlers call `SecuredContentConfigurationService`; they do not mutate `ContentConfigurationRepository` directly and do not implement authorization rules themselves.

`SecuredContentConfigurationService` owns the Admin-facing application-security boundary and delegates lifecycle/validation mutation logic to `ContentConfigurationService`. It may use the repository for authorized version/audit reads needed by the application facade.

The combined facade/domain-service boundary remains responsible for:
- capability enforcement,
- DRAFT-only mutation,
- validation,
- immutable publication,
- atomic publish/supersede through the repository,
- clone-based rollback,
- server-derived audit entries.

### Read surface

- `GET /current` — current PUBLISHED configuration.
- `GET /versions` — version history visible to configuration managers.
- `GET /versions/{version_id}` — one version.
- `GET /audit` — append-only configuration audit; requires `AUDIT_READ`.

Read operations never return Admin session/CSRF secrets.

### Mutation surface

- `POST /drafts` — clone current PUBLISHED configuration to a new DRAFT.
- `PUT /versions/{version_id}` — replace editable fields of an existing DRAFT.
- `POST /versions/{version_id}/publish` — validate and publish a DRAFT, atomically superseding the prior PUBLISHED version.
- `POST /versions/{version_id}/rollback-drafts` — clone a historical PUBLISHED/SUPERSEDED version into a new DRAFT; rationale required.

A client cannot directly set lifecycle state, version number, published timestamp, created_by, clone provenance or audit actor.

### Payload model

The editable payload contains registry/configuration semantics only:
- Domains, Topics, Base Formats, Modifiers and compatibility,
- Primitives,
- Capabilities and Primitive compatibility,
- FlowTemplateVersions and Steps,
- risk/claim/source/disclosure allow-lists.

Strict request schemas reject unknown fields.

### Error and concurrency semantics

Existing Content Configuration domain errors remain the source of validation/lifecycle behavior. Concurrent publication retains the repository's database transaction/one-published-version guarantees. HTTP does not add an alternate last-write-wins lifecycle.

## Consequences

- Admin Studio gains a secure configuration lifecycle without duplicating auth or coupling to an IdP/CMS vendor.
- Configuration management remains auditable and server-authoritative.
- The next slice can bind effective configuration/Flow provenance into CaseVersion publication using the same durable aggregate.
- Consumer/mobile Flow execution remains out of scope.
