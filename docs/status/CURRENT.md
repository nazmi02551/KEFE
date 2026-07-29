# KEFE Current Project Checkpoint

**Updated:** 2026-07-29  
**Repository:** `nazmi02551/KEFE`  
**Default branch:** `main`  
**Latest verified implementation commit:** `5e78261212454338ec957bcf854bfd1c50a54e11`  
**Latest accepted architecture-lock merge:** `1088e9a6b53e38420fefd77263d291761fdf8041`

This is the **single canonical durable engineering handoff**. Chat history is not a source of truth. On every continuation, read this file from `main`, inspect open PRs/recent CI, and fetch the Drive CURRENT publication artifact only when editable DOCX/PDF source detail is needed.

Historical checkpoint lineage is preserved in Git. The pre-M4 consolidated checkpoint is commit `9c626322c4f4b5f29f03023361ea1a1ae6342701`; an earlier detailed checkpoint is `452609ccbfa777c092b0522116016362d9f4c8a4`. No prior implementation/history is discarded by this consolidation.

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

Current publication artifact: `KEFE_Documentation_Ecosystem_2026-07-28_v3.4_CURRENT.zip`

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

## 2. Binding architecture

Consumer experience path: `Launch → Explore → Case → Context → Weigh → Commit → Reveal → Perspective → My KEFE Progress → Share`

Platform value lifecycle: `ME → WE → SIGNAL → IMPACT`

Core rules:
- KEFE is a case-agnostic modular decision/public-reasoning engine.
- canonical composition is `Primitive → Capability → FlowTemplateVersion → CaseVersion`.
- Composition over Case Types; Base Format is an editorial archetype, not a runtime class.
- Schema before Screen.
- Commit First is global; blind/principle-first variants are reusable optional capabilities.
- Context, Reveal, Exposure and Intervention are distinct.
- generic decision lineage is `DecisionRevision → Exposure/Intervention → DecisionRevision → DecisionDelta`; dimension-specific Delta engines are forbidden.
- Reflection is bounded, server-derived and non-causal; it observes committed lineage and does not create a DecisionRevision.
- Claim is first-class and Claim ≠ claimant.
- canonical Claim Types: FACTUAL, CAUSAL, BEHAVIORAL, MOTIVE, NORMATIVE, LEGAL, PROCESS, PREDICTION.
- canonical Claim States: VERIFIED, SUPPORTED, CLAIMED, DISPUTED, UNVERIFIED, UNRESOLVED, FALSE; semantics are versioned.
- Claim evaluation history is append-only/versioned; evidence support, claimant reputation or popularity never becomes a truth oracle.
- one SourceArtifact/NormalizedArtifact may yield zero or many Claims, arguments, decision problems and Candidate Cases.
- provider-specific source logic ends at SourceAdapter; the knowledge domain remains provider-neutral.
- AI may extract/classify/normalize/suggest/compose/detect, but is not truth authority, normative voice, editorial acceptance or autonomous publisher.
- published CaseVersion pins effective Content Configuration provenance and immutable resolved Flow.
- consumer execution uses only the session-pinned CaseVersion and pinned `resolved_flow`; live configuration never reinterprets history.

Signal integrity remains binding:
- Collective Result ≠ Signal.
- CORE_PRE_RESULT, EXPOSED and ADVOCACY_SUPPORT never silently mix.
- Signal is methodology-qualified, not a percentage threshold.
- Scope Alignment is mandatory; Stakeholder Gap may not be hidden.
- Signal/Consensus is not formal authority and not KEFE opinion.
- Impact lifecycle is `Signal → Target → Institution Response → Action → Impact Evidence → Impact Verification`.

## 3. Completed executable foundation

Retained platform foundation:
- FastAPI modular monolith + PostgreSQL.
- idempotent linearizable Commit, transactional outbox and durable worker.
- hashed/revocable guest sessions and admission guards.
- Explore/Case reads, typed questions, pre-Commit Context/Sources, private Reason Capture.
- Commit-gated Reveal and bounded Perspective.
- actor-scoped My KEFE Progress + optional post-Reveal Account Offer.
- provider-neutral Content Authoring lifecycle, immutable published CaseVersion and atomic consumer publication.
- separate Admin security domain with capability-first authorization, MFA/session assurance, CSRF, step-up and server-derived audit identity.
- Flutter Flow-driven consumer foundation including DecisionRevision and Reflection.
- provider-neutral first-class Claim/Argument knowledge persistence foundation.

Completed architecture/implementation milestones:

### PR #47 / ADR-0020 — composable Content Configuration
Implementation commit `7223dfeef55936f2fd70922bec74d3ce56232820`.

Primitive/Capability/versioned FlowTemplate registry, generic bootstrap flows and compatibility validation established.

### PR #49 — durable composable Content Configuration persistence
Implementation commit `ee74719c99f29230447ed7bdd4a2ea01d15eae70`.

Migration `20260728_0011`; isolated `content_config` schema; immutable lifecycle, audit, clone/rollback and PostgreSQL round-trip. PR #45 remains closed as superseded.

### PR #51 / ADR-0021 — secured Admin configuration HTTP
Implementation commit `a88ee763222ec70e0b50e2c78d1c917bec0d5c68`.

API/OpenAPI 0.13.0; secured `/internal/admin/v1/content-configuration`; existing Admin session/CSRF boundary reused. API CI `30386784064` PASS.

### PR #52 / ADR-0022 — CaseVersion Flow/configuration pinning
Implementation commit `b9b26dddaeb9298166b28e673cb48c3c8a92e701`.

Published CaseVersion pins Content Configuration provenance + immutable resolved Flow. Migration `20260728_0012`. API CI `30391510709` PASS.

### PR #54 / ADR-0023 — generic consumer Flow runtime
Implementation commit `164a97dc43dc1c6d4b67e749326ab319d2e2e19b`.

API/OpenAPI 0.14.0; actor-scoped server-authoritative Flow from pinned CaseVersion. No live-config inference or result/private-reason leakage. API CI `30392910874` PASS.

### PR #56 / ADR-0024 — Flutter Flow-driven rendering
Implementation commit `94d31fcc6ba9e99ebdeb386f3adf9bbbbfae18db`.

Flutter iterates server Step order, persists Flow snapshot for recovery, reuses generic UI primitives and fails safely on unsupported capability without Case-specific branching.

### PR #57 — authoring-published live demo + Preview APK
Implementation commit `c45cf369eeda79daf884beddb25e976c88ddabc4`.

Demo Case is published through the real authoring lifecycle and executes through the same generic Flow. API CI `30401109769` PASS; Mobile CI `30401109851` PASS; Preview APK artifact ID `8704923555`.

### PR #60 / ADR-0025 — DecisionRevision / Exposure / Intervention / DecisionDelta
Implementation commit `9d5b4b4d3bccb1e2f21479c921f07a6c51357c05`; checkpoint follow-up `cd766fec7b04e5478344da828b575410f3109222`.

- initial Commit materializes immutable Revision #1;
- later DECISION Steps create immutable revisions via separate draft/commit path;
- actual Context encounter becomes Exposure and may become server-classified Intervention;
- generic non-causal DecisionDelta links revisions and intervention lineage;
- Flutter reuses the same Flow-driven/offline-idempotent state machine;
- migration `20260729_0013_decision_revision_lineage.py`;
- contract baseline: API/OpenAPI 0.15.0, generic Flow runtime 1.1.0, DecisionRevision lineage 1.1.0, Mobile Flow runtime UI 1.1.0, manifest 1.29.0.

### PR #64 / ADR-0026 — generic Reflection runtime and completion
Merge commit `2e2a3df8a3f95104db4c23556107677cf186372a`; exact green PR head `157dca230e60de892b8adc24e537c9d468538c1f`.

- durable cursor-pinned `ReflectionCompletion`; migration `20260729_0014_reflection_completion.py`;
- actor-scoped bounded read model with no raw response/private-reason leakage;
- idempotent completion pinned to latest DecisionRevision/optional DecisionDelta;
- later revision reopens Reflection for the new lineage cursor;
- reusable Flutter `REFLECTION` primitive with non-causal server-derived summary;
- persisted retry identity and same-session recovery across restarts;
- strict read-only CI restored; temporary recovery workflows removed.

Exact-head verification:
- API CI `30438276272` PASS including PostgreSQL integration.
- Mobile CI `30438276284` PASS including analyze, widget tests and Preview APK build.

Recovery lineage: original draft PR #63 is closed unmerged and preserved as source-history; it must not be merged independently.

### PR #65 / ADR-0027 — Claim/Argument normalized-ingestion architecture lock
Architecture-lock merge `1088e9a6b53e38420fefd77263d291761fdf8041`; exact green PR head `11ec0e0e06018e9be0408f48a6851eecc1532708`.

Accepted before implementation:
- Claim independent of claimant/source/CaseVersion;
- versioned append-only ClaimAssessment history;
- ClaimAssertion separate from Claim State;
- EvidenceLink separate from ClaimAssessment;
- versioned ClaimRelation graph edge;
- first-class Argument + typed relation to Claim/Question/Argument;
- provider-specific edge ends at SourceAdapter;
- normalized path `SourceAdapter → SourceArtifact → NormalizedArtifact → Claims/Evidence/Replies/Arguments → Decision Problems → Candidate Cases`;
- AI output is auditable proposal, not final truth/editorial acceptance/autonomous publication;
- existing Context four-state projection remains backward-compatible;
- PostgreSQL canonical; graph DB deferred.

Contract lock baseline: `claim-argument-ingestion.v1.yaml` 1.0.0, manifest 1.32.0. API CI `30439670861` PASS.

### PR #66 / ADR-0027 — first-class Claim/Argument domain + persistence — COMPLETE
Merge commit `5e78261212454338ec957bcf854bfd1c50a54e11`; exact green PR head `f9254619ee36e3af161540f644730d36486e17b2`.

Implemented:
- immutable `Claim`, append-only/versioned `ClaimAssessment`, separate `ClaimAssertion`;
- `EvidenceLink` with explicit source/normalized-artifact target and required provenance; SUPPORTS does not mutate Claim State;
- registry-governed `ClaimRelation` with required provenance and self-edge rejection;
- first-class `Argument` and `ArgumentRelation` targeting exactly one Claim/Question/Argument;
- immutable `SourceArtifact` with idempotency fingerprint `(adapter_code, external_locator, content_hash)`;
- provider-neutral `NormalizedArtifact`, including parent/reply lineage;
- provider-specific `SourceAdapter` port + provider-neutral `KnowledgeRepository` port;
- in-memory repository with referential invariants;
- PostgreSQL `knowledge` schema + `PostgresKnowledgeRepository`;
- migration `20260729_0015_claim_argument_knowledge.py`;
- DB constraints for canonical Claim types/states, review states, exactly-one polymorphic targets, provenance and self-edge rejection;
- persistence builder wiring without adding HTTP or consumer UI;
- conceptual ERD advanced to `core-erd.v3.mmd`, while `core-erd.v2.mmd` remains registered for DecisionRevision lineage fitness compatibility;
- `claim-argument-ingestion.v1.yaml` advanced to implementation v1.1.0;
- manifest v1.33.0;
- dedicated Claim/Argument architecture fitness gate added to strict API CI;
- existing Context status enum remains exactly VERIFIED/CLAIMED/DISPUTED/UNKNOWN.

Exact-head verification:
- API CI `30441698265` PASS;
- lint PASS;
- contract sync PASS;
- Case Flow, generic Flow, DecisionRevision, Reflection, Claim/Argument and Admin contract gates PASS;
- unit tests PASS;
- OpenAPI drift PASS;
- PostgreSQL migration/seed/integration PASS, including knowledge graph round-trip, SourceArtifact replay idempotency and append-only ClaimAssessment history.

Explicitly **not** implemented in PR #66: HTTP/consumer Claim Graph, Context Claim-status remapping, provider/AI calls, global claimant identity resolution, automatic Candidate Case publication, graph database.

## 4. Current implementation gap

The ADR-0027 persistence/domain foundation is complete. The next behavior is **not yet contract-locked**.

Candidate next boundary, to be resolved against the canonical product/methodology documents before coding:
- provider-neutral ingestion orchestration + extraction/proposal/review workflow from SourceArtifact/NormalizedArtifact into reviewed Claims/Evidence/Arguments/Decision Problems/Candidate Cases; or
- editorial projection from accepted knowledge records into existing Case authoring drafts.

Consumer Claim Graph/UI should not be the next default step because the upstream ingestion/review/publication path is not yet executable.

Still later:
- WE/Signal bounded context + MethodologyVersion sample/scope/stakeholder semantics.
- Impact bounded context.
- Admin Flow Composer UX for non-default FlowTemplateVersion.
- production deployment/observability and full account continuity/share maturity.

The generic retest path remains fully executable without a Case-specific feature family: `DecisionRevision → Exposure/Intervention → DecisionRevision → DecisionDelta → Reflection`.

## 5. Recommended next sequence

1. **Lock the post-M4 ingestion/editorial orchestration boundary with a new ADR + machine-readable contract before implementation.**
   - preserve provider-specific logic behind SourceAdapter;
   - make extraction/classification outputs proposals with reproducible provenance;
   - define human/editorial acceptance/rejection and reprocessing semantics;
   - define how accepted Claims/Evidence/Arguments become Decision Problems/Candidate Cases without auto-publication;
   - reuse the existing Content Authoring lifecycle for actual Case draft/review/publish;
   - define idempotency/replay/job-state/error boundaries before introducing external providers or AI calls.
2. Implement only the locked orchestration slice with in-memory/PostgreSQL tests and no consumer UI unless separately contracted.
3. Lock an editorial projection contract if Candidate Case → Case Draft mapping is not included in that orchestration ADR.
4. Only after the upstream path is executable consider a consumer Claim/Argument read surface.
5. Then proceed to WE/Signal, Impact, Admin Flow Composer and infrastructure maturity in architecture-compatible slices.

No implementation may leapfrog an unresolved product/domain contract.

## 6. Guardrails

- Never leak result/Perspective into core pre-result decision paths.
- Never leak another user's private/PENDING reason.
- No raw comment feed or popularity-only ranking.
- Keep human reasons and AI summaries/proposals distinct.
- Preserve provenance, moderation, methodology and taxonomy-version metadata.
- No personality/ideology/psychometric inference from activity.
- Published CaseVersion never mutates in place.
- Editorial mutable state never enters consumer tables before publication.
- Provider-specific CMS/SQL/IdP/AI/source dependencies stay behind adapters.
- Consumer credentials never authenticate Admin commands.
- Client-provided Admin/audit identity is forbidden.
- Same-session CSRF and Admin assurance ordering remain binding.
- Runtime live config never silently reinterprets historical published objects.
- Flow execution must use CaseVersion-pinned resolved Flow.
- Flow runtime may expose result readiness but never pre-Commit result payload.
- Reflection remains server-derived, bounded and non-causal; no client Delta-causality inference.
- Claim ≠ claimant; source/claimant reputation/user popularity do not directly determine Claim State.
- EvidenceLink ≠ ClaimAssessment; SUPPORTS evidence is not automatically VERIFIED truth.
- Claim/Argument relations preserve required provenance where contracted.
- AI proposal ≠ editorial acceptance; autonomous publication remains forbidden.
- existing Context Claim-status projection stays unchanged until an explicit projection contract is accepted.
- Preview/demo infrastructure is dev/build-only and never production fallback.
- Signal sample classes never silently mix.
- Consensus/Signal is not formal authority and not KEFE opinion.

## 7. Continuation protocol

1. Read this file from `main`.
2. Inspect open PRs, recent merges and CI.
3. Fetch Drive CURRENT only when publication-source detail is required; verify its SHA against this checkpoint.
4. Resolve work against MPD v1.3.0 + ADR-0019 through ADR-0027 + registered contracts.
5. One coherent branch per vertical slice.
6. ADR + machine-readable contract before new behavior.
7. Preserve ports/adapters, versioning, provenance and historical reproducibility.
8. Tests/contracts ship with implementation.
9. Merge only with green relevant CI and no newer authority conflict.
10. Update CURRENT after every meaningful merge.
11. DOCX/PDF regenerate only at declared milestones; persist to Drive and read back/hash before declaring PASS.

## 8. New-chat recovery prompt

> Continue KEFE from `nazmi02551/KEFE`. Read `docs/status/CURRENT.md` on `main` first and inspect open PRs/recent CI. Official docs baseline is Ecosystem v3.4. Binding architecture is case-agnostic: `Primitive → Capability → FlowTemplateVersion → CaseVersion`, with `ME → WE → SIGNAL → IMPACT`. PR #60 / ADR-0025 implemented DecisionRevision → Exposure/Intervention → DecisionDelta. PR #64 / ADR-0026 completed generic server-derived non-causal Reflection. PR #65 / ADR-0027 locked first-class Claim/ClaimAssessment/Assertion/Evidence/Argument and provider-neutral normalized-ingestion semantics. PR #66, merged as `5e782612...`, implemented the ADR-0027 domain+persistence slice with PostgreSQL migration `20260729_0015`, Claim/Argument contract v1.1.0, core ERD v3 and manifest v1.33.0; exact-head API CI `30441698265` passed including PostgreSQL integration. The next behavior is not yet locked: resolve and contract the provider-neutral ingestion/extraction/review/Candidate Case orchestration boundary before coding. Do not add external provider/AI calls, auto-publication, Context status remapping, consumer Claim Graph UI or a graph DB without the required next ADR/contract.

## M2 DecisionRevision checkpoint — 2026-07-29

- main baseline `9d5b4b4d3bccb1e2f21479c921f07a6c51357c05`.
- migration `20260729_0013_decision_revision_lineage.py`.
- API/OpenAPI 0.15.0; generic Flow runtime 1.1.0; DecisionRevision lineage 1.1.0; Mobile Flow runtime UI 1.1.0; manifest 1.29.0.

## M3 Reflection checkpoint — 2026-07-29

- implementation baseline `2e2a3df8a3f95104db4c23556107677cf186372a`.
- migration `20260729_0014_reflection_completion.py`.
- API/OpenAPI 0.16.0; Reflection runtime 1.1; generic Flow runtime 1.2; Mobile Flow runtime UI 1.2; manifest 1.31.0.
- exact-head API CI `30438276272` PASS; Mobile CI `30438276284` PASS.

## M4 Claim/Argument checkpoint — 2026-07-29

- architecture-lock baseline `1088e9a6b53e38420fefd77263d291761fdf8041` via PR #65 / ADR-0027.
- implementation baseline `5e78261212454338ec957bcf854bfd1c50a54e11` via PR #66.
- migration `20260729_0015_claim_argument_knowledge.py`.
- `claim-argument-ingestion.v1.yaml` 1.1.0; `core-erd.v3.mmd`; manifest 1.33.0.
- exact-head implementation SHA `f9254619ee36e3af161540f644730d36486e17b2`.
- API CI `30441698265` PASS including PostgreSQL integration.
- next architecture slice is not yet accepted; ingestion/editorial orchestration must be locked before behavior implementation.
