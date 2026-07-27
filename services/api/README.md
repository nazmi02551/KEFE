# KEFE API

FastAPI modular monolith. Capability modules own domain/application behavior behind declared ports; infrastructure/provider adapters remain outside domain code.

## M0 vertical slice

The first executable product slice is:

`Guest Identity → Case → Weigh → Commit → Reveal`

The same decision application service supports two persistence adapters:

- `memory` — default for fast unit tests and isolated development
- `postgres` — durable adapter selected with runtime configuration

### Implemented invariants

- Guest users receive opaque revocable bearer credentials; client-supplied actor IDs are not trusted.
- Only bearer-token hashes are persisted server-side; raw guest tokens are returned to the client and are not stored.
- Commit First: Reveal is forbidden before a confirmed commit.
- Session ownership is actor-scoped.
- Required questions must be answered before commit.
- Sessions are pinned to a CaseVersion; stale versions are blocked.
- Consumer reveal returns the Trusted result layer.
- Domain failures use stable machine-readable error codes.
- Draft response updates and commit use a row-locked write boundary in PostgreSQL.
- The same commit `Idempotency-Key` is replay-safe, including concurrent retries.
- Competing different-key commits linearize to one successful commit.
- A commit idempotency key cannot silently identify another actor commit command.
- Session state and its start/commit outbox event are persisted in one transaction.
- Decision lifecycle outbox rows have database uniqueness guards.
- Outbox transport is provider-neutral and runs outside the request transaction.
- Outbox workers use bounded batches, leases, exponential backoff and dead-letter state.
- Delivery semantics are at-least-once; downstream consumers must be idempotent by `event_id`.

## Local PostgreSQL

From the repository root:

```bash
docker compose -f infra/local/compose.yaml up -d postgres
```

Then from `services/api`:

```bash
export KEFE_DATABASE_URL='postgresql+psycopg://kefe:kefe@localhost:5432/kefe'
alembic upgrade head
python -m kefe_api.infrastructure.seed_demo
export KEFE_PERSISTENCE_BACKEND=postgres
uvicorn kefe_api.main:app --reload
```

Create a guest credential before calling protected Decision endpoints:

```bash
curl -X POST http://localhost:8000/v1/identity/guest
```

Use the returned token as `Authorization: Bearer <token>`. `POST /v1/identity/guest` does not require phone/email and is intentionally separate from later account verification.

Run the event publisher in another terminal:

```bash
export KEFE_DATABASE_URL='postgresql+psycopg://kefe:kefe@localhost:5432/kefe'
python -m kefe_api.workers.outbox
```

The initial transport is structured logging. A managed queue or broker adapter can replace it behind `EventTransport` without changing decision domain/application code.

The default API persistence remains `memory`, so PostgreSQL is opt-in until local/dev environment orchestration is fully standardized.

### Demo IDs

The development bootstrap exposes one low-risk DILEMMA seed through fixed UUIDs in `modules/decision/bootstrap.py`. These are fixtures only, not product identifiers.

### Next backend slice

1. check in generated OpenAPI and enforce compatibility/drift gates
2. add guest-token issuance rate limiting and device-integrity adapter boundary
3. add outbox backlog/dead-letter observability and an audited replay command
4. expand CaseVersion/question persistence toward the full physical contract
5. add query-budget and latency regression tests
