# F4 Connected Alpha External Acceptance — 2026-08-09

Status: IMPLEMENTED_CANDIDATE / REAL_EXECUTION_BLOCKED / EXACT_HEAD_CI_PENDING

Issue: #351

Parent: PR #350 / `a0989c27ad1c3f430e08ecc9ff6c0ba7a9350215`

## Purpose

Define one repeatable, provider-neutral proof that a deployed KEFE Connected Alpha is genuinely shared multi-user state rather than Product Preview, local execution or compile-only evidence.

## Implemented candidate

- external operator tool `services/api/tools/run_connected_alpha_acceptance.py`;
- HTTPS-only, non-local/non-reserved endpoint validation;
- explicit `--case-id` and `--allow-write` gates;
- exact 40-hex deployed source commit required for evidence identity;
- `/health` and `/ready` probes before writes;
- dedicated Case inspection and typed required SINGLE_CHOICE discovery;
- exactly two independent guest actors;
- both drafts written before the second actor commits;
- actor 1 commit → RAW reveal;
- actor 2 commit → exact `n + 1` assertion;
- actor 1 reread → same post-second-commit sample and option payload;
- TRUSTED reveal rejected as unsuitable for this live RAW proof;
- both test actors deleted in `finally` through canonical privacy self-service;
- cleanup failure makes the acceptance fail;
- redacted evidence record contains no bearer token, actor ID or selected option;
- exact deployed source SHA recorded;
- networkless fake-transport tests for success, guardrails, TRUSTED rejection and cleanup;
- versioned contract, ADR-0126 and executable checker.

## Why real execution is blocked

The canonical production API is not deployed to an approved HTTPS origin yet. The alpha PostgreSQL schema is also intentionally not applied until the exact canonical Alembic snapshot is generated and reviewed.

Therefore the external tool is **not executed** in this checkpoint. Running it against Product Preview, localhost, an `.invalid` endpoint or an arbitrary public Case would invalidate the evidence boundary.

## Data hygiene

A real run must use a dedicated acceptance Case with no TRUSTED snapshot. The harness creates exactly two guest actors and sends only the required decision response. It sends no private reason, confidence answer, demographic or profile data.

Every created actor is deleted through `DELETE /v1/me` with exact actor-bound confirmation. The evidence record excludes actor identifiers and credentials.

## Evidence meaning

If the future real run succeeds, it proves only that, at that exact source SHA and observed time:

- the HTTPS API was reachable and ready;
- two independent guest clients could commit through the canonical API;
- the second commit changed the shared RAW population by exactly one;
- the first actor could reread the same shared result;
- test actors were privacy-cleaned.

It does not prove broad availability, load capacity, representativeness, Signal/Impact, SLO attainment, store readiness or complete F4.

## GitHub Actions state

Recent Connected Alpha heads still have no workflow runs due the existing Actions/webhook incident, including feature-branch push attempts. The dedicated CI for this slice is networkless and will only validate the harness itself; it never receives a real alpha endpoint and never performs external writes.

No exact-head PASS is claimed until runs exist and succeed.

## Next sequence

1. recover exact-head CI execution;
2. generate/review the canonical Alembic SQL snapshot from PR #348;
3. apply it first to the isolated Neon validation branch and verify head/schema;
4. apply the reviewed schema to the isolated alpha database under a separate bootstrap decision;
5. deploy the exact reviewed FastAPI image to an approved HTTPS host;
6. create/publish a dedicated acceptance Case with no TRUSTED snapshot;
7. execute this harness with exact deployment SHA;
8. review the redacted acceptance record before any reachability/status promotion.
