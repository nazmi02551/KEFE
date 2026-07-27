# KEFE API

FastAPI modular monolith. Capability modules own domain/application behavior behind declared ports; infrastructure/provider adapters remain outside domain code.

## M0 vertical slice

The first executable product slice is:

`Case → Weigh → Commit → Reveal`

The same decision application service now supports two persistence adapters:

- `memory` — default for fast unit tests and isolated development
- `postgres` — durable adapter selected with runtime configuration

### Implemented invariants

- Commit First: Reveal is forbidden before a confirmed commit.
- Session ownership is actor-scoped.
- Commit is idempotent for the same `Idempotency-Key`.
- A second commit with a different idempotency key is rejected.
- Required questions must be answered before commit.
- Sessions are pinned to a CaseVersion; stale versions are blocked.
- Consumer reveal returns the Trusted result layer.
- Domain failures use stable machine-readable error codes.
- Session state and its start/commit outbox event are persisted in one transaction.

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

The default remains `memory`, so PostgreSQL is opt-in until local/dev environment orchestration is fully standardized.

### Demo IDs

The development bootstrap exposes one low-risk DILEMMA seed through fixed UUIDs in `modules/decision/bootstrap.py`. These are fixtures only, not product identifiers.

### Next persistence hardening

1. database compare-and-set / row-lock protection for competing commit requests
2. contract patch for explicit `commit_idempotency_key`
3. outbox publisher worker and retry policy
4. richer CaseVersion/question schema from the full physical contract
5. performance/query-budget integration tests
