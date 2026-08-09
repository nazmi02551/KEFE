# F4 Connected Alpha Mobile Boundary — 2026-08-09

Status: IMPLEMENTED_CANDIDATE / EXACT_HEAD_CI_PENDING

Issue: #345

Parent: PR #344 / `af4d248ee3aee6d4f5b9ce36a7e8ca4d89e78172`

## What this checkpoint adds

- strict Connected Alpha API configuration in `AppConfig`;
- separate `main_connected_alpha.dart` entrypoint;
- explicit use of the canonical HTTP runtime and secure stores;
- executable rejection of local, emulator, reserved and non-HTTPS targets;
- timeout bounds for the Connected Alpha HTTP client;
- Product Preview exclusion from the Connected Alpha composition;
- versioned contract and ADR;
- focused configuration tests;
- dedicated compile-only CI with no installable artifact publication.

## Runtime separation

### Local/development

`main.dart` retains the existing `AppConfig.fromEnvironment()` behavior so local development is not forced through Connected Alpha restrictions.

### Product Preview

`main_preview.dart` remains the phone-review environment with Preview repositories and memory-isolated state. It is not a network fallback and is not evidence of multi-user operation.

### Connected Alpha

`main_connected_alpha.dart` uses the production-family `KefeApp` and canonical HTTP repository composition. It requires a real externally supplied HTTPS base URL and rejects known local/reserved targets.

## Artifact state

No Connected Alpha APK is approved for handoff yet. The dedicated workflow may compile the entrypoint to prove repository/build integrity, but removes the generated file and publishes nothing.

A future artifact requires a real approved HTTPS endpoint and a separately reviewed reachability/deployment step.

## Infrastructure preparation outside repository claims

An isolated PostgreSQL project has been provisioned for the future Connected Alpha environment. This does not change repository reachability status and is not production durability evidence. The database remains separate from Product Preview. Canonical schema migration must be performed through the repository Alembic chain before application traffic is allowed.

No database credential or provider-specific connection value is committed to this repository.

## Evidence currently available

Repository changes are present on the child branch. Exact-head GitHub Actions evidence is still pending. The wider repository Actions queue is currently affected by the existing GitHub Actions/webhook delay; absence of a run is not PASS and not repository failure.

## Preserved boundaries

- Commit First;
- Blind First / pre-result isolation;
- immutable published CaseVersion;
- generic composable Flow runtime;
- Product Preview / connected runtime isolation;
- Collective Result is not automatically Signal;
- My KEFE remains descriptive-only;
- no automatic review/approval/publication;
- TR/EN, theme, accessibility and Reduce Motion remain continuous requirements.

## Explicit non-claims

This checkpoint does not prove:

- a deployed Connected Alpha API;
- external HTTPS reachability;
- migrated or durable alpha PostgreSQL state;
- real OTP delivery;
- multi-phone shared-state acceptance;
- deployed SLO/observability/paging;
- human usability acceptance;
- store distribution;
- F4 completion;
- CAP-123 lifecycle promotion.

## Next evidence sequence

1. obtain exact-head CI for PR #344 and this child slice;
2. run canonical Alembic migrations against the isolated alpha PostgreSQL database;
3. deploy the exact reviewed FastAPI image to a real HTTPS host;
4. externally verify `/health`, `/ready` and a controlled canonical read/write path;
5. bind the Connected Alpha mobile build to that approved endpoint;
6. verify two independent phones observe shared server state before any wider alpha handoff.
