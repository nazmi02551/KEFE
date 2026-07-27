# KEFE

KEFE is a global decision and perspective platform. This repository contains the product implementation, machine-readable contracts, technical architecture assets, and delivery tooling.

## Architecture

- Mobile: Flutter
- Web: Next.js
- Admin Studio: Next.js
- API: FastAPI modular monolith
- Primary data store: PostgreSQL
- Cache/ephemeral state: Redis
- Object storage: S3-compatible
- Search: PostgreSQL FTS first; OpenSearch only when justified by scale/use cases

The implementation follows ports/adapters, provider independence, configuration-driven architecture, event contracts, and a strict Commit First invariant.

## Repository layout

- `apps/mobile` — Flutter consumer application
- `apps/web` — public web/deep-link experience
- `apps/admin` — Admin Studio
- `services/api` — FastAPI modular monolith
- `packages` — shared contracts/tokens/localization/config/test fixtures
- `infra` — migrations, IaC, observability and security policy
- `docs` — ADRs, runbooks and generated/reference material
- `tools` — contract and architecture checks

## M0: Walking Skeleton

The first vertical slice is:

`Case → Weigh → Commit → Reveal`

A successful M0 must preserve Commit First, idempotent commit, immutable published CaseVersion semantics, typed errors, traceability, provider isolation, and graceful degradation of optional subsystems.

## Canonical documentation

Product decisions are governed by the KEFE documentation ecosystem. Machine-readable implementation contracts live under `docs/contracts` and are compatibility-checked in CI.
