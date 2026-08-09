# F4 Connected Alpha Database Environment — 2026-08-09

Status: INFRASTRUCTURE_PROVISIONED / SCHEMA_MIGRATION_PENDING

## Purpose

Record the existence of an isolated PostgreSQL environment for the first controlled Connected Alpha without converting infrastructure provisioning into a production-readiness claim.

## State

- an isolated PostgreSQL project exists for Connected Alpha preparation;
- it is separate from Product Preview and carries no Preview fixture authority;
- no database credential, connection string or provider secret is committed to Git;
- canonical KEFE schema migration has not yet been claimed complete;
- no application traffic is authorized until the repository Alembic chain is applied and verified;
- production reachability inventory remains unchanged.

## Required next proof

1. apply the repository's exact Alembic migration chain through `alembic upgrade head` from an exact reviewed runtime;
2. verify exactly one migration head and expected canonical catalog;
3. record the reviewed application commit SHA used for migration;
4. bind the API runtime through secret-managed `KEFE_DATABASE_URL` only;
5. verify `/ready` against PostgreSQL after deployment;
6. keep database provider identity out of domain/application semantics.

## Non-claims

Provisioning alone does not prove schema correctness, durability, backups, recovery, security posture, production reachability, deployed SLOs, Connected Alpha readiness, F4 completion or CAP-123 lifecycle promotion.
