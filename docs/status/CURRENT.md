# KEFE Current Project Checkpoint

**Updated:** 2026-07-29  
**Repository:** `nazmi02551/KEFE`  
**Default branch:** `main`  
**Latest verified implementation commit:** `c45cf369eeda79daf884beddb25e976c88ddabc4`

This is the **single canonical durable engineering handoff**. Chat history is not a source of truth. On every continuation, read this file from `main`, inspect open PRs/recent CI, and fetch the Drive CURRENT publication artifact only when editable DOCX/PDF source detail is needed.

## 1. Official documentation baseline

**KEFE Documentation Ecosystem v3.4 — validation PASS**

Principal versions:
- Master Product Document v1.3.0 — Approved Canonical
- Documentation Governance v1.5.0 — Approved
- Product Bible v1.5.0 — Working Baseline
- Engineering Blueprint v0.7.0 — Implementation Baseline
- MVP Delivery Plan v1.3.0
- Admin Studio Specification v1.3.0
- Security & Privacy Model v1.3.0

Specialist baseline versions are v1.2.0 for AI Architecture, Analytics Event Dictionary, Case & Scenario Library, Civic Integrity Model, Commercial & Growth Design, Content & Question Design Bible, Decision Graph Specification, Editorial Transformation Guide, Research Methodology, and Trust & Integrity Methodology.

Current publication artifact:  
`KEFE_Documentation_Ecosystem_2026-07-28_v3.4_CURRENT.zip`

- 18 active logical documents / 36 active DOCX+PDF files
- 289 active PDF pages
- package audit PASS
- accessibility high-severity findings: 0
- SHA-256: `b14ca825d9b62ff00b7fc61a0f2530aa3d2dd0c7b7f0d222c477b8af9bde9b0b`
- Drive CURRENT file ID: `1MXvCTNPfv-pWYIHCo5KqpmTOf-3RyFhZ`
- Drive raw readback hash: MATCHED

Recovery lineage:
- v3.3 original byte-level artifact was lost and is not falsely presented as reconstructed byte-identical.
- v3.3 recovery R1 SHA-256 `760a74d91f60339c0277cf4f0b568f5865d8677ed04c41a0f276738ef079e0c7`, Drive ID `1I0n-kzYUk_p0rHTxR1IloDjUMITRVN8b`, readback MATCHED.
- exact verified v3.2 SHA-256 `3af400c28a9849f0714bf1e4656a5cb4b0b625164f05183caff75984ac5bc223`, Drive ID `1joFVxCQW29e-XMdu3cVViLLESU__GM-m`.

Milestone publication is complete only after render/QA, PDF preflight, manifest/audit/checksum, archive, persistent Drive upload and raw readback SHA verification.

## 2. Binding product architecture

Consumer experience path:  
`Launch → Explore → Case → Context → Weigh → Commit → Reveal → Perspective → My KEFE Progress → Share`

Platform value lifecycle:  
`ME → WE → SIGNAL → IMPACT`

Binding architecture:
- KEFE is a case-agnostic modular decision/public-reasoning engine.
- canonical composition is `Primitive → Capability → FlowTemplateVersion → CaseVersion`.
- Composition over Case Types; new cases should be content/configuration/composition, not new runtime feature families.
- Base Format is an editorial archetype, not a runtime Case class.
- Schema before Screen.
- Commit First remains global; Blind/Principle First are reusable optional methodology capabilities.
- Context, Reveal, Exposure and Intervention are distinct.
- generic lineage is `DecisionRevision → Exposure/Intervention → DecisionRevision → DecisionDelta`; dimension-specific delta engines are forbidden.
- Claim is first-class and Claim ≠ claimant.
- initial Claim Types: FACTUAL, CAUSAL, BEHAVIORAL, MOTIVE, NORMATIVE, LEGAL, PROCESS, PREDICTION.
- initial Claim States: VERIFIED, SUPPORTED, CLAIMED, DISPUTED, UNVERIFIED, UNRESOLVED, FALSE; semantics are methodology-versioned.
- one source may yield multiple Claims, decision problems and Candidate Cases.
- AI may extract/classify/normalize/suggest/compose/detect, but is not KEFE's normative/political/moral voice or final truth authority.
- published CaseVersion pins its effective Content Configuration provenance and self-contained resolved Flow.
- consumer Flow execution uses only the session-pinned CaseVersion + its pinned `resolved_flow`; live Content Configuration must never reinterpret historical Cases.

Signal integrity:
- Collective Result ≠ Signal.
- Signal is not a percentage threshold; methodology includes agreement, sample strength, data quality, stability, counterargument exposure/resilience, stakeholder distribution/gap, scope alignment and freshness.
- CORE_PRE_RESULT, EXPOSED and ADVOCACY_SUPPORT never silently mix.
- result exposure excludes that decision from the core pre-result sample for that lineage.
- Challenge Card and Signal/Consensus Card are semantically distinct.
- Scope Alignment is mandatory and Stakeholder Gap may not be hidden.
- Signal/Consensus is not formal authority and not KEFE's own opinion.
- Impact lifecycle is `Signal → Target → Institution Response → Action → Impact Evidence → Impact Verification`.

## 3. Completed executable foundation

Retained foundation:
- FastAPI modular monolith + PostgreSQL.
- idempotent linearizable Commit, transactional outbox and durable worker.
- hashed/revocable guest sessions and admission guard ports.
- Explore/Case reads, typed questions, pre-Commit Context/Sources, private Reason Capture.
- Commit-gated Reveal and bounded Perspective.
- actor-scoped My KEFE Progress + optional post-Reveal Account Offer.
- provider-neutral Content Authoring lifecycle, immutable published CaseVersion, PostgreSQL editorial persistence and atomic consumer publication.
- separate Admin security domain, capability-first authorization, MFA/session assurance, same-session CSRF, recent step-up and server-derived audit identity.
- secured internal Admin authoring/configuration HTTP under `/internal/admin/v1`; no Admin login/SSO endpoint yet.
- Flutter consumer foundation contains Explore, Context, typed Question/Reason, Commit, Reveal, Perspective and Progress presentation paths.

### PR #47 / ADR-0020 — composable Content Configuration — COMPLETE

Implementation commit: `7223dfeef55936f2fd70922bec74d3ce56232820`

Implemented:
- PrimitiveDefinition, CapabilityDefinition, FlowStepDefinition, versioned FlowTemplateDefinition.
- ContentConfigurationSnapshot owns Primitive/Capability/FlowTemplate registries while retaining Domain/Topic/Base Format/Modifier.
- generic bootstrap flows `STANDARD_COMMIT_REVEAL` and `PRINCIPLE_CONTEXT_RETEST`.
- validation for identity uniqueness, references, Capability/Primitive compatibility, entry/transition integrity and terminal Step.

### PR #49 — durable composable Content Configuration persistence — COMPLETE

Implementation commit: `ee74719c99f29230447ed7bdd4a2ea01d15eae70`

Implemented:
- migration `20260728_0011` with isolated `content_config` schema.
- immutable DRAFT/PUBLISHED/SUPERSEDED lifecycle, one-published-version DB guard and JSONB aggregate storage.
- append-only audit, clone provenance, explicit rollback draft and atomic publish/supersede.
- full PostgreSQL round-trip for Domains/Topics/Base Formats/Modifiers plus Primitive/Capability/FlowTemplate/Step semantics.
- API CI `30384684807` PASS.

PR #45 is closed without merge as superseded by PR #49; the pre-ADR-0019 narrow aggregate must not be reintroduced.

### PR #51 / ADR-0021 — secured Admin composable configuration HTTP — COMPLETE

Implementation commit: `a88ee763222ec70e0b50e2c78d1c917bec0d5c68`

Implemented:
- API/OpenAPI v0.13.0.
- secured `/internal/admin/v1/content-configuration` lifecycle surface.
- current/version/audit reads; clone current to DRAFT; DRAFT save; publish; historical rollback-to-new-DRAFT.
- `TAXONOMY_MANAGE` for configuration management and `AUDIT_READ` for audit.
- existing opaque Admin session + same-session CSRF ordering reused; no second auth surface.
- strict payloads forbid client lifecycle/version/admin/audit identity injection.
- current approved policy still does not require recent step-up for `TAXONOMY_MANAGE`; changing that requires an explicit security-policy decision.

Verification: final API CI `30386784064` PASS including lint, contract sync, Admin HTTP fitness, OpenAPI drift, unit and PostgreSQL integration.

### PR #52 / ADR-0022 — CaseVersion Flow + configuration pinning — COMPLETE

Implementation commit: `b9b26dddaeb9298166b28e673cb48c3c8a92e701`

Implemented:
- DRAFT CaseVersion selects `flow_template_code` + `flow_template_version_no`.
- publication resolves selection against current PUBLISHED ContentConfiguration.
- publication validates effective Domain/Base Format/Modifier/Flow/Primitive/Capability compatibility.
- published CaseVersion pins server-derived `content_configuration_id`, configuration version and self-contained immutable `resolved_flow`.
- revision preserves editorial Flow selection but clears prior publication pin and resolves again on publication.
- migration `20260728_0012` adds consumer provenance fields without breaking historical rows.
- editorial JSONB and consumer materialization round-trip the same Flow/config provenance.
- consumer CaseVersion read model carries the pinned resolved Flow.

Verification: final API CI `30391510709` PASS including migration/seed and PostgreSQL provenance round-trip.

### PR #54 / ADR-0023 — generic consumer Flow runtime — COMPLETE

Implementation commit: `164a97dc43dc1c6d4b67e749326ab319d2e2e19b`

Implemented:
- API/OpenAPI v0.14.0.
- authenticated actor-scoped `GET /v1/weigh-sessions/{session_id}/flow`.
- server-authoritative Flow Step graph/state from the session-pinned CaseVersion's immutable `resolved_flow`.
- no live Content Configuration lookup, client-completed-Step claims or historical reinterpretation.
- no result/Perspective/private-reason payload leakage through Flow runtime.
- runtime Step states: READY, COMPLETED, BLOCKED, UNSUPPORTED; execution support FULL/PARTIAL.
- `CONTEXT` is informational/non-blocking in runtime v1.
- first `DECISION` maps to current single-Commit WeighSession.
- `COLLECTIVE_RESULT` remains blocked pre-Commit and becomes READY post-Commit; actual result data remains behind Reveal.
- later `DECISION` uses the same generic graph but reports `FLOW_DECISION_REVISION_REQUIRED` until DecisionRevision exists.
- legacy CaseVersions without pinned Flow return `FLOW_RUNTIME_UNAVAILABLE`; no default/live Flow inference.
- `STANDARD_COMMIT_REVEAL` is FULL through the generic runtime.
- `PRINCIPLE_CONTEXT_RETEST` is parsed by the same runtime and reports PARTIAL at the exact revision capability boundary.

Verification:
- final API CI run `30392910874` PASS.
- lint PASS.
- contract sync PASS.
- Case Flow pinning gate PASS.
- generic Flow runtime gate PASS.
- Admin HTTP gate PASS.
- OpenAPI drift PASS.
- unit tests PASS.
- PostgreSQL integration PASS, including publish → guest session → Flow read → response → Commit → Flow read.

### PR #56 / ADR-0024 — Flutter Flow-driven rendering — COMPLETE

Implementation commit: `94d31fcc6ba9e99ebdeb386f3adf9bbbbfae18db`

Implemented:
- Flutter fetches the server-authoritative Flow runtime for each active WeighSession.
- FlowRuntimeSnapshot is persisted with the local DecisionDraft for recovery/offline continuity.
- rendering iterates server Step order instead of a hard-coded Context → Questions → Commit → Reveal composition.
- `CONTEXT`, `DECISION` and `COLLECTIVE_RESULT` reuse the existing production UI components.
- unsupported runtime capability is surfaced explicitly and neutrally; the client never silently emulates or skips it.
- no Case Type/Base Format branching or default Flow inference was introduced.
- PARTIAL `PRINCIPLE_CONTEXT_RETEST` reaches the exact DecisionRevision capability boundary without client-side hard-coding.
- mobile architecture fitness contract: `mobile-flow-runtime-ui.v1.yaml`.

### PR #57 — authoring-published live demo + installable Flow preview — COMPLETE

Implementation commit: `c45cf369eeda79daf884beddb25e976c88ddabc4`

Implemented:
- the stable demo Case is no longer directly inserted into consumer Case/Question tables.
- demo CaseVersion is created through the production Content Authoring lifecycle: DRAFT → IN_REVIEW → APPROVED → PUBLISHED.
- publication pins effective Content Configuration provenance and immutable `STANDARD_COMMIT_REVEAL` resolved Flow before demo result/Perspective fixtures are attached.
- legacy 1–5 demo Confidence schema was corrected to the canonical authoring contract 1–10 rather than weakening validation.
- PostgreSQL seed explicitly uses PostgreSQL authoring/configuration adapters; runtime memory defaults cannot divert the seed from durable publication.
- isolated `main_preview.dart` + PreviewDecisionRepository exercise the same Flow runtime/Decision/Commit/Reveal/Perspective UI contracts without becoming a production runtime fallback.
- Mobile CI creates a temporary Android host project when packaging, builds a debug APK, and uploads `kefe-preview-android`.
- production/network failures never switch into preview mode.

Verification:
- final API CI `30401109769` PASS.
- final Mobile CI `30401109851` PASS including analyze, widget tests and Android APK build.
- preview artifact `kefe-preview-android`, Actions artifact ID `8704923555`, generated 2026-07-28.

## 4. Current implementation gap

Still implementation-pending:
- Admin authoring selection/composer UX for non-default FlowTemplateVersion; current HTTP authoring remains transitional default-compatible.
- DecisionRevision/Exposure/Intervention/DecisionDelta.
- first-class Claim/Argument graph and normalized ingestion.
- WE/Signal bounded context and MethodologyVersion sample/scope/stakeholder semantics.
- Impact bounded context.
- production deployment/observability and full account continuity/share maturity.

The first tangible Flow-driven consumer milestone is complete: an authoring-published Case can execute through the generic server Flow and the same Flutter rendering path, with an installable deterministic Preview APK available for direct inspection.

## 5. Recommended next sequence

1. **DecisionRevision / Exposure / Intervention / DecisionDelta**
   - lock ADR + machine-readable contract before implementation.
   - make a DecisionRevision an immutable decision state at a defined exposure state.
   - record actual Exposure separately from authored Reveal intent.
   - represent methodology-significant exposures/events as Interventions.
   - compute generic DecisionDelta between revisions; no ActorDelta/LegalDelta/etc. engines.
   - unlock `PRINCIPLE_CONTEXT_RETEST` and future evidence/actor/source/result retest flows through the existing generic Flow runtime.
2. **First-class Claim + Argument Graph + ingestion normalization**.
3. **WE/Signal foundation** with contribution classes, Scope Alignment, Stakeholders and MethodologyVersion.
4. **Impact foundation** with Target, Official Response, Action, Evidence and Verification.
5. **Admin Flow Composer UX** over already versioned Primitive/Capability/FlowTemplate semantics.
6. Continue observability/deployment, account continuity and share in architecture-compatible slices.

No implementation may leapfrog an unresolved product/domain contract.

## 6. Guardrails

- Never leak result/Perspective into core pre-result decision paths.
- Never leak another user's private/PENDING reason.
- No raw comment feed or popularity-only ranking.
- Keep human reasons and AI summaries distinct.
- Preserve provenance, moderation and methodology metadata.
- No personality/ideology/psychometric inference from activity.
- Published CaseVersion never mutates in place.
- Editorial mutable state never enters consumer tables before publication.
- Provider-specific CMS/SQL/IdP/AI dependencies stay behind adapters.
- Consumer credentials never authenticate Admin commands.
- Client-provided Admin/audit identity is forbidden.
- Same-session CSRF and Admin assurance ordering remain binding.
- Runtime live config never silently reinterprets historical published objects.
- Flow execution must use the CaseVersion-pinned resolved Flow.
- Flow runtime may expose result readiness but never pre-Commit result payload.
- Preview/demo infrastructure is build-time/dev-only and must never become a production fallback path.
- Signal sample classes never silently mix.
- Consensus/Signal is not formal authority and not KEFE opinion.

## 7. Continuation protocol

1. Read this file from `main`.
2. Inspect open PRs, recent merges and CI.
3. Fetch Drive CURRENT only when publication-source detail is required; verify its SHA against this checkpoint.
4. Resolve work against MPD v1.3.0 + ADR-0019 through ADR-0024 + registered contracts.
5. One coherent branch per vertical slice.
6. ADR + machine-readable contract before new behavior.
7. Preserve ports/adapters, versioning, provenance and historical reproducibility.
8. Tests/contracts ship with implementation.
9. Merge only with green relevant CI and no newer authority conflict.
10. Update CURRENT after every meaningful merge.
11. DOCX/PDF regenerate only at declared milestones; persist to Drive and read back/hash before declaring PASS.

## 8. New-chat recovery prompt

> Continue KEFE from `nazmi02551/KEFE`. Read `docs/status/CURRENT.md` on `main` first and inspect open PRs/recent CI. Official docs baseline remains Ecosystem v3.4. The binding architecture is case-agnostic: `Primitive → Capability → FlowTemplateVersion → CaseVersion`, with `ME → WE → SIGNAL → IMPACT`. PR #54 (`164a97dc...`) provides the server-authoritative generic Flow runtime from the CaseVersion-pinned resolved Flow. PR #56 (`94d31fcc...`) makes Flutter render from that Flow without Case-specific branching. PR #57 (`c45cf369...`) proves a production-authoring-published demo Case through the same architecture and produces an installable deterministic Preview APK. The next locked development target is DecisionRevision → Exposure/Intervention → DecisionDelta so revision-dependent Flow paths such as `PRINCIPLE_CONTEXT_RETEST` become FULL. Do not code an unlocked product decision.

## M2 DecisionRevision Runtime Checkpoint — 2026-07-29

- Main baseline: `9d5b4b4d3bccb1e2f21479c921f07a6c51357c05`
- PR #60 delivered the first executable DecisionRevision lineage slice under ADR-0025.
- Initial Commit materializes immutable Revision #1; later Decision Steps use separate revision drafts and immutable revisions.
- Context between committed Decisions is recorded as actual Exposure and promoted server-side to a methodology-significant Intervention.
- Generic DecisionDelta links predecessor revision, intervention lineage and successor revision without claiming causality.
- Flow runtime v2 evaluates between-decision Context and later Decision readiness from server lineage state; Reflection remains explicitly pending.
- Consumer Flutter uses the same Flow-driven screen and offline/idempotent draft state machine for initial and later Decisions; no Case/BaseFormat branching was introduced.
- Contract baseline: API/OpenAPI 0.15.0, generic Flow runtime 1.1.0, DecisionRevision lineage 1.1.0, Mobile Flow runtime UI 1.1.0, manifest 1.29.0.
- Durable PostgreSQL migration: `20260729_0013_decision_revision_lineage.py`.
- Validation baseline includes API lint/contracts/unit, PostgreSQL migration/seed/integration, Flutter analyze/widget tests, `PRINCIPLE_CONTEXT_RETEST` acceptance and Preview APK build.
- Next architecture slice: generic `REFLECTION` runtime over committed DecisionRevision/DecisionDelta lineage, preserving the same Case-agnostic composition model. Do not introduce Reflection-specific Case types or client-side delta inference.

