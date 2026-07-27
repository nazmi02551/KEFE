# KEFE API

FastAPI modular monolith. Capability modules own domain/application behavior behind declared ports; infrastructure/provider adapters remain outside domain code.

## M0 vertical slice

The first executable product slice is:

`Case → Weigh → Commit → Reveal`

The same decision application service supports two persistence adapters:

- `memory` — default for fast unit tests and isolated development
- `postgres` — durable adapter selected with runtime configuration

### Implemented invariants

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

### Next backend slice

1. outbox publisher worker with retry/backoff and consumer idempotency contract
2. full OpenAPI synchronization and generated client model gate
3. richer CaseVersion/question schema from the full physical contract
4. query-budget and latency regression tests
5. replace temporary `X-Actor-Id` development identity with the guest/auth boundary
