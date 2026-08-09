# ADR-0123 — Connected Alpha mobile runtime boundary

Status: Accepted for stacked implementation

Date: 2026-08-09

Issue: #345

Parent runtime boundary: ADR-0122 / PR #344

## Context

KEFE already has three materially different execution concerns:

1. ordinary local/development composition;
2. Product Preview, which intentionally uses preview repositories and memory-isolated state for phone review;
3. the future Connected Alpha, which must talk to the canonical FastAPI + PostgreSQL runtime over a real externally configured HTTPS endpoint.

The current production mobile shell is intentionally compile-only while `canonical-api-production` remains `NOT_CONFIGURED`. Product Preview must not become a fallback for a connected build, and a placeholder such as `https://beta-api.invalid/` must never be accepted as a real Connected Alpha target.

## Decision

Introduce a separate `main_connected_alpha.dart` entrypoint and a strict Connected Alpha `AppConfig` constructor.

The Connected Alpha entrypoint:

- uses `KefeApp`, not `ProductPreviewApp`;
- uses the existing canonical HTTP repository composition;
- reuses secure credential and persistent decision-draft stores;
- does not import or compose Preview repositories, Preview account/privacy/progress/media adapters, or Preview memory stores;
- requires an externally supplied `KEFE_API_BASE_URL`;
- fails closed unless that URL is absolute HTTPS with a non-local, non-reserved host;
- rejects credentials, query and fragment material in the base URL;
- rejects localhost, loopback, Android emulator alias, wildcard and `.invalid` targets;
- bounds the HTTP timeout to 3–60 seconds.

The existing `AppConfig.fromEnvironment()` remains unchanged for local-development compatibility. Product Preview remains unchanged and isolated.

## Artifact policy

Until a real Connected Alpha endpoint has been deployed and approved:

- CI may compile the Connected Alpha entrypoint as repository evidence;
- CI must not upload an installable Connected Alpha APK;
- compile success must not change reachability inventory state;
- no release/store/deployment claim may be inferred.

Once a real deployment identity exists, artifact publication requires a separate reviewed change that binds the exact approved HTTPS endpoint and preserves ADR-0118 reachability evidence rules.

## Alternatives rejected

### Reuse `main_preview.dart`

Rejected. It would collapse Preview/production isolation and could convert demo data into false connected-alpha evidence.

### Replace the canonical backend with Supabase/Firebase or another mobile-first backend

Rejected. PR #344 already prepares the canonical FastAPI + PostgreSQL runtime. A parallel backend would duplicate domain/application authority and violate the single-delivery-line architecture.

### Hardcode a temporary host in the app

Rejected. Hosting must remain an external deployment concern. Repository code owns validation and composition, not vendor identity or credentials.

## Consequences

- Local development stays convenient.
- Product Preview remains independently testable.
- Connected Alpha becomes an explicit third runtime boundary rather than a convention around build flags.
- A misconfigured alpha build fails before creating misleading network behavior.
- The first real alpha artifact remains blocked on actual endpoint and external evidence.

## Preserved invariants

This ADR does not change:

- Commit First;
- Blind First / pre-result isolation;
- immutable published CaseVersion;
- generic case-agnostic Flow runtime;
- Collective Result / Signal separation;
- My KEFE descriptive-only / non-inference;
- Content Authoring/review/publication authority;
- TR/EN, theme, accessibility, Reduce Motion and low-end Android requirements;
- Product Preview / production data isolation.

## Evidence boundary

Repository code, tests and CI can prove configuration and composition rules. They cannot prove a deployed endpoint, external reachability, PostgreSQL durability, provider delivery, deployed SLOs, human usability, operator rollback, store distribution, F4 completion or CAP-123 lifecycle promotion.
