# ADR-0122: Provider-neutral production API runtime boundary

- Status: Accepted for deployment-boundary preparation only
- Date: 2026-08-09
- Foundation wave: F4
- Capabilities: CAP-092, CAP-123
- Issue: #343
- Parent stack: PR #342 and its ancestors

## Context

The canonical KEFE backend already exists as the FastAPI modular monolith with
PostgreSQL persistence. The mobile production entrypoint already uses the
canonical HTTP repository. The F4 reachability inventory correctly records the
production API as `NOT_CONFIGURED`, because there is no approved externally
reachable HTTPS deployment yet.

Creating a second backend or embedding a hosting vendor into domain/application
code would fragment the architecture and violate the existing continuation
protocol. The next Connected Alpha step is therefore to make the existing
canonical API safely deployable while keeping provider choice reversible and
external reachability claims evidence-based.

## Decision

### The existing FastAPI + PostgreSQL runtime remains canonical

No Supabase, Firebase, alternate API, or parallel persistence model is
introduced. Product, domain, flow, Commit First, Blind First, immutable
CaseVersion, publication, moderation, privacy, identity, and My KEFE semantics
remain unchanged.

### Production configuration fails closed

When `KEFE_ENVIRONMENT=production`:

- `KEFE_PERSISTENCE_BACKEND` must be `postgres`;
- `KEFE_DATABASE_URL` must be a PostgreSQL network URL;
- local/emulator/reserved database hosts are rejected;
- the development guest/account merge replay secret is rejected, including as a
  retained rotation key;
- OTP capture mode is rejected;
- disabling the OTP request abuse guard is rejected.

Development defaults remain available for local and unit-test workflows.

### Container packaging is provider-neutral

`services/api/Dockerfile` packages the canonical Python 3.12 runtime without
hardcoding a hosting vendor, production hostname, database credential, or paid
service. Proxy trust is not widened inside the image; a chosen deployment
platform must establish any trusted proxy boundary explicitly.

### Migrations are an explicit pre-deploy operation

Schema migration is intentionally separate from normal API process startup:

```text
alembic upgrade head
```

The API container does not auto-run migrations. This avoids each horizontally
scaled replica racing to own schema mutation. A deployment platform or operator
must run the migration command exactly once as a release/pre-deploy step before
new application replicas receive traffic.

### Liveness and readiness are separate

`GET /health` remains the public process-liveness surface.

`GET /ready` is an internal deployment probe, intentionally excluded from the
public OpenAPI contract. In PostgreSQL mode it performs a minimal `SELECT 1`
dependency probe. Failure returns a generic `503 not ready` and never returns
the underlying connection or secret-bearing exception detail.

### Reachability is not inferred from repository configuration

Adding a Dockerfile, production validators, or readiness probe does not make the
API externally reachable. The canonical reachability inventory must remain
`NOT_CONFIGURED` until a real production configuration exists. It may move to
`VERIFICATION_PENDING` only when a concrete deployment identity/endpoint exists,
and to `REACHABLE_VERIFIED` only after approved external HTTPS evidence is
captured according to ADR-0118.

## Consequences

- The first Connected Alpha can use the current canonical backend rather than a
  replacement architecture.
- Production cannot silently fall back to in-memory persistence or development
  OTP/secret behavior.
- Deployment provider selection can prioritize a free-tier-compatible option
  without changing KEFE domain/application code.
- Database migration ownership is explicit and repeatable.
- Health probes distinguish process liveness from database readiness.
- External deployment, SLO, pager, store, and human/operator evidence remain
  separately governed.

## Preserved product and trust boundaries

This ADR does not change:

- Commit First or Blind First;
- immutable published CaseVersion behavior;
- the generic case-agnostic Flow runtime;
- Collective Result / Signal separation;
- provider/AI non-authority and no auto-publish rules;
- Product Preview / production data isolation;
- My KEFE descriptive-only and non-inference rules;
- TR/EN, theme, accessibility, or Reduce Motion contracts;
- CAP-123 lifecycle status.

## Non-goals and non-claims

This change does not:

- deploy or name a production hosting vendor;
- prove a public HTTPS endpoint is reachable;
- prove PostgreSQL production data exists or is durable;
- prove OTP provider delivery;
- prove deployed telemetry, SLO, error-budget, pager, RTO, or RPO evidence;
- publish a mobile store build;
- complete F4;
- promote CAP-123 to `IMPLEMENTED_PARTIAL` or `IMPLEMENTED_VERIFIED`.
