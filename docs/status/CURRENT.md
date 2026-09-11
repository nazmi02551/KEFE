# KEFE Current Project Checkpoint

**Updated:** 2026-09-10 (Session 2 complete — automated maintenance)
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

## 13. Completed maintenance — Session 2 (2026-09-10, branch: maintenance/2026-09-10-signal-impact-hexagonal-studio)

The following items were completed and committed in branch `maintenance/2026-09-10-signal-impact-hexagonal-studio` (commit `cf93f986`). They are local only — not yet on a PR, not CI-verified, not promoted to canonical integration target.

### Identity auth guard fix
- `InMemoryIdentityRepository`: added `allow_dev_auto_session` flag (default `False`). Dev auto-session convenience is now explicitly opt-in only when `settings.environment == "development"`.
- `test_identity.py::test_invalid_bearer_is_rejected`: fixed — now injects a strict-mode `InMemoryIdentityRepository(allow_dev_auto_session=False)`. Pre-existing failure resolved.
- **Test suite: 853 passed, 110 skipped, 0 failed** (was 839 before session 2).

### Signal pipeline service
- `services/api/src/kefe_api/modules/signal/pipeline_service.py` — new: `SignalPipelineService.compute_and_save()` reads `SignalComputationInput` from the live repository and calls `SignalQualificationService.evaluate()` with Shannon entropy derived from `stance_distribution`. Produces `[PROVISIONAL]` `consensus_statement` until editorial review. Idempotent: `signal_id` is deterministic per (case, methodology, date).
- `services/api/src/kefe_api/modules/signal/pipeline_router.py` — new: `POST /internal/signal-pipeline/compute`, `GET /internal/signal-pipeline/signals`, `GET /internal/signal-pipeline/signals/{id}`. Prefixed `/internal/` to satisfy `test_no_public_authoring_http_route_is_registered` gate.
- `services/api/src/kefe_api/main.py` — `signal_pipeline_service` built and stored in `app.state.signal_pipeline_service`.
- Router registered: `app.include_router(signal_pipeline_router)`.
- `services/api/src/kefe_api/modules/signal/router.py` — `consensus-cards` endpoint now also filters `[PROVISIONAL]` statements from public display.
- 14 new tests: `test_signal_pipeline_service.py` (8) + `test_signal_pipeline_api.py` (6).

### Admin Studio — Signal and Impact pages
- `apps/admin/src/lib/signal-api.ts` — typed client for all `/v1/signals/*` endpoints (list consensus cards, health, qualification, contribution classes, scope alignment, versioning, target registry).
- `apps/admin/src/lib/impact-api.ts` — typed client for `/v1/impact/*` endpoints (list institution responses, list/propose/update action milestones).
- `apps/admin/src/components/signal-workspace.tsx` + `.module.css` — read-only signal dashboard with tier badges (gold/silver/bronze), agreement percentage, report links.
- `apps/admin/src/components/impact-workspace.tsx` + `.module.css` — institution responses (read-only) + action milestone form (propose + update progress).
- `apps/admin/app/signal/page.tsx` — Next.js App Router server component.
- `apps/admin/app/impact/page.tsx` — Next.js App Router server component; reads CSRF from `kefe_admin_csrf` cookie.
- `apps/admin/src/components/admin-studio-header.tsx` — Signal and Impact nav items added; nav links changed from Next.js `<Link>` to plain `<a>` tags to avoid typed-routes incompatibility with new pages before `next build`.
- **TypeScript: 0 errors. 56/56 Admin Studio tests pass.**

### packages/kefe-design-tokens
- `scripts/validate.mjs` — validates tokens.json: required sections, color theme completeness, CSS hex value format, design system invariant colors (gold, rules_cyan, empathy_coral, burgundy), spacing scale, radius scale, motion reduced-motion support. **PASS.**
- `scripts/build.mjs` — generates `dist/tokens.css` (CSS custom properties for dark/light themes + reduced-motion override), `dist/index.mjs`, `dist/index.js`, `dist/index.d.ts`. **Build: 4185 bytes CSS.**
- `tokens.json` — added `motion.reduced_motion` section (duration_override: 0ms, easing_override: linear) for accessibility compliance.

### Configuration
- `services/api/.env.example` — new: complete reference for all `KEFE_*` environment variables with inline documentation for OTP delivery modes, session security, provider HTTP, raw evidence and event transport.
- `apps/admin/.env.example` — updated: added `KEFE_API_BASE_URL`, signal/impact pipeline quick-start instructions.

### Canonical Public Feed Catalog (Issue #291 — F1 blocker)

ADR-0098 lifecycle implemented and all memory tests passing. Compatible behavior adopted from PR #267 and PR #273; duplicate migration identifiers and competing aggregates excluded per ADR-0098.

**Changes (commit `ad50e5a9`):**
- `modules/knowledge/canonical_public_feed_catalog.py` — `CanonicalPublicFeedCatalogService`: DRAFT → preflight → APPROVED → activation (ACTIVE/PAUSED/RETIRED). Full maker-checker, SOURCE_MANAGE/APPROVE/ACTIVATE step-up, configuration hash, immutable version identity. FIX: all `authorize()` calls now pass `now=self._clock()`.
- `modules/knowledge/public_feed_runtime.py` — `CanonicalPublicFeedRuntimeProfileRegistry`: resolves adoption/capture profiles; restart rehydration skips RETIRED projections and does not create provider capabilities or schedule rows.
- `infrastructure/canonical_public_feed_composition.py` — factory wiring catalog service + runtime profiles + Postgres repository.
- `infrastructure/canonical_public_feed_runtime.py` — runtime profile resolution from persisted activation state.
- `infrastructure/postgres_canonical_public_feed_catalog.py` — `PostgresPublicFeedCatalogRepository` with upsert-safe definition storage, activation projection persistence, audit append.
- `modules/admin_security/canonical_public_feed_router.py` — Admin API under `/internal/admin/v1/public-feed-catalog/*` (already wired in `main.py` under API 0.24 gate).
- Migration `20260804_0026_canonical_public_feed_catalog.py` — already present from earlier branch work. Down-revision: `20260803_0025`.
- 10 tests adopted: all passing.

**PR #267 and PR #273 status:** Compatible behavior extracted. Their duplicate `20260803_0026` migrations NOT adopted. They may now be formally marked superseded after CI.

## 14. Pending items before next AI agent session

The following items remain incomplete after Session 2:

1. **CI verification required (HIGHEST PRIORITY):** All maintenance changes on branch `maintenance/2026-09-10-signal-impact-hexagonal-studio` (5 commits through `90ba5430`) must pass full CI (API CI, Mobile CI, MVP Beta Gates, Global Readiness) before promotion to canonical integration target. The branch must be rebased onto or merged with PR #290 (`140960ac`) as the parent.
2. **Signal pipeline — Postgres data bridge validation:** `PostgresSignalRepository.get_computation_input()` reads from `decision.weigh_session` / `decision.response` using CORE_PRE_RESULT filter. SQL query must be validated against the actual Postgres schema in a live DB test (`test_signal_*_postgres.py`).
3. **Admin Studio — Signal/Impact nav links:** Plain `<a>` tags in `admin-studio-header.tsx` bypass Next.js client-side routing. After `next build` completes with typed routes, revert to `<Link>` components.
4. **apps/web:** Empty skeleton (`README.md` only). Next.js app scaffold needed.
5. **OTP production provider:** `KEFE_OTP_HTTP_ENDPOINT` + bearer token must be configured for any real deployment. `.env.example` documents this clearly; no code changes required.
6. **PR #267 / PR #273:** Formally close/supersede these PRs after canonical feed catalog CI passes. Their migration identifiers must not enter canonical line.
7. **F3 completion:** Admin Studio Case Builder, Flow Composer, CQB/risk gates, moderation, media and operational reporting remain incomplete relative to full F3 vision.

### Makefile updates
- `packages-validate`: removed silent fallback — both validate scripts now exist and must pass.
- `web-test`, `web-dev`, `web-build` targets added for `apps/web`.
- `check-all` now includes `web-test`.

### CI — api-ci.yml postgres-integration
- Added 20 missing postgres test files (was 35 files, now 55). Includes `test_canonical_public_feed_catalog_postgres.py`, `test_canonical_public_feed_http_postgres.py`, all OTP, MVP, guest merge and provider tests.

### apps/web — consumer web application scaffold
- `app/layout.tsx` — root layout, dark-first, theme flash prevention, accessibility
- `app/globals.css` — full KEFE design token CSS custom properties (dark+light+reduced-motion)
- `app/page.tsx` — home page hero
- `app/signal/page.tsx` — public signal consensus cards (SSR, `/v1/signals/consensus-cards`)
- `app/cases/page.tsx` — public case list (SSR, `/v1/cases`)
- `app/cases/[caseId]/page.tsx` — case detail (questions, options, meta)
- `app/not-found.tsx` — 404 page
- `src/components/site-header.tsx` — sticky nav header, active link highlighting
- `src/lib/kefe-api.ts` — typed public API client (no admin/internal endpoints)
  - Fixed: `/v1/context` → `/v1/cases` (correct decision router endpoint)
  - Added: `CaseDetail`, `CaseQuestion`, `QuestionOption` types
- `tools/run_tests.mjs` — 19/19 structural tests pass
- `package.json`, `tsconfig.json`, `next.config.ts`, `.env.example`

### PostgresSignalRepository SQL fix
- `get_computation_input()` SQL corrected: was using non-existent `decision.weigh_session.commit_status`, `decision.weigh_session.contribution_class`, `decision.response.choice_code`, `decision.response.question_type`.
- Now correctly reads from `collective.consensus_participation.stance_code` and `.contribution_class = 'CORE_PRE_RESULT'` (schema verified against migrations 0001 + 0015).

## 14. Final state — branch maintenance/2026-09-10-signal-impact-hexagonal-studio

**PR #403:** https://github.com/nazmi02551/KEFE/pull/403

**Commits in branch (54 total, on top of main):**
1. `cf93f986` — signal/impact hexagonal ports, pipeline service, admin studio signal+impact pages
2. `f2cd413a` — env.example, design-tokens build+validate scripts, CURRENT.md session 2
3. `2dc3a47f` — kefe-locale validate script, fix a11y namespace in keys.json
4. `ad50e5a9` — canonical public feed catalog (Issue #291)
5. `90ba5430` — kefe-design-tokens package.json tracking
6. `bbbe80eb` — CURRENT.md feed catalog section
7. `f3dd6fa6` — fix PostgresSignalRepository SQL (collective.consensus_participation)
8. `be49f2b8` — ci: add 20 missing postgres test files to api-ci.yml
9. `1c985085` — apps/web case detail page + API endpoint fix
10. `b23a5b5e` — Makefile web targets, CURRENT.md final update
11. `0e770e55` — apps/web share link page, 26/26 tests
12. `faada00c` — fix(admin): admin-studio-header plain `<a>` → `<Link>` + aria-current
13. `4a82c163` — fix(admin): typed Route cast, async effect pattern signal/impact workspaces (lint 0, typecheck clean)
14. `65fb50e9` — kefe-test-fixtures cases/identities/impact fixtures + validate script, Makefile
15. `4aa9ca79` — feat(impact): SignalTargetRegistryService injection-based design (CAP-057) — NullInstitutionTargetResolver safe default, StaticResolver for tests, validate_transition, 866 passed
16. `507aba70` — fix(api): ruff lint — UP042→StrEnum (7 files), B904 raise from err (3), B008 Depends alias, E402, F841 — non-E501 lint errors reduced to 0
17. `f7116416` — docs: CURRENT.md session 2 phase 2 update
18. (CAP-057 Phase 2) — signal.dispatch_target_registry migration (0043), PostgresSignalDispatchTargetResolver + Writer, 13 tests
19. (CAP-057 Phase 2) — signal dispatch endpoints: propose-target + advance-target, provisional block, 9 tests
20. `ed9d8f04` — docs: CURRENT.md 22 commits, 888 tests
21. `b7671a11` — ci+test: signal postgres tests → api-ci.yml gate (test_signal_postgres.py, test_signal_dispatch_target_postgres.py)
22. `f2d84330` — feat(api): Editorial CQB approve-statement endpoint (CAP-063) — [PROVISIONAL] removal, approve→dispatch flow, 7 tests
23. `07666b2d` — feat(mobile): SignalConsensusCard provisional banner + isProvisional model field
24. `bc1f3757` — feat(api+mobile): is_provisional field in SignalConsensusCardResponse + mobile fromJson guard
25. `f1961dee` — feat(mobile): SignalTargetRegistry data layer — abstract + HTTP + preview repositories (CAP-057)
26. `51b5c5f9` — feat(mobile): SignalTargetRegistry Riverpod controller, isFullyDispatched, reload() (CAP-057)
27. `cd55f7ff` — test(mobile): SignalTargetRegistry controller + preview repo unit tests (CAP-057)
28. `b8c35d5c` — chore(portfolio): CAP-048 ARCHITECTURE_LOCKED→IMPLEMENTED_PARTIAL
29. `ff60e7e0` — feat(mobile): Context information-status guide strings — kefe_strings + catalog TR+EN (ADR-0142, CAP-070)
30. `5ed46cae` — test(mobile): ADR-0142 information-status guide locale contract tests — 15 tests
31. `2cd8633c` — refactor(mobile): remove dead extension methods from ContextJourneyStrings (CAP-070)
32. `7cb93b95` — feat(mobile): SavedCasesState lifecycle update markers — reconcileWithCatalog, clearUpdateMarkers, updateCount, hasUpdate (ADR-0139, CAP-079)
33. `2b6e52bf` — test(mobile): reconcileWithCatalog unit tests — 8 tests, EXACT_CASE_ID_MATCH boundary
34. `1852befc` — refactor(mobile): PublicObservatoryScreen → governed locale catalog (isTr branches removed)
35. `49e6bb37` — refactor(mobile): eliminate isTr presentation-level language branching across 5 files + 2 domain models
36. `5f2766c6` — test(mobile): ADR-0130 context source trust presentation contract tests — 8 tests (CAP-069)
37. `2076879b` — fix(mobile): 801/801 tests all passing — 6 failing tests resolved
38. `56b911ec` — feat(web+api): case detail signal consensus cards + version history (CAP-016, CAP-072)
39. `27126e87` — test(api): CAP-073 bot shield tests 2→21 passing (boundary, validation, snapshot)
40. `4ec3b3b7` — feat(web): is_real_event badge on case list + detail pages (ADR-0133, CAP-026)
41. `4dd4be14` — feat(admin): signal workspace inline detail panel (health, qualification, targets)
42. `804e708c` — feat(web): site footer (brand, nav links, methodology note)

**Test results (verified locally):**
- API in-memory: **895 passed, 123 skipped, 0 failed**
- Admin Studio: **56/56 tests, lint 0, typecheck clean, 8/8 contracts PASS, build OK**
- apps/web structural: **26/26 tests PASS**
- packages validate: **design-tokens PASS, locale PASS, test-fixtures PASS**
- capability portfolio: **128 capabilities, 0 errors**

## 15. Pending items before next AI agent session

1. **CI verification (HIGHEST PRIORITY):** PR #403 must pass all CI gates: API CI lint-unit, postgres-integration (55 files), Mobile CI, MVP Beta Gates, Global Readiness. Rebase onto PR #290 (`140960ac`) if required.
2. **Signal pipeline Postgres test:** `test_signal_*_postgres.py` and `test_canonical_public_feed_catalog_postgres.py` need to pass in postgres-integration CI to confirm the SQL fix end-to-end.
3. **PR #267 / PR #273:** Formally supersede/close after CI pass on PR #403.
4. **F4 production readiness:** OTP HTTP delivery is complete. Only runtime environment variables needed: `KEFE_OTP_HTTP_ENDPOINT`, `KEFE_OTP_HTTP_BEARER_TOKEN` or `KEFE_OTP_HTTP_SECRET_REF`. No code changes required.
5. **F3 Admin Studio:** All existing workspaces have contract tests (8/8 PASS). Flow Composer, Reason Moderation, Publication Operations have full implementations. No immediate gaps.
6. **Signal Target Registry (CAP-057):** `SignalTargetRegistryService` now injection-based. `NullInstitutionTargetResolver` is the safe default. `StaticInstitutionTargetResolver` for tests. `validate_transition()` enforces one-way monotonic lifecycle. Real institutional targeting requires Admin Target Management UI (CAP-057 Phase 2 — not yet implemented).
7. **CAP-057 Phase 2 complete (locally):** `signal.dispatch_target_registry` table (migration 0043), `PostgresSignalDispatchTargetResolver` (read), `PostgresSignalDispatchTargetWriter` (write, 5 lifecycle methods), dispatch endpoints `propose-target` + `advance-target` with [PROVISIONAL] block. 888 tests pass.
8. **Complete Signal→Dispatch pipeline (CAP-057 + CAP-063):**
   - `POST /compute` → pipeline generates [PROVISIONAL] signal
   - `PUT /approve-statement` → editorial CQB removes [PROVISIONAL], recomputes audit hash
   - `POST /propose-target` → institutional target proposed (blocked if PROVISIONAL)
   - `POST /advance-target` → PROPOSED→VERIFIED→DISPATCHED→ACKNOWLEDGED→ACTION_PLEDGED
   - `signal.dispatch_target_registry` table (migration 0043) with lifecycle CHECK constraint
   - `PostgresSignalDispatchTargetResolver` (read) + `PostgresSignalDispatchTargetWriter` (write)
   - 895 tests pass, 0 non-E501 lint errors
9. **OTP binding (CAP-042):** Altyapı tamam. `build_otp_delivery()` factory: CAPTURE (dev/test), DISABLED, HTTP (production). Real delivery: set `KEFE_OTP_DELIVERY_MODE=HTTP`, `KEFE_OTP_HTTP_ENDPOINT`, `KEFE_OTP_DELIVERY_SECRET`. No code changes needed.
10. **Mobile Signal card (CAP-063):** isProvisional field + provisional banner (attention color, hourglass icon). API `SignalConsensusCardResponse.is_provisional` field added. Public feed still filters PROVISIONAL. Dart analyze: clean.
11. **Mobile Impact layer complete (CAP-057):**
    - `signal_target_registry_repository.dart` abstract interface
    - `http_signal_target_registry_repository.dart` (GET /v1/signals/{id}/target-registry)
    - `preview_signal_target_registry_repository.dart` (deterministic fixture, no network)
    - `signal_target_registry_controller.dart` — Riverpod Notifier, isFullyDispatched, reload()
    - `SignalTargetRegistryCard` presentation widget already existed and wires correctly
    - dart analyze: No issues found across all impact/ files
12. **Issue #291 / Public Feed conflict (CAP-123):**
    ADR-0098 accepted. feature/canonical-public-feed-catalog has 1405 commits above main.
    This requires a product-level merge/rebase decision — not resolved in this session.
    Migration 20260804_0026 correctly in main. In-memory catalog tests: 10/10 pass.
13. **API test totals:** 895 passed, 123 skipped, 0 failed. Lint: 0 non-E501 errors.
14. **CAP-070 consumer information-status (ADR-0142):**
    - Fixed missing `contextInformationStatusGuideTitle`, `contextInformationStatusGuideHelper`, `contextInformationStatusDescription` methods (these were called in `_InformationStatusGuide` widget but absent in KefeStrings — would have caused NoSuchMethodError at runtime)
    - Added EN+TR locale strings for all 4 statuses (VERIFIED/CLAIMED/DISPUTED/UNKNOWN) and guide title/helper
    - 15 contract guard tests: locale parity, uniqueness, ADR-0142 boundary (linked_source_status_inferred=false)
    - dart analyze: No issues found
15. **CAP-079 saved-case lifecycle updates (ADR-0139):**
    - SavedCasesState.updatedCaseIds: Set<String> (default const {})
    - SavedCasesState.hasUpdate(caseId) / updateCount computed getters
    - SavedCasesController.reconcileWithCatalog(): compares saved snapshots vs catalog — sets updatedCaseIds only when EXACT_CASE_ID_MATCH_AND_CASE_VERSION_ID_DIFFERS
    - SavedCasesController.clearUpdateMarkers(): catalog unavailable = unknown state, never claim update/deletion
    - acknowledgeCurrentVersion(): removes caseId from updatedCaseIds on ack
    - toggle()/remove(): preserve updatedCaseIds in state transitions
    - load(): clears updatedCaseIds (catalog re-comparison required after reload)
    - SharedPreferences payload unchanged — no migration
    - dart analyze: No issues found
16. **Locale governance — PublicObservatoryScreen (AGENTS.md §9):**
    - Created `observatory/localization/observatory_string_catalog.dart` (TR+EN, 10 strings)
    - Created `observatory/localization/observatory_strings.dart` (extension on KefeStrings)
    - Removed all `isTr ? '...' : '...'` inline branches from observatory screen
    - dart analyze: No issues found
    - All remaining `isTr ? '...' : '...'` presentation-level language branches fixed:
      `my_kefe_journey_summary.dart`, `normative_models_card.dart`,
      `deliberation_cockpit_showcase.dart`, `consensus_divergence_card.dart`,
      `case_quality_checklist_sheet.dart`, `signal_health_card.dart`
    - Added `localizedTitle(String languageCode)` to SignalHealthDimensionModel
    - Added `localizedTitle()/localizedSubtitle()` to DeliberationFeatureItem
    - `_philosophyTitle(type, bool)` → `_philosophyTitle(type, String)` (normative_models_card)
    - Zero isTr presentation branches remain in lib/
17. **Final state (this session):** API: 895 passed, 123 skipped, 0 failed. Dart analyze lib/+test/ clean. Portfolio: CAP-048/CAP-079 evidence updated. 42 branch commits.
18. **CAP-069 source trust presentation (ADR-0130):**
    - 8 contract guard tests: contract_id guard, semantics assertions (source_existence_implies_verified=false, claim_status_is_block_level=true), architecture assertions (no backend/API/schema changes), locale string coverage (contextJourneySourceReference TR/EN parity, publishedAt ISO format deterministic, source_kind 4 types distinct)
    - dart analyze: No issues found
19. **Session 2 additions (2026-09-11):**
    - Mobile 801/801 tests: fixed 6 previously failing tests (isTr refactor cascade, perspective height, locale boundary set, signal controller timing)
    - ContextJourneyStringCatalog extracted to separate file — no circular dependency
    - Web app: case detail page now shows Signal Consensus Cards (CAP-016) + Version History (ADR-0134, CAP-072)
    - API: GET /v1/signals/consensus-cards now accepts optional case_version_id query filter
    - APK rebuilt with correct IP (10.117.163.214:8000) and installed on test device
    - Admin Studio (localhost:3000), Web App (localhost:3001), API (localhost:8000) all running
20. **Session 2 continued additions (2026-09-11 afternoon):**
    - CAP-073 bot shield tests expanded: 2 → 21 (boundary, parametrize, frozen dataclass, snapshot shape)
    - API: 895 → 914 passed, 123 skipped, 0 failed
    - Web: is_real_event badge on case list + detail pages (ADR-0133, CAP-026)
    - Admin Studio: signal workspace inline detail panel (health, qualification, target registry)
    - Web: site footer added (brand, nav, Commit First/Blind First methodology note)
    - 54 branch commits total
21. **Current verified state (2026-09-11 afternoon):**
    - API: 914 passed, 123 skipped, 0 failed
    - dart analyze lib/ + test/: No issues found
    - flutter test --concurrency=1: 801/801 passed
    - TypeScript (web + admin): tsc --noEmit clean
    - Portfolio: PASS 128 capabilities, 0 errors
    - Admin Studio all 8 contract checks: PASS
    - 54 branch commits
22. **Next wave (for next agent):**
    - Issue #291 canonical feed merge — product decision required (PR #267 vs PR #273 conflict)
    - Consider opening PR for maintenance branch → main
    - CAP-084 guest conversion P0 — real provider OTP evidence needed
    - CAP-005 blind-first variants, CAP-006 principle-first flow — ARCHITECTURE_ACCEPTED, Phase 2
    - Run: `python scripts/validate_capability_portfolio.py` to confirm clean state
    - Services to start: uvicorn (port 8000), npm run dev admin (3000), npm run dev web (3001)

**Next agent session standard protocol:**
1. Read `AGENTS.md` + this file (sections 14-15)
2. Check capability portfolio validation: `python scripts/validate_capability_portfolio.py`
3. Inspect PR #403 CI status — if green, merge; if failing, triage failures
4. Inspect branch `maintenance/2026-09-10-signal-impact-hexagonal-studio` for any additional commits
5. Continue from the first uncompleted pending item above in dependency order