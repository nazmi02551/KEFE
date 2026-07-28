# KEFE Current Project Checkpoint

**Updated:** 2026-07-28  
**Repository:** `nazmi02551/KEFE`  
**Default branch:** `main`  
**Latest verified implementation commit:** `9ee366dd1c645039271e45ebc84bce6630a00621`

This is the **single canonical durable engineering handoff**. Chat history is not a source of truth. At every continuation: read this file from `main`, inspect open PRs/recent CI, then use the current Drive publication artifact when editable DOCX/PDF source material is needed.

## 1. Official product and documentation authority

The case-agnostic decision-engine architecture milestone is **documentation validation PASS** and advances the official publication baseline to **KEFE Documentation Ecosystem v3.4**.

Current principal document versions:

- KEFE Master Product Document **v1.3.0** — Approved Canonical
- KEFE Documentation Governance **v1.5.0** — Approved
- KEFE Product Bible **v1.5.0** — Working Baseline
- KEFE Engineering Blueprint **v0.7.0** — Implementation Baseline
- KEFE MVP Delivery Plan **v1.3.0** — Approved Execution Baseline
- KEFE Admin Studio Specification **v1.3.0** — Approved Baseline
- KEFE Security & Privacy Model **v1.3.0** — Approved Baseline

Specialist baselines advanced with the same milestone:

- AI Architecture v1.2.0
- Analytics Event Dictionary v1.2.0
- Case & Scenario Library v1.2.0
- Civic Integrity Model v1.2.0
- Commercial & Growth Design v1.2.0
- Content & Question Design Bible v1.2.0
- Decision Graph Specification v1.2.0
- Editorial Transformation Guide v1.2.0
- Research Methodology v1.2.0
- Trust & Integrity Methodology v1.2.0

### v3.4 publication artifact

`KEFE_Documentation_Ecosystem_2026-07-28_v3.4_CURRENT.zip`

- active logical documents: **18**
- active DOCX+PDF files: **36**
- active PDF pages: **289**
- package audit: **PASS**
- accessibility high-severity findings: **0**
- ZIP SHA-256: `b14ca825d9b62ff00b7fc61a0f2530aa3d2dd0c7b7f0d222c477b8af9bde9b0b`
- Google Drive CURRENT file ID: `1MXvCTNPfv-pWYIHCo5KqpmTOf-3RyFhZ`
- Drive raw-file readback SHA-256: **MATCHED** the publication SHA above.

All final v3.4 DOCX sources were rendered; changed/critical title and architecture surfaces were visually inspected after version/date corrections; all 18 generated PDFs were preflighted; package manifest/audit/checksums and superseded archive were generated from final bytes.

### Recovery lineage

The original byte-level v3.3 publication ZIP recorded by PR #42 was no longer available. It was **not** silently recreated as the original artifact.

A semantic recovery artifact was built from the exact verified v3.2 package plus durable PR #40/#42/CURRENT evidence:

`KEFE_Documentation_Ecosystem_2026-07-28_v3.3_RECOVERY_R1.zip`

- audit: **PASS**
- SHA-256: `760a74d91f60339c0277cf4f0b568f5865d8677ed04c41a0f276738ef079e0c7`
- Drive archive file ID: `1I0n-kzYUk_p0rHTxR1IloDjUMITRVN8b`
- Drive raw-file readback SHA-256: **MATCHED**
- recovery provenance explicitly states that byte identity with the lost original v3.3 ZIP is not claimed.

The exact verified v3.2 source package remains available in Drive with file ID `1joFVxCQW29e-XMdu3cVViLLESU__GM-m` and SHA-256 `3af400c28a9849f0714bf1e4656a5cb4b0b625164f05183caff75984ac5bc223`. It was manually uploaded before the connector had write authorization for that file, so it remains in the KEFE folder rather than being moved by the connector; this does not affect its verified recovery role.

Binding documentation policy:

- DOCX is the editable official publication source; PDF is generated immutable publication output.
- Git-hosted ADRs, contracts and this checkpoint are the engineering continuation layer.
- Binary DOCX/PDF ecosystems live as milestone publication artifacts, not normal Git history.
- A milestone is complete only after render/QA, PDF preflight, manifest/audit/checksum, archive, persistent Drive upload **and raw readback hash verification**.
- Superseded/recovery artifacts are never presented as byte-identical originals unless their hashes prove it.

## 2. Binding product architecture

### Experience path and value lifecycle

Consumer Golden Path remains:

`Launch → Explore → Case → Context → Weigh → Commit → Reveal → Perspective → My KEFE Progress → Share`

The platform value lifecycle is separately:

`ME → WE → SIGNAL → IMPACT`

- **ME:** individual decision, reason, confidence, revision/delta and reflection.
- **WE:** descriptive collective results, reasons, segments, stakeholders, arguments, consensus/divergence.
- **SIGNAL:** methodology-qualified collective finding.
- **IMPACT:** traceable Signal → Target → Institution Response → Action → evidence → verified real-world effect.

### Case-agnostic composition

ADR-0019 and the machine-readable contracts are binding:

- KEFE is a **case-agnostic modular decision/public-reasoning engine**.
- Canonical composition hierarchy: `Primitive → Capability → FlowTemplateVersion → CaseVersion`.
- Composition over Case Types; new cases should not create new runtime `case_type`/feature families.
- Base Format is an editorial/interaction archetype, not a runtime Case subclass.
- Schema before Screen.
- Published CaseVersion pins resolved Flow/Step semantics plus relevant configuration/methodology versions.
- Flow Template is a reusable versioned starting composition, not product logic.
- Case-specific runtime behavior requires proof that no reusable Primitive/Capability can express it and requires an ADR.

### Commit, context and decision lineage

- Commit First remains mandatory and is **not** Blind First.
- Context/Sources may appear pre-Commit but cannot leak result/community/Perspective.
- Principle First and Actor/Source Blind are optional reusable methodological capabilities.
- `Context`, `Reveal`, `Exposure` and `Intervention` have distinct semantics.
- Generic decision lineage is `DecisionRevision → Exposure/Intervention → DecisionRevision → DecisionDelta`.
- Delta is generic `D1 + Intervention + D2`; dimension-specific delta engines are forbidden.

### Claims, arguments and ingestion

- Claim is first-class and **Claim ≠ claimant**.
- Initial Claim Types: `FACTUAL`, `CAUSAL`, `BEHAVIORAL`, `MOTIVE`, `NORMATIVE`, `LEGAL`, `PROCESS`, `PREDICTION`.
- Initial Claim States: `VERIFIED`, `SUPPORTED`, `CLAIMED`, `DISPUTED`, `UNVERIFIED`, `UNRESOLVED`, `FALSE`.
- Taxonomies are methodology-versioned, not permanent hard-coded truth semantics.
- Claim/Argument graphs must preserve what evidence/reply/argument actually addresses.
- One source may produce zero or many Claims, decision problems and Candidate Cases.
- Normalized ingestion can expand through `Source Artifact → Original Content → Media → Claims → External Evidence → Replies → Reply Claims → Argument Families → Decision Problems → Candidate Cases`.
- Rule, Process, Incentive, Observed Behavior and Motive Claim remain distinct; incentive does not prove motive.
- AI may extract/classify/normalize/suggest/compose/detect, but cannot become KEFE's normative/political/moral voice, final truth authority or autonomous publisher.

### Reusable capability direction

Reusable capability candidates include Principle First, Commit First, Actor/Source Blind, Evidence/Source/Actor Reveal, Role Flip, Counterargument, Claim/Argument Graph, Responsibility Analysis, Process Analysis, Incentive Map, Threshold Analysis, Fairness/Normative Model Comparison, Policy Simulator, Stakeholder Analysis, Reflection, Institution Response and Impact Tracking.

Real-world examples such as airline child seating, political discourse, apparel fairness, real-estate commission, legal fees or local/site governance are **architecture stress fixtures**, not feature families.

## 3. Signal and Impact integrity

- Collective Result ≠ Signal.
- Signal is not a high percentage alone.
- Minimum Signal dimensions include agreement, sample strength, data quality/integrity, stability, counterargument exposure, counterargument resilience, stakeholder distribution/gap, scope alignment and freshness under a MethodologyVersion.
- `CORE_PRE_RESULT`, `EXPOSED`, `ADVOCACY_SUPPORT` are separate contribution classes and must never be silently pooled.
- Seeing result/Signal before deciding permanently excludes that decision from the core pre-result sample for that exposure lineage.
- A Signal Card mini-weigh after result exposure is `EXPOSED`.
- Advocacy Support is not a decision sample.
- Challenge Card and Signal/Consensus Card are distinct product semantics; implementation inheritance is intentionally not yet fixed.
- Scope Alignment is mandatory; an unrelated broad population cannot be framed as formal authority for a narrow target population.
- Stakeholder Gap must not be hidden by an overall percentage.
- Consensus/Signal does not create legal, contractual, corporate, electoral or governance authority.
- KEFE has no normative view derived from a Signal; copy attributes the finding to a methodology-qualified community pattern.
- Institution Response requires provenance/authority verification appropriate to the Target and may become a generic Intervention for a later DecisionRevision/Delta.
- Impact verification must not claim causality without evidence.

MethodologyVersion must be able to pin claim/argument taxonomies, capability semantics that affect interpretation, sample/contribution rules, Signal/Consensus criteria, scope/stakeholder rules, relevant AI classifications and composition/recommendation semantics.

## 4. Existing executable foundation

Already implemented and retained:

- FastAPI modular monolith + PostgreSQL; idempotent linearizable Commit; transactional outbox and durable worker.
- Hashed/revocable guest sessions and admission guard ports.
- Explore/Case read path, typed questions, pre-Commit Context/Sources, private structured Reason Capture.
- Commit-gated Reveal and bounded Perspective with curated fallback.
- actor-scoped My KEFE Progress and optional post-Reveal Account Offer.
- provider-neutral Content Authoring lifecycle with immutable published CaseVersion and PostgreSQL editorial persistence/atomic consumer materialization.
- dedicated Admin security domain, capability-first authorization, MFA/session assurance, same-session CSRF, recent step-up and server-derived audit identity.
- secured internal Admin authoring HTTP surface at `/internal/admin/v1`; no Admin login/SSO endpoint yet.
- ADR-0018 versioned Content Configuration foundation: stable Domain/Topic/Base Format/Modifier IDs, immutable published config, clone-based rollback and server-derived review requirements.

Important gap: working code still primarily models `CaseVersion → Issues/Questions + Context/Sources`; generic Flow/Step composition, DecisionRevision/Exposure/Intervention/Delta, first-class Claim/Argument graph, Signal and Impact are architecture-locked but implementation-pending.

## 5. Open work and PR #45

PR #45 is preserved as a **draft architecture-reassessment branch**. Its PostgreSQL persistence mechanics are valuable, but it must not merge against the older narrow ContentConfiguration aggregate.

Preserve from PR #45:
- isolated `content_config` schema,
- immutable DRAFT/PUBLISHED/SUPERSEDED lifecycle,
- one-published-version guard,
- clone provenance,
- append-only audit,
- atomic publish/supersede transaction,
- provider-neutral repository boundary and PostgreSQL tests.

Reassess before ready-for-review:
- Primitive/Capability/Flow Template registry scope,
- versioned Step/Flow semantics,
- publication-time resolved Flow/config/methodology provenance,
- contract/schema/manifest alignment after ADR-0019.

Its last pre-reassessment API CI run (`30360284669`) completed successfully; that green run does **not** authorize merge under the new architecture.

## 6. Recommended next sequence

1. **Reconcile Content Configuration with ADR-0019**
   - design the versioned Primitive/Capability/FlowTemplate/Step configuration aggregate,
   - decide which semantics belong to content configuration vs methodology registry,
   - update ADR/contracts before code,
   - then rebase/reshape PR #45 or replace it if the diff becomes incoherent.
2. **First generic Flow/Step vertical slice**
   - prove at least materially different stress fixtures can use the same engine without case-specific code.
3. **DecisionRevision / Exposure / Intervention / Delta**
   - generic lineage and provenance; no dimension-specific engines.
4. **First-class Claim + Argument Graph and ingestion normalization**.
5. **WE/Signal foundation**
   - sample lineage, contribution classes, scope, stakeholders, methodology pinning.
6. **Impact foundation**
   - Target, Official Response, Action, Evidence, Verification.
7. Resume observability/deployment, account continuity and share work in architecture-compatible slices.

No product implementation should leapfrog the ADR/contract decision for its bounded context.

## 7. Continuing guardrails

- Never expose result/Perspective before Commit unless the product object is explicitly an exposed Signal surface; exposed contributions remain separated from core.
- Never leak another user's private/PENDING reason.
- No raw comment feed or popularity-only ranking.
- Keep human reasons and AI summaries distinct.
- Preserve provenance, moderation and methodology metadata.
- No personality/ideology/psychometric inference from activity.
- Published CaseVersion is never mutated in place.
- Mutable editorial states never enter consumer read models before publication.
- Provider-specific CMS/SQL/IdP/AI details stay behind adapters.
- Consumer credentials never authenticate Admin commands.
- Client-provided Admin/audit identity is forbidden.
- Same-session CSRF and Admin assurance ordering remain binding.
- Runtime live configuration never silently reinterprets historical published content/results.
- Signal sample classes never silently mix.
- Consensus/Signal is not formal authority and not KEFE's own opinion.

## 8. Continuation protocol

1. Read this file from `main`.
2. Inspect open PRs, recent merges and latest CI; never infer state from chat memory.
3. When publication-source detail is needed, fetch the Drive CURRENT artifact and verify its SHA-256 against this file before use.
4. Resolve the next slice against MPD v1.3.0 + ADR-0019 + registered contracts.
5. One coherent branch per vertical slice.
6. Lock behavior in ADR + machine-readable contract before implementation.
7. Preserve ports/adapters, versioning, provenance and immutable historical interpretation.
8. Add tests/contracts in the same implementation PR.
9. Merge only with relevant CI green and no newer authority conflict.
10. Update this checkpoint after every meaningful merged milestone.
11. Regenerate DOCX/PDF only at declared documentation milestones; always persist to Drive and read back/hash before declaring the milestone complete.

## 9. New-chat recovery prompt

> Continue KEFE development from `nazmi02551/KEFE`. First read `docs/status/CURRENT.md` on `main`, then inspect open PRs/recent commits/CI. Fetch the Drive CURRENT documentation artifact only if publication-source detail is needed and verify its SHA against CURRENT. The official documentation baseline is Ecosystem v3.4: MPD v1.3.0, GOV v1.5.0, PB v1.5.0, ENG v0.7.0, MVP v1.3.0, ADM v1.3.0, SEC v1.3.0 and specialist v1.2.0 baselines. ADR-0019 locks KEFE as a case-agnostic composable decision/public-reasoning engine: Primitive → Capability → FlowTemplateVersion → immutable CaseVersion; ME → WE → SIGNAL → IMPACT is the value lifecycle. Commit First remains global, Blind variants optional. Use generic DecisionRevision/Exposure/Intervention/Delta; Claim is first-class and distinct from claimant; Collective Result ≠ Signal; CORE_PRE_RESULT/EXPOSED/ADVOCACY_SUPPORT never mix; Scope Alignment and Stakeholder Gap are binding; Signal is not formal authority or KEFE opinion; Impact requires provenance/evidence. PR #45 is draft pending ContentConfiguration aggregate reassessment against ADR-0019. Do not code an unlocked product decision.
