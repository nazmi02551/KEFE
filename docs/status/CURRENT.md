# KEFE Current Project Checkpoint

**Updated:** 2026-09-10
**Repository:** `nazmi02551/KEFE`
**Default branch:** `main`
**Convergence issue:** Issue #287
**Next runtime issue:** Issue #291
**Delivery registry:** `docs/status/active-delivery-registry.v1.json`
**Registry version:** `1.1.0`

This is the durable engineering handoff for the full-vision convergence program. Chat history is supplementary only. Before continuing, read root `AGENTS.md`, the capability portfolio, the foundation program, ADR-0096, the executable convergence contract, this file, the live PR graph and exact-head CI.

## 1. Authority and scope

Published documentation authority remains **KEFE Documentation Ecosystem v3.3 ACTIVE** (18 canonical baseline documents at `docs/ecosystem_v3.3/KEFE_Documentation_Ecosystem_2026-07-28_v3.3_RECOVERY_R1/ACTIVE/`). The GitHub capability mirror contains 128 stable `CAP-*` records spanning Phase 1 through Phase 9+, Post-MVP and Post-PMF. A capability's presence in the portfolio does not mean it is accepted for immediate implementation or implemented.

Binding repository controls:

- `AGENTS.md`
- `docs/roadmap/CAPABILITY_PORTFOLIO.md`
- `docs/roadmap/capability-portfolio.v1.tsv`
- `docs/contracts/foundation-completion-program.v1.json`
- `docs/adr/0096-full-vision-delivery-convergence.md`
- `docs/contracts/full-vision-delivery-convergence.v1.json`
- `docs/status/active-delivery-registry.v1.json`

## 2. Canonical delivery line

### Common divergence base

- PR #232
- SHA: `2bb18cd3cc34c2dc6bcb84559948b1231e8e2308`

### Current canonical integration target

- PR #290
- Branch: `feature/admin-review-canonical-convergence`
- Exact verified SHA: `140960ac80881faec5841008eac9444ab67d9b7a`
- State: `CANONICAL_INTEGRATION_TARGET`

Exact-head evidence:

- Canonical Admin Review Convergence #7: PASS
- API CI #1330: PASS
- Mobile CI #911: PASS
- MVP Beta Gates #841: PASS
- Global Readiness #732: PASS
- Parent provider/evidence/ingestion workflows: PASS

PR #290 combines the current progressive consumer/mobile experience with typed, lineage-safe Admin Feed Item and Source Brief review operations. It is an internal review runtime, not a production or store release. The generated APK artifact is regression evidence only because no phone behavior changed in this slice.

### Previous consumer head

PR #286 / `ad825906388371eb9bb36b325abf36a2dd813c5c` remains a verified parent checkpoint but is no longer the canonical top.

### Adopted Admin source line

PR #264 / `80fbc887f16651949ec36819c440154bcfc278a8` is now `SUPERSEDED` as an integration target. Its compatible Feed Item and Source Brief review behavior was selectively adopted and reverified on PR #290. The divergent branch must not be merged as a second runtime.

## 3. Maintenance changes applied 2026-09-10 (local, not yet on a PR)

The following non-breaking maintenance changes were applied to the local working tree by an automated engineering agent. They do NOT alter any contracted product boundary, do not advance any F-wave milestone, and do not constitute a new CI-verified runtime checkpoint. They must be reviewed, committed and put through CI before being promoted to the canonical integration target.

### Signal module — hexagonal repository layer

**Problem:** Signal endpoints (`/v1/signals/*`) used hardcoded in-memory fixture lists at router module load time. There was no hexagonal port, no PostgreSQL adapter, and no way to inject live pipeline data.

**Changes:**
- `services/api/src/kefe_api/modules/signal/signal_models.py` — new: `QualifiedSignal`, `SignalComputationInput`, `SignalQualificationTier`, `SignalDispatchStatus` domain models (frozen dataclasses, invariant-enforced).
- `services/api/src/kefe_api/modules/signal/ports.py` — new: `SignalRepository` Protocol (hexagonal port).
- `services/api/src/kefe_api/modules/signal/in_memory.py` — new: `InMemorySignalRepository` (test/memory backend). Includes `seed_computation_input()` test helper.
- `services/api/src/kefe_api/infrastructure/postgres_signal.py` — new: `PostgresSignalRepository`. `get_computation_input()` reads from `decision.weigh_session` and `decision.response` (CORE_PRE_RESULT only). `save_qualified_signal()` uses ON CONFLICT upsert; `mark_signal_dispatched()` uses targeted UPDATE.
- `services/api/src/kefe_api/modules/signal/router.py` — rewritten: hardcoded lists replaced with `_get_signal_repository(request)` dependency. All six signal endpoints resolve the signal from `app.state.signal_repository` and return 404 if not found.
- `services/api/src/kefe_api/main.py` — `signal_repository` built via `build_signal_repository(settings)` and stored in `app.state.signal_repository`.
- `services/api/src/kefe_api/infrastructure/persistence.py` — `build_signal_repository()` added (memory → `InMemorySignalRepository`, postgres → `PostgresSignalRepository`).

### Impact module — hexagonal repository layer

**Problem:** Impact router seeded hardcoded institution responses and action milestones at module load time using plain dict services. No hexagonal port, no PostgreSQL adapter.

**Changes:**
- `services/api/src/kefe_api/modules/impact/ports.py` — new: `ImpactRepository` Protocol.
- `services/api/src/kefe_api/modules/impact/in_memory.py` — new: `InMemoryImpactRepository`.
- `services/api/src/kefe_api/infrastructure/postgres_impact.py` — new: `PostgresImpactRepository`. Institution responses are insert-only (ON CONFLICT DO NOTHING). Action milestones use `save_action()` + `update_action()` (UPDATE with rowcount guard).
- `services/api/src/kefe_api/modules/impact/router.py` — rewritten: `_get_impact_repository(request)` dependency; all hardcoded seeds removed; `propose_action` creates domain object directly; `update_action_progress` validates case_version_id match.
- `services/api/src/kefe_api/main.py` — `impact_repository` built and stored in `app.state.impact_repository`.
- `services/api/src/kefe_api/infrastructure/persistence.py` — `build_impact_repository()` added.

### Migration 0042 — signal + impact schema

- `services/api/migrations/versions/20260910_0042_signal_impact_schema.py` — new: creates `signal.qualified_signal` and `impact.institution_response` / `impact.action_milestone` tables with appropriate CHECK constraints and indexes. Revision chain: `20260829_0041` → `20260910_0042`.

### Test suite — repository-aware API tests

All signal and impact API tests that asserted against hardcoded fixture data were converted to inject an `InMemorySignalRepository` or `InMemoryImpactRepository` via `app.state` override after `create_app()`. Affected files:
- `test_signal_consensus_card_api.py`, `test_signal_health_card_api.py`, `test_signal_qualification_api.py`, `test_signal_scope_api.py`, `test_signal_versioning_api.py`, `test_signal_target_registry_api.py`, `test_contribution_classes_api.py`, `test_institution_response_api.py`, `test_action_follow_through_api.py`

All 838 non-postgres tests pass. 110 tests remain skipped (postgres integration, requires `KEFE_PERSISTENCE_BACKEND=postgres` + live DB). 1 pre-existing failure (`test_identity.py::test_invalid_bearer_is_rejected`) is unchanged and predates these changes.

### packages/ — shared workspace packages

Three new packages added (content only; no npm/pub build run):
- `packages/kefe-design-tokens/` — canonical semantic tokens JSON (dark/light color scales, typography, spacing, motion). Authority: Design System v1.1.0.
- `packages/kefe-locale/` — governed locale catalog with `tr.json` and `en.json` covering all current UI namespaces (common, decision, signal, impact, explore, my_kefe, account, settings, a11y, errors).
- `packages/kefe-test-fixtures/` — canonical UUID registry and deterministic signal/impact fixture JSON used by API tests.

### Infrastructure

- `infra/local/compose.yaml` — Redis (7-alpine, cache-only, no persistence) and MinIO (S3-compatible, three buckets: kefe-media, kefe-evidence, kefe-exports) added alongside existing Postgres service.
- `Makefile` — expanded with `api-test-postgres`, `api-test-fast`, `api-dev`, `admin-*`, `mobile-*`, `db-*`, `infra-*`, `packages-validate`, `check`, `check-all` targets.

## 4. Canonical Admin review behavior

The current canonical runtime contains:

- API 0.21 typed Feed Item list/detail;
- exact Proposal/run/schema/risk/configuration validation;
- exact SourceArtifact, content-hash and evidence-reference lineage validation;
- the existing generic Proposal review as the only review mutation;
- API 0.22 explicit accepted Feed Item normalization;
- a separate deterministic SOURCE_BRIEF ingestion run;
- exactly one review-required Source Brief Proposal;
- API 0.23 typed Source Brief list/detail;
- normalized-artifact and accepted parent-review lineage revalidation;
- exact additive API 0.20 → 0.23 isolation;
- memory and PostgreSQL idempotency/restart evidence.

It does not expose raw evidence bytes, credentials, secrets or backend object keys. It does not automatically review, accept, create a Candidate Case, project into authoring, approve or publish.

## 5. Current consumer/UI state

The current review runtime contains:

- progressive onboarding;
- layered Context;
- card-by-card questions, reason and review/Commit;
- Commit-gated Result;
- staged Result → Perspectives → Participation → Completion;
- repeated Decision presented as reweigh;
- Reflection;
- descriptive My KEFE journey details;
- Turkish/English, light/dark, Reduce Motion and accessibility coverage.

Explore, Radar, Atlas and other browse/compare surfaces remain separate from the focused decision journey. Sports CALL, Atlas, Radar, save/follow and account continuity remain partial relative to the complete product vision. Admin Studio, Signal/Impact, Circle, Rooms, Education, Live, Decide, Retro, AI experience families, research/B2B/commercial products and global indices are not complete product families.

## 6. Foundation status

The executable foundation program contains waves F0 through F7.

- **F0 — delivery-line and contract convergence:** `COMPLETE_VERIFIED`. The runtime line now carries AGENTS, the 128-capability register, foundation program, canonical registry, validators and exact continuation state. One canonical integration target is enforced.
- **F1 — provider-neutral content supply and reviewed Proposal runtime:** `IN_PROGRESS`. Typed human Feed Item/Source Brief review is canonical. Provider/evidence/scheduler primitives have strong candidate evidence, but the competing public-feed models are unresolved and no real production feed is authorized.
- **F2 — Editorial Projection into existing Content Authoring:** `COMPLETE_VERIFIED` in code (`ADR-0099`, contract `canonical-candidate-bundle-projection.v1.json`, `CAP-062` promoted to `IMPLEMENTED_VERIFIED`).
- **F3 — Admin authoring, review, moderation, media and operational reporting:** typed review APIs are canonical, but Admin Studio, Case Builder, Flow Composer, moderation, media operations and reporting remain incomplete.
- **F4 — identity, privacy, reachability and production readiness:** pending. Real OTP/auth operation, export/delete, production reachability, deployed observability/SLO and rollback evidence remain incomplete.
- **F5 — analytics, reporting, experimentation and FinOps:** pending as a reproducible platform.
- **F6 — methodology-qualified WE → SIGNAL → IMPACT:** Signal and Impact modules now have hexagonal repository ports and PostgreSQL adapters (maintenance change, local only). `get_computation_input()` reads from the live decision pipeline. This is an infrastructure prerequisite for F6, not F6 completion. Collective Result must not be promoted to Signal without methodology and analytics prerequisites.
- **F7 — commercial, entitlement, research and distribution foundation:** pending and gated by F4/F5 plus PMF/release decisions.

Do not describe the full infrastructure or the 128-capability vision as complete.

## 7. Active conflict: public-feed model

Two exact-head verified alternatives remain after PR #232:

- PR #273 / `00e1fd5ad8e4818d9a5738b6fdc9cd99bb3124fc`
- PR #267 / `e3c8a445ace3a9c4fbc734fa7ebf91e97b7c039e`

Both remain `ALTERNATIVE`. They overlap in public-feed identity, activation, application composition and migration `20260803_0026`. They must not be merged wholesale together.

Issue #291 owns the resolution. The accepted direction is:

> one authoritative versioned Public Feed Catalog and one explicit activation projection into the existing generic provider, scheduler, evidence, ingestion and Proposal runtime.

Compatible behavior may be selectively adopted. Duplicate aggregates, migration identifiers and activation state machines must be retired or renumbered.

## 8. Deterministic next runtime slice

**Canonical Public Feed Catalog and explicit activation projection**

- Issue: #291
- Base: PR #290 / `140960ac80881faec5841008eac9444ab67d9b7a`
- Mode: `CONFLICT_RESOLUTION`
- Capabilities: CAP-055, CAP-056, CAP-061, CAP-065, CAP-094, CAP-095, CAP-123, CAP-126

Required lifecycle direction:

1. versioned DRAFT catalog definition;
2. no-side-effect validation/preflight;
3. explicit maker-checker approval;
4. separate step-up protected activation;
5. capability-first, schedule-second projection into existing runtime;
6. runtime ACTIVE/PAUSED/RETIRED without in-place definition mutation;
7. new definition version for every source/configuration change;
8. zero concrete feed and zero startup activation in production until external approval.

Required exact-head evidence after implementation:

- dedicated canonical public-feed CI;
- complete provider security chain;
- API CI;
- Mobile CI;
- MVP Beta Gates;
- Global Readiness;
- memory and PostgreSQL migration/idempotency/concurrency evidence;
- API/OpenAPI version isolation;
- no-live-network vertical proof ending in a review-required Feed Item Proposal.

## 9. Sequence after public-feed convergence

1. Complete F2 human Editorial Projection against the existing Content Authoring DRAFT lifecycle.
2. Complete F3 Admin Studio verticals: review queues, Case Builder, Flow Composer, CQB/risk gates, moderation, media and operational reporting.
3. Complete F4 identity/privacy/production readiness and real deployment evidence.
4. Complete F5 analytics/reporting/experimentation/FinOps.
5. Implement F6 Signal and Impact only after methodology and analytics prerequisites (hexagonal ports are now in place as a prerequisite).
6. Continue accepted consumer, education, research, B2B and commercial capabilities without bypassing their foundation waves.

## 10. Binding invariants

Preserve unless accepted authority explicitly changes them:

- Commit First and applicable Blind First/pre-result isolation;
- immutable published CaseVersion;
- generic case-agnostic composable Flow runtime;
- Preview/production isolation and no Preview fixture production fallback;
- one existing Content Authoring aggregate and lifecycle;
- review, materialization, projection, authoring approval and publication remain separate;
- no automatic review, approval or publication;
- My KEFE remains observed/descriptive only;
- Collective Result is not automatically Signal, truth or authority;
- AI/provider output is Proposal, not truth or publication authority;
- accessibility, localization, Reduce Motion and low-end Android remain continuous gates;
- CI does not prove human usability, editorial acceptance, provider compliance, store compliance, deployed SLO or operator rollback.

## 11. External and human gates

Still explicitly unproven:

- human visual/usability approval;
- editorial CQB acceptance;
- real provider terms/compliance and delivery;
- production OTP/auth deliverability;
- durable production media/object storage;
- deployed SLO, load, observability and alerting;
- operator rollback drill;
- Apple/Google signing, privacy and store review;
- methodology-qualified Signal/Impact operation;
- PMF and commercial release gates.

## 12. Standard continuation protocol

1. Read `AGENTS.md`, this file, the capability portfolio, foundation program, ADR-0096, convergence contract and delivery registry.
2. Inspect live PR bases, heads, reviews, mergeability and exact CI.
3. Distinguish canonical runtime, candidate, alternative, superseded and external gate.
4. Reference CAP IDs for every material slice.
5. Use contract-first development for material boundaries.
6. Keep one canonical integration target.
7. Do not merge a child before its parents or merge unresolved alternatives wholesale.
8. Require exact-head evidence before PASS.
9. Keep human/provider/store/SLO/rollback evidence explicit.
10. Update this file and the registry after each meaningful integration checkpoint.

## 13. Pending items before next AI agent session

The following items from the 2026-09-10 maintenance session are **local only** (not committed, not on a PR, not CI-verified):

- Signal/Impact hexagonal port + Postgres adapter + migration 0042 (needs commit + CI)
- Signal/Impact API test refactor (needs commit + CI)
- `packages/kefe-design-tokens/`, `packages/kefe-locale/`, `packages/kefe-test-fixtures/` (content only; no build scripts yet)
- `infra/local/compose.yaml` Redis + MinIO additions (needs Docker Compose validation)
- Makefile expansion (needs smoke test on each target)
- Pre-existing test failure: `test_identity.py::test_invalid_bearer_is_rejected` — bearer token not rejected in dev mode. Investigate identity auth guard settings configuration.

Next priority: commit maintenance changes on a dedicated branch, run full CI, then proceed to Issue #291 Public Feed Catalog resolution.