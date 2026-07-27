# KEFE API

FastAPI modular monolith. Capability modules own domain/application behavior behind declared ports; infrastructure/provider adapters remain outside domain code.

## M0 vertical slice

The first executable product slice is now:

`Case → Weigh → Commit → Reveal`

Current implementation deliberately uses an in-memory adapter so domain invariants can be proven before PostgreSQL persistence is wired in. The next adapter will implement the same `DecisionRepository` port against PostgreSQL without changing domain/application behavior.

### Implemented invariants

- Commit First: Reveal is forbidden before a confirmed commit.
- Session ownership is actor-scoped.
- Commit is idempotent for the same `Idempotency-Key`.
- A second commit with a different idempotency key is rejected.
- Required questions must be answered before commit.
- Sessions are pinned to a CaseVersion; stale versions are blocked.
- Consumer reveal returns the Trusted result layer.
- Domain failures use stable machine-readable error codes.

### Demo IDs

The development bootstrap currently exposes one low-risk DILEMMA seed through fixed UUIDs in `modules/decision/bootstrap.py`. These are fixtures only, not product identifiers.

### Next adapter slice

1. Alembic migration baseline
2. PostgreSQL repository adapter
3. transactional commit + outbox event
4. integration tests against PostgreSQL
5. Docker local development stack
