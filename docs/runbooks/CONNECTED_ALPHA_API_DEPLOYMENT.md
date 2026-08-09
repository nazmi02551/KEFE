# KEFE Connected Alpha — API deployment runbook

Status: provider-neutral preparation; no production endpoint is claimed by this document.

Authority: ADR-0122 and `docs/contracts/production-api-runtime.v1.json`.

## 1. Initial topology

The first controlled Connected Alpha uses **one API replica**.

Reason: canonical decision/content/identity persistence is PostgreSQL-backed in production,
but guest admission currently uses a process-local `InMemoryGuestIssueRateLimiter`. Multiple
API replicas would therefore weaken consistency of that abuse-control boundary. Horizontal
scaling requires a separately reviewed durable/distributed guest admission limiter or an
approved equivalent edge control.

This limitation is an operational constraint, not permission to introduce a parallel backend.

## 2. Required production inputs

Supply all secrets through the chosen platform's secret manager/environment injection. Do not
commit production values to Git.

Required baseline:

```text
KEFE_ENVIRONMENT=production
KEFE_PERSISTENCE_BACKEND=postgres
KEFE_DATABASE_URL=<secret PostgreSQL network URL>
KEFE_ACCOUNT_MERGE_REPLAY_SECRET=<secret, non-development value>
KEFE_OTP_DELIVERY_MODE=DISABLED | HTTP
KEFE_OTP_REQUEST_GUARD_MODE=AUTO | ENFORCE
```

If OTP HTTP delivery is enabled, configure its endpoint and secret/bearer inputs according to
the existing OTP provider contracts. `CAPTURE` is forbidden in production.

Do not use localhost, emulator aliases, `.invalid` hosts, preview fixtures, or development
secrets as a production fallback.

## 3. Build the canonical image

From the repository root:

```text
docker build -t kefe-api:<immutable-revision> -f services/api/Dockerfile services/api
```

Use an immutable image revision derived from the reviewed commit SHA. Do not use mutable image
identity as deployment evidence.

## 4. Run schema migration as a release step

Before new API replicas receive traffic, run exactly one reviewed migration job against the
target PostgreSQL database:

```text
alembic upgrade head
```

The normal API process must not own schema migration. This prevents migration races between
replicas and keeps deployment/rollback decisions explicit.

Database downgrade is **not** an automatic rollback mechanism. Any `alembic downgrade` must be
reviewed against data-loss and compatibility risk first.

## 5. Start the API process

The container starts the canonical application:

```text
uvicorn kefe_api.main:app --host 0.0.0.0 --port 8000
```

For the initial Connected Alpha, keep the API replica count at one.

Configure any trusted reverse-proxy/forwarded-header behavior at the selected infrastructure
boundary; the canonical image intentionally does not trust arbitrary forwarded headers.

## 6. Probe in this order

1. `GET /health` — process liveness only.
2. `GET /ready` — dependency readiness; PostgreSQL must answer the minimal readiness query.
3. External HTTPS probe through the real production hostname.
4. A controlled anonymous/guest mobile read path.
5. A controlled decision write/read-back path using non-preview data.

A 200 from `/health` alone is not production readiness. A successful container build or local
probe is not external reachability evidence.

## 7. Reachability inventory state

Before a real deployment identity exists:

```text
canonical-api-production = NOT_CONFIGURED
```

After a concrete HTTPS deployment exists but before approved external evidence:

```text
canonical-api-production = VERIFICATION_PENDING
```

Only after the ADR-0118 external proof boundary is satisfied may it become:

```text
canonical-api-production = REACHABLE_VERIFIED
```

Do not edit this status optimistically.

## 8. Rollback boundary

Application rollback means restoring the previously approved immutable API image while keeping
the database at a schema version compatible with that image. If a migration is not backward
compatible, rollback requires an explicit migration/data plan before deployment.

Never switch production traffic to Product Preview, memory persistence, preview fixtures, or a
secondary backend as a rollback shortcut.

## 9. Still required after this runbook

This runbook does not prove or complete:

- a selected production hosting/database provider;
- an externally reachable HTTPS API;
- production PostgreSQL durability/backups;
- real OTP delivery;
- deployed telemetry/SLO/error-budget evidence;
- external pager delivery;
- human incident/rollback exercise;
- mobile store distribution;
- F4 completion or CAP-123 lifecycle promotion.
