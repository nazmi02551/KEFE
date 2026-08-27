# ADR-0124 — Connected Alpha schema snapshot boundary

Status: Proposed / F4 candidate

Issue: #347

Parent: PR #346 / `7ace2eb3f9e1860f70adc8b9056005142ad9c6f3`

## Context

KEFE already has one canonical FastAPI + PostgreSQL backend and a linear Alembic migration authority. The Connected Alpha database environment is intentionally empty until the repository schema can be applied without introducing provider-generated tables, handwritten drift, or Product Preview data.

The current execution environment cannot directly connect to the external PostgreSQL host, while `services/api/migrations/env.py` already supports Alembic offline mode. That makes a generated SQL snapshot the safest transport boundary between repository authority and the future database-application step.

## Decision

The first Connected Alpha schema bootstrap will be derived from the repository's own command:

`alembic upgrade head --sql`

The snapshot is CI evidence only. Generation and application are separate operations.

The snapshot generator must:

1. use `services/api/alembic.ini` and the committed migration tree;
2. prove a single connected chain from `20260727_0001` to the head/count recorded
   by `connected-alpha-schema-snapshot.v1.json` (currently
   `20260827_0037` / 37 files);
3. fail when the committed migration graph drifts from that contract;
4. run in offline PostgreSQL-dialect mode without a live database connection;
5. produce a SHA-256 digest;
6. upload SQL + digest as one named CI artifact;
7. contain no database credential, real endpoint, Product Preview fixture, or provider-specific connection string.

## Database application boundary

Applying the SQL to the Connected Alpha database is a separate reviewed slice. Before application, the target must be rechecked as empty/expected, the artifact digest must match the exact reviewed source head, and post-application evidence must prove the Alembic head and schema inventory.

A generated SQL file is not permission to mutate production or alpha state automatically.

## Preserved architecture

This decision does not change:

- FastAPI as the canonical API runtime;
- PostgreSQL as the canonical production persistence boundary;
- Alembic as schema authority;
- Commit First or Blind First;
- immutable published CaseVersion;
- generic case-agnostic Flow runtime;
- Product Preview / production isolation;
- Collective Result / Signal separation;
- My KEFE descriptive-only policy.

## Consequences

Positive:

- no handwritten migration translation;
- no dependency on direct database network access from the current agent runtime;
- deterministic reviewable bootstrap artifact;
- artifact can be hashed and tied to an exact source head;
- hosting provider remains replaceable.

Costs:

- schema generation and schema application become two explicit steps;
- exact-head CI is required before the snapshot is trusted;
- future migration additions must update the snapshot contract's expected head/count.

## Non-claims

This ADR does not prove a migrated database, deployed API, externally reachable service, production durability, OTP delivery, SLO attainment, store distribution, F4 completion, or CAP-123 lifecycle promotion.
