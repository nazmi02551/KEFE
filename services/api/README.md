# KEFE API

FastAPI modular monolith. Capability modules own domain/application behavior behind declared ports; infrastructure/provider adapters remain outside domain code.

## Current M0 vertical slice

The executable product path is:

`Guest Identity → Explore → Case → Typed Weigh → Private Reason → Commit → Reveal → Perspective`

The same decision application service supports two persistence adapters:

- `memory` — default for fast unit tests and isolated development
- `postgres` — durable adapter selected with runtime configuration

### Implemented invariants

- Guest users receive opaque revocable bearer credentials; client-supplied actor IDs are not trusted.
- Only bearer-token hashes are persisted server-side; raw guest tokens are returned to the client and are not stored.
- Commit First: Reveal and Perspective are forbidden before a confirmed Commit.
- Session ownership is actor-scoped.
- Required questions must be answered before Commit; optional questions do not silently become blockers.
- Question behavior is versioned through `response_type` + `response_schema` and validated server-side.
- Question display order is explicit editorial data, not UUID or insertion order.
- The first typed question contracts are `SINGLE_CHOICE` and `CONFIDENCE`.
- Private reason capture is schema-driven and actor-scoped.
- Reason tags are validated against the CaseVersion policy, deduplicated and bounded.
- Optional short reason text is technically capped and enters moderation state `PENDING`; tags-only reasons use `NOT_REQUIRED`.
- Participant reasons remain `PRIVATE`; the Perspective endpoint never reads `decision.private_reason`.
- Draft reasons are editable only before Commit and become immutable with the decision lifecycle.
- The first Perspective source is `EDITORIAL_HUMAN`, linked to the pinned CaseVersion and decision question.
- Perspective eligibility requires `PUBLISHED` + `ALLOWED` editorial content after Commit.
- `EDITORIAL_OPPOSITION_V1` selects items whose structured target differs from the viewer's committed `SINGLE_CHOICE` value.
- Perspective ordering uses explicit editorial priority and deterministic tie-breaking, not likes, popularity or engagement.
- Sessions are pinned to a CaseVersion; stale versions are blocked.
- Consumer reveal returns the Trusted result layer.
- Domain failures use stable machine-readable error codes.
- Draft response/reason updates and Commit use row-locked write boundaries in PostgreSQL.
- The same Commit `Idempotency-Key` is replay-safe, including concurrent retries.
- Competing different-key commits linearize to one successful Commit.
- A Commit idempotency key cannot silently identify another actor Commit command.
- Session state and its start/Commit outbox event are persisted in one transaction.
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

The development bootstrap exposes one low-risk DILEMMA Case through fixed UUID fixtures. It contains a required `SINGLE_CHOICE` question, an optional schema-driven `CONFIDENCE` question, a private reason policy and two moderation-approved editorial human perspectives representing the two structured choices. These are development fixtures, not product identifiers, final copy or global ranking defaults.

### Perspective boundary

`GET /v1/weigh-sessions/{session_id}/perspectives` is Bearer-protected and available only after Commit. The response identifies the decision axis, the viewer's committed value, the versioned selection policy and eligible editorial-human items with provenance/moderation metadata.

This endpoint deliberately does **not** expose another participant's private reason. Participant-reason visibility, consent, moderation thresholds, ranking methodology, AI clustering and persuasion/Bridge Score ordering require later explicit product and methodology contracts.

### Next backend slices

1. Context/source read contracts with progressive disclosure and no result leakage.
2. Content/Admin authoring and publication workflow for Cases, Questions and editorial Perspectives.
3. outbox backlog/dead-letter observability and audited replay tooling.
4. expand CaseVersion/content persistence toward the full physical contract.
5. query-budget and latency regression tests.
