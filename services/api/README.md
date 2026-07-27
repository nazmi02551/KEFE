# KEFE API

FastAPI modular monolith. Capability modules own domain/application behavior behind declared ports; infrastructure/provider adapters remain outside domain code.

## Current M0 vertical slice

The executable product path is:

`Guest Identity → Explore → Case → Typed Weigh → Private Reason → Commit → Reveal`

The same decision application service supports two persistence adapters:

- `memory` — default for fast unit tests and isolated development
- `postgres` — durable adapter selected with runtime configuration

### Implemented invariants

- Guest users receive opaque revocable bearer credentials; client-supplied actor IDs are not trusted.
- Only bearer-token hashes are persisted server-side; raw guest tokens are returned to the client and are not stored.
- Commit First: Reveal is forbidden before a confirmed commit.
- Session ownership is actor-scoped.
- Required questions must be answered before commit; optional questions do not silently become blockers.
- Question behavior is versioned through `response_type` + `response_schema` and validated server-side.
- Question display order is explicit editorial data, not UUID or insertion order.
- The first typed question contracts are `SINGLE_CHOICE` and `CONFIDENCE`.
- Private reason capture is schema-driven and actor-scoped.
- Reason tags are validated against the CaseVersion policy, deduplicated and bounded.
- Optional short reason text is technically capped and enters moderation state `PENDING`; tags-only reasons use `NOT_REQUIRED`.
- Reasons remain `PRIVATE` in this slice; there is no public comment feed, ranking or cross-user reason read model.
- Draft reasons are editable only before Commit and become immutable with the decision lifecycle.
- Sessions are pinned to a CaseVersion; stale versions are blocked.
- Consumer reveal returns the Trusted result layer.
- Domain failures use stable machine-readable error codes.
- Draft response/reason updates and commit use row-locked write boundaries in PostgreSQL.
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

### Demo Case

The development bootstrap exposes one low-risk DILEMMA Case through fixed UUID fixtures. It contains a required `SINGLE_CHOICE` question, an optional schema-driven `CONFIDENCE` question and a private reason policy with structured tags plus optional short text. These are development fixtures, not product identifiers or global product defaults.

### Next backend slices

1. safe Perspective read model after Commit, beginning with moderation-approved opposing reasons rather than popularity-only ranking.
2. Context/source read contracts with progressive disclosure and no result leakage.
3. outbox backlog/dead-letter observability and audited replay tooling.
4. expand CaseVersion/content persistence toward the full physical contract.
5. query-budget and latency regression tests.
