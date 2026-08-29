# F4 Connected Alpha Schema Snapshot — 2026-08-09

Status: IMPLEMENTED_CANDIDATE / EXACT_HEAD_CI_PENDING

Issue: #347

Parent: PR #346 / `7ace2eb3f9e1860f70adc8b9056005142ad9c6f3`

## Purpose

Create a deterministic transport artifact from the canonical Alembic migration authority before any schema is applied to the isolated Connected Alpha PostgreSQL environment.

## Canonical migration facts

- migration authority: `services/api/migrations`;
- root revision: `20260727_0001`;
- expected head: `20260829_0038`;
- current migration files: 38;
- generation mode: Alembic offline SQL;
- generation command: `alembic upgrade head --sql`;
- target dialect: PostgreSQL.

The validator derives continuity from `revision` and `down_revision`; numeric filename gaps or repeated date-local counters are not treated as sequence authority.

The 2026-08-27 session-renewal convergence extends the same linear authority
with `20260812_0035 -> 20260812_0036`. The snapshot contract is now the
validator's head/count source, so later migration additions must update the
reviewed contract rather than a parallel script constant.

The 2026-08-27 KEFE Today consumer projection extends that chain with
`20260812_0036 -> 20260827_0037`. It adds only the governed real-event boolean
to the existing immutable consumer CaseVersion table; it does not apply the
snapshot to any database.

The 2026-08-29 F5 analytics convergence extends the same authority with
`20260827_0037 -> 20260829_0038`. It adds the isolated, privacy-safe analytics
event projection store; it does not apply the snapshot to any database or
calculate a KPI.

## Artifact boundary

Expected artifact:

- `kefe-connected-alpha-schema.sql`;
- `kefe-connected-alpha-schema.sha256`;
- GitHub Actions artifact name: `kefe-connected-alpha-schema-snapshot`.

The artifact is repository/CI evidence only. It does not mutate a database and is not deployment, durability, reachability, SLO, or release evidence.

## Current database state

The isolated Connected Alpha PostgreSQL environment was previously verified with zero user tables. This slice does not change that state.

No database credential, Neon connection string, API endpoint, or provider secret is committed in this branch.

## Actions incident handling

The existing pull-request Actions/webhook path has produced no run for the parent Connected Alpha heads. This slice therefore contains a temporary feature-branch push trigger in its dedicated workflow so a fresh commit can request schema-snapshot generation without weakening any production gate.

If an exact-head run succeeds, the temporary feature-branch trigger should be removed in a follow-up commit while retaining normal `pull_request`, `workflow_dispatch`, and `main` behavior.

Absence of a run is not PASS and is not repository failure.

## Preserved invariants

- Commit First;
- Blind First / pre-result isolation;
- immutable published CaseVersion;
- generic case-agnostic Flow;
- Product Preview / production isolation;
- one canonical backend;
- Collective Result is not automatically Signal;
- My KEFE remains descriptive-only.

## Non-claims

This checkpoint does not prove:

- schema applied to alpha PostgreSQL;
- database durability/backups;
- deployed FastAPI;
- external HTTPS reachability;
- real OTP delivery;
- two-phone shared-state acceptance;
- deployed observability/SLO/paging;
- store distribution;
- F4 completion;
- CAP-123 lifecycle promotion.

## Next evidence sequence

1. obtain an exact-head schema snapshot CI run;
2. download and verify SQL + SHA-256 artifact;
3. reverify the isolated alpha DB is still empty/expected;
4. apply the exact artifact in a separately reviewed database-bootstrap slice;
5. verify Alembic head, schemas and required tables after application;
6. only then proceed to API deployment/reachability.
