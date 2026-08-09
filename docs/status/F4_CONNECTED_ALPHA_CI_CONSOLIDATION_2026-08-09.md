# F4 Connected Alpha CI Consolidation — 2026-08-09

## State

Candidate implementation on top of PR #357. GitHub Actions remains disabled at account level; exact-head CI is therefore pending and no PASS claim is made.

## Problem addressed

The Connected Alpha stack had accumulated six feature-specific workflow files while the repository already carried a large workflow inventory. Those files contained useful evidence but duplicated checkout, Python/Flutter setup, dependency installation and PR orchestration.

## Candidate convergence

Connected Alpha evidence is now assigned to two existing core gates:

### API CI

- production runtime contract;
- provider-neutral Docker build/import proof;
- canonical migration-chain validation;
- offline Alembic SQL snapshot + validation + SHA-256 artifact;
- live RAW contract;
- live RAW PostgreSQL test;
- external acceptance harness contract;
- networkless acceptance unit behavior;
- explicit no-real-alpha-endpoint CI boundary.

### Mobile CI

- Connected Alpha runtime validator;
- full mobile analyze/test including Connected Alpha configuration tests;
- compile-only Connected Alpha entrypoint proof;
- compile-proof APK deletion before Preview build;
- RAW methodology presentation validator/tests;
- RAW KEFE Gap interpretation validator/tests;
- existing Product Preview APK build/upload remains separate.

## Removed orchestration

The candidate branch removes:

- `.github/workflows/production-api-runtime.yml`
- `.github/workflows/connected-alpha-mobile-runtime.yml`
- `.github/workflows/connected-alpha-schema-snapshot.yml`
- `.github/workflows/live-raw-collective-result.yml`
- `.github/workflows/connected-alpha-external-acceptance.yml`
- `.github/workflows/raw-result-methodology-presentation.yml`

The underlying tests, contracts, tools and evidence boundaries remain.

## Guard

`docs/contracts/connected-alpha-ci-consolidation.v1.json` and `scripts/validate_connected_alpha_ci_consolidation.py` prevent the six dedicated workflows from reappearing and require their unique evidence to remain in the core gates.

Both API CI and Mobile CI use `cancel-in-progress: true` concurrency control to reduce obsolete duplicate work on rapidly changing refs.

## Important non-claims

This checkpoint does not claim:

- GitHub Actions access has been restored;
- the account restriction was caused by workflow count;
- exact-head CI has passed;
- the schema has been applied to Neon;
- the API is externally deployed;
- Connected Alpha is distributable;
- RAW is representative or Signal/Impact;
- F4 or CAP-123 is complete.

## Next evidence after Actions restoration

1. consolidated API CI creates jobs and passes on the exact head;
2. consolidated Mobile CI creates jobs and passes on the exact head;
3. schema snapshot artifact is generated from the canonical Alembic chain;
4. only after review, apply that artifact/migration authority to the isolated validation PostgreSQL branch;
5. continue to real HTTPS deployment and the external two-actor acceptance proof.
