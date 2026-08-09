# ADR-0129 — Connected Alpha verification lives in core CI gates

- Status: Candidate
- Date: 2026-08-09
- Wave: F4
- Related: #353, #358, PRs #344–#357

## Context

The Connected Alpha stack accumulated six feature-specific GitHub Actions workflow files. Each file carried useful evidence, but each also repeated checkout, runtime setup, dependency installation and event orchestration. The repository already has a large workflow inventory, and the account-level Actions restriction made continued one-workflow-per-slice growth an unacceptable operational pattern.

The evidence itself remains necessary. The orchestration shape does not.

## Decision

Connected Alpha verification SHALL be consolidated into the existing core workflows:

- `.github/workflows/api-ci.yml`
- `.github/workflows/mobile-ci.yml`

The following dedicated workflow files are removed and forbidden from reappearing:

1. `production-api-runtime.yml`
2. `connected-alpha-mobile-runtime.yml`
3. `connected-alpha-schema-snapshot.yml`
4. `live-raw-collective-result.yml`
5. `connected-alpha-external-acceptance.yml`
6. `raw-result-methodology-presentation.yml`

## API CI authority

API CI now owns repository evidence for:

- production runtime guardrails and readiness;
- provider-neutral Docker packaging and canonical app import;
- canonical Alembic migration-chain validation;
- offline SQL snapshot generation, validation and SHA-256 artifact;
- live RAW Collective Result contract;
- live RAW PostgreSQL integration test;
- external two-actor acceptance harness contract and networkless unit behavior;
- the explicit prohibition on a real Connected Alpha endpoint in CI.

The offline schema artifact remains evidence only and does not authorize or perform database mutation.

## Mobile CI authority

Mobile CI now owns repository evidence for:

- fail-closed Connected Alpha endpoint configuration;
- Connected Alpha configuration tests;
- compile-only `main_connected_alpha.dart` proof;
- deletion of the compile-proof APK before any upload step;
- RAW methodology presentation contract and tests;
- RAW KEFE Gap interpretation boundary and tests;
- the existing Product Preview build and its separately labeled preview artifact.

Only Product Preview is uploaded by this gate until a real Connected Alpha endpoint has separate reviewed reachability evidence.

## Run control

Both core workflows use concurrency cancellation so a newer commit on the same ref supersedes obsolete in-progress work.

New feature slices SHOULD add executable contracts/tests to an existing core gate rather than creating a standalone workflow. A new top-level workflow requires an explicit architecture reason that cannot be satisfied by an existing gate.

## Preserved evidence hierarchy

- repository/CI evidence is not deployed evidence;
- a successful container build is not external reachability;
- an offline migration snapshot is not an applied database migration;
- a Connected Alpha compile proof is not a distributable alpha artifact;
- fake-transport acceptance tests are not external shared-state proof;
- RAW Collective Result remains descriptive and is not Signal/Impact;
- Product Preview remains isolated from production.

## Consequences

The Connected Alpha stack adds zero dedicated workflow files while retaining its evidence. The number of workflow-run orchestration events is reduced, repeated setup is removed, and future feature verification has a clear default home.

This ADR does not diagnose why GitHub disabled Actions for the account and does not claim that consolidation alone will cause GitHub to restore access.

## Verification

`scripts/validate_connected_alpha_ci_consolidation.py` checks that:

- all six dedicated files are absent;
- required API evidence remains in API CI;
- required mobile evidence remains in Mobile CI;
- both gates have concurrency cancellation;
- Connected Alpha compile output is deleted before the separate Preview artifact is built/uploaded.

Exact-head GitHub Actions PASS is still mandatory before merge or lifecycle promotion once account access is restored.
