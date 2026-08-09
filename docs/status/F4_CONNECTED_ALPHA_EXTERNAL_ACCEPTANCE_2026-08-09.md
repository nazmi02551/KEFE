# F4 Connected Alpha External Acceptance — 2026-08-09

Status: IMPLEMENTED_CANDIDATE / REAL_EXECUTION_BLOCKED / EXACT_HEAD_CI_PENDING

Issue: #351

Parent: PR #350 / `a0989c27ad1c3f430e08ecc9ff6c0ba7a9350215`

Current orchestration authority: ADR-0129 / core `API CI`

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
- each deletion receipt must match the test actor and confirm private-data deletion plus aggregate-contribution handling;
- malformed/negative cleanup receipt makes the acceptance fail;
- redacted evidence record contains no bearer token, actor ID or selected option;
- exact deployed source SHA recorded;
- networkless fake-transport tests for success, guardrails, TRUSTED rejection and cleanup-receipt failure;
- versioned contract `connected-alpha-external-acceptance.v1.json` v1.0.1, ADR-0126 and executable checker.

## Why real execution is blocked

The canonical production API is not deployed to an approved HTTPS origin yet. The alpha PostgreSQL schema is also intentionally not applied until the exact canonical Alembic snapshot is generated and reviewed.

Therefore the external tool is **not executed** in this checkpoint. Running it against Product Preview, localhost, an `.invalid` endpoint or an arbitrary public Case would invalidate the evidence boundary.

## Data hygiene

A real run must use a dedicated acceptance Case with no TRUSTED snapshot. The harness creates exactly two guest actors and sends only the required decision response. It sends no private reason, confidence answer, demographic or profile data.

Every created actor is deleted through `DELETE /v1/me` with exact actor-bound confirmation. Cleanup is successful only after the returned receipt matches that actor and explicitly confirms the existing privacy-deletion policy. The evidence record excludes actor identifiers and credentials.

## Evidence meaning

If the future real run succeeds, it proves only that, at that exact source SHA and observed time:

- the HTTPS API was reachable and ready;
- two independent guest clients could commit through the canonical API;
- the second commit changed the shared RAW population by exactly one;
- the first actor could reread the same shared result;
- both test actors returned verified privacy-cleanup receipts.

It does not prove broad availability, load capacity, representativeness, Signal/Impact, SLO attainment, store readiness or complete F4.

## GitHub Actions state

GitHub currently reports Actions disabled at the account level. This is not classified as a KEFE runtime failure and missing workflow runs are not PASS evidence.

Under ADR-0129, harness validation no longer has a dedicated feature workflow. The executable checker and networkless fake-transport tests are owned by the existing core `API CI`, which must execute on the exact reviewed head after GitHub restores Actions access. Core CI never receives a real Connected Alpha endpoint and never performs the external write acceptance automatically.

## Next sequence

1. restore account-level GitHub Actions execution;
2. run the consolidated exact-head API/Mobile core gates;
3. generate/review the canonical Alembic SQL snapshot from the consolidated API CI;
4. apply it first to the isolated Neon validation branch and verify head/schema;
5. apply the reviewed schema to the isolated alpha database under a separate bootstrap decision;
6. deploy the exact reviewed FastAPI image to an approved HTTPS host;
7. create/publish a dedicated acceptance Case with no TRUSTED snapshot;
8. execute this harness with exact deployment SHA;
9. review the redacted acceptance record before any reachability/status promotion.
