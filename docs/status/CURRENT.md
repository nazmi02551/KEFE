# KEFE Current Project Checkpoint

**Updated:** 2026-07-28  
**Repository:** `nazmi02551/KEFE`  
**Default branch:** `main`  
**Latest verified implementation commit:** `7223dfeef55936f2fd70922bec74d3ce56232820`

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

### Current publication artifact

`KEFE_Documentation_Ecosystem_2026-07-28_v3.4_CURRENT.zip`

- 18 active logical documents / 36 active DOCX+PDF files
- 289 active PDF pages
- package audit PASS
- accessibility high-severity findings: 0
- SHA-256: `b14ca825d9b62ff00b7fc61a0f2530aa3d2dd0c7b7f0d222c477b8af9bde9b0b`
- Drive CURRENT file ID: `1MXvCTNPfv-pWYIHCo5KqpmTOf-3RyFhZ`
- Drive raw readback hash: MATCHED

Recovery lineage:
- v3.3 original byte-level publication artifact was lost and is **not** falsely reconstructed as byte-identical.
- `KEFE_Documentation_Ecosystem_2026-07-28_v3.3_RECOVERY_R1.zip`
  - SHA-256 `760a74d91f60339c0277cf4f0b568f5865d8677ed04c41a0f276738ef079e0c7`
  - Drive file ID `1I0n-kzYUk_p0rHTxR1IloDjUMITRVN8b`
  - raw readback hash MATCHED
- exact verified v3.2 remains recoverable with SHA-256 `3af400c28a9849f0714bf1e4656a5cb4b0b625164f05183caff75984ac5bc223`, Drive file ID `1joFVxCQW29e-XMdu3cVViLLESU__GM-m`.

Milestone completion requires render/QA + PDF preflight + manifest/audit/checksum + archive + persistent Drive upload + raw readback SHA verification.

## 2. Binding product architecture

Consumer experience path remains:
`Launch → Explore → Case → Context → Weigh → Commit → Reveal → Perspective → My KEFE Progress → Share`

Platform value lifecycle:
`ME → WE → SIGNAL → IMPACT`

ADR-0019 is binding:
- KEFE is a case-agnostic modular decision/public-reasoning engine.
- canonical composition: `Primitive → Capability → FlowTemplateVersion → CaseVersion`.
- Composition over Case Types; new cases should be content/configuration/composition, not new runtime feature families.
- Base Format is an editorial archetype, not a runtime Case class.
- Schema before Screen.
- published CaseVersion must eventually pin resolved Flow/Step plus relevant config/methodology versions.
- Commit First remains global; Blind/Principle First variants are reusable optional methodology capabilities.
- Context, Reveal, Exposure and Intervention are distinct.
- generic lineage: `DecisionRevision → Exposure/Intervention → DecisionRevision → DecisionDelta`; dimension-specific delta engines are forbidden.
- Claim is first-class and Claim ≠ claimant.
- initial Claim Types: FACTUAL, CAUSAL, BEHAVIORAL, MOTIVE, NORMATIVE, LEGAL, PROCESS, PREDICTION.
- initial Claim States: VERIFIED, SUPPORTED, CLAIMED, DISPUTED, UNVERIFIED, UNRESOLVED, FALSE; semantics are methodology-versioned.
- one source can yield multiple Claims, decision problems and Candidate Cases.
- AI may extract/classify/normalize/suggest/compose/detect, but is not KEFE's normative/political/moral voice or final truth authority.

Signal integrity:
- Collective Result ≠ Signal.
- Signal is not a percentage threshold; assessment includes agreement, sample strength, data quality, stability, counterargument exposure/resilience, stakeholder distribution/gap, scope alignment and freshness under MethodologyVersion.
- CORE_PRE_RESULT, EXPOSED and ADVOCACY_SUPPORT never silently mix.
- result exposure excludes that decision from the core pre-result sample for that lineage.
- Challenge Card and Signal/Consensus Card are semantically distinct.
- Scope Alignment is mandatory and Stakeholder Gap may not be hidden.
- Signal/Consensus is not formal authority and not KEFE's own opinion.
- Impact lifecycle: Signal → Target → Institution Response → Action → Impact Evidence → Impact Verification.

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
- secured internal Admin authoring HTTP under `/internal/admin/v1`; no Admin login/SSO endpoint yet.
- ADR-0018 versioned Content Configuration foundation.

### PR #47 / ADR-0020 — composable configuration foundation — COMPLETE

Implementation commit: `7223dfeef55936f2fd70922bec74d3ce56232820`

Added:
- ADR-0020 and `composable-content-configuration.v1.yaml`.
- `PrimitiveDefinition` registry.
- `CapabilityDefinition` registry with Primitive compatibility.
- `FlowStepDefinition`.
- versioned `FlowTemplateDefinition`.
- ContentConfigurationSnapshot now owns Primitive/Capability/FlowTemplate registries while retaining Domain/Topic/Base Format/Modifier compatibility.
- bootstrap generic composition examples:
  - `STANDARD_COMMIT_REVEAL`
  - `PRINCIPLE_CONTEXT_RETEST`
- configuration save/publish validation for duplicate identities, unknown references, capability/primitive incompatibility, entry/transition integrity and required terminal Step.
- error registry v1.9.0 and contract manifest v1.21.0.

Verification:
- API CI run `30383888427` PASS.
- lint PASS.
- contract sync PASS.
- Admin HTTP contract PASS.
- OpenAPI drift PASS.
- unit tests PASS.
- PostgreSQL integration PASS.

This proves materially different Flow compositions can share the same generic configuration schema without case-specific runtime types.

Still implementation-pending:
- PostgreSQL persistence of the **expanded** ContentConfiguration aggregate.
- Admin HTTP management of expanded registries.
- authoring/consumer CaseVersion resolved Flow pinning and generic execution/rendering.
- DecisionRevision/Exposure/Intervention/Delta.
- first-class Claim/Argument graph and normalized ingestion.
- WE/Signal and Impact bounded contexts.

## 4. PR #45 status

PR #45 remains **draft** and must not merge as-is. It was built against the pre-ADR-0019 narrow ContentConfiguration aggregate.

Its reusable persistence mechanics remain valuable:
- isolated `content_config` PostgreSQL schema,
- immutable DRAFT/PUBLISHED/SUPERSEDED lifecycle,
- one-published-version guard,
- JSONB aggregate storage,
- clone provenance,
- append-only audit,
- atomic publish/supersede,
- provider-neutral repository boundary,
- PostgreSQL integration coverage.

Next work should port/rebase these mechanics onto the expanded ADR-0020 aggregate rather than discarding them or merging the old branch unchanged.

## 5. Recommended next sequence

1. **Expanded Content Configuration PostgreSQL persistence**
   - use PR #45 mechanics but serialize/deserialize Primitive/Capability/FlowTemplate definitions,
   - retain atomic publish, audit, rollback and one-published-version guarantees,
   - update schema/contract snapshots and PostgreSQL integration tests.
2. **Secured Admin configuration HTTP** using existing Admin session/CSRF/TAXONOMY_MANAGE boundary.
3. **Resolved Flow pinning** onto authoring publication and consumer CaseVersion, then one generic Flow executor/renderer slice.
4. **DecisionRevision / Exposure / Intervention / Delta**.
5. **First-class Claim + Argument Graph + ingestion normalization**.
6. **WE/Signal foundation** with contribution classes, scope/stakeholders and MethodologyVersion.
7. **Impact foundation** with Target, Official Response, Action, Evidence and Verification.
8. Resume observability/deployment, account continuity and share in architecture-compatible slices.

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
- Signal sample classes never silently mix.
- Consensus/Signal is not formal authority and not KEFE opinion.

## 7. Continuation protocol

1. Read this file from `main`.
2. Inspect open PRs, recent merges and CI.
3. Fetch Drive CURRENT only when publication-source detail is required; verify its SHA against this checkpoint.
4. Resolve work against MPD v1.3.0 + ADR-0019 + ADR-0020 + registered contracts.
5. One coherent branch per vertical slice.
6. ADR + machine-readable contract before new behavior.
7. Preserve ports/adapters, versioning, provenance and historical reproducibility.
8. Tests/contracts ship with implementation.
9. Merge only with green relevant CI and no newer authority conflict.
10. Update CURRENT after every meaningful merge.
11. DOCX/PDF regenerate only at declared milestones; persist to Drive and read back/hash before declaring PASS.

## 8. New-chat recovery prompt

> Continue KEFE from `nazmi02551/KEFE`. Read `docs/status/CURRENT.md` on `main` first, inspect open PRs/recent CI, and use the Drive CURRENT artifact only when publication-source detail is required. Official docs baseline is Ecosystem v3.4 (MPD 1.3.0, GOV 1.5.0, PB 1.5.0, ENG 0.7.0, MVP/ADM/SEC 1.3.0, specialists 1.2.0). ADR-0019 locks the case-agnostic engine: Primitive → Capability → FlowTemplateVersion → CaseVersion; ME → WE → SIGNAL → IMPACT; generic DecisionRevision/Exposure/Intervention/Delta; Claim ≠ claimant; Result ≠ Signal; CORE_PRE_RESULT/EXPOSED/ADVOCACY_SUPPORT separation; Scope/Stakeholder integrity; verified Impact. ADR-0020 and PR #47 (`7223dfe...`) implement the first composable Content Configuration foundation with Primitive/Capability/FlowTemplate registries and validation. PR #45 remains draft; reuse its PostgreSQL persistence mechanics only after adapting them to the expanded aggregate. Do not code an unlocked product decision.
