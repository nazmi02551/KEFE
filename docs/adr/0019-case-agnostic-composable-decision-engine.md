# ADR-0019 — Case-agnostic composable decision engine and ME → WE → SIGNAL → IMPACT

**Status:** Accepted  
**Date:** 2026-07-28

## Context

KEFE has already established immutable CaseVersion publication, schema-driven questions, Context/Sources, Commit-gated Reveal/Perspective, versioned Content Configuration and provider-neutral Admin authoring. Stress testing against heterogeneous real-world problems — including consumer, civic, political, legal, economic, sports, governance and rights-conflict scenarios — showed that the current `CaseVersion → Issue → Question` shape is a sound foundation but is not yet general enough to make a new case primarily a content/configuration operation.

The product must not accumulate runtime case classes or case-specific backend/UI logic such as airline-child, political-insult, real-estate, legal-fee or local-governance feature families. The architecture must express these through reusable semantics and versioned composition.

The same stress test also established a second product lifecycle beyond the consumer navigation path: `ME → WE → SIGNAL → IMPACT`. Individual judgment and reflection are followed by collective understanding, methodology-qualified Signal, then traceable real-world follow-through. Signal is not synonymous with a result percentage, and Impact is not synonymous with advocacy.

## Decision

### 1. Product category and composition hierarchy

- KEFE is a **case-agnostic modular decision and public-reasoning engine**, not a survey engine or a collection of fixed case types.
- Composition over case types is binding.
- The canonical hierarchy is `Primitive → Capability → FlowTemplateVersion → CaseVersion`.
- A Base Format is an editorial/interaction archetype and authoring shortcut; it is not a runtime Case subclass or behavior discriminator.
- New real-world cases should be created through content, configuration and composition. Introducing case-specific runtime behavior requires evidence that the behavior cannot be expressed as a reusable Primitive/Capability and requires a separate ADR.
- Schema precedes screen implementation. UI surfaces render approved Step semantics; UI structure is not the product authority.

### 2. Versioned Flow and Step

- A published CaseVersion pins its resolved Flow semantics, Step ordering/branching, capability references and relevant methodology/configuration versions.
- A Case is not required to traverse a fixed global screen sequence. Different CaseVersions may compose different valid flows while preserving global guardrails such as Commit First and leakage constraints.
- Flow Templates are versioned reusable starting compositions. They are not product logic and must not become case-type inheritance.
- Long-term Admin authoring may provide a Flow Composer/Case Builder over the same versioned schemas.

### 3. Reusable decision semantics

- `Context` is decision-relevant information.
- `Reveal` is the action of making previously withheld information available.
- `Exposure` records that an Actor actually encountered information/result/perspective.
- `Intervention` is an exposure/event whose relationship to a later judgment is intentionally analyzed.
- `DecisionRevision` records an Actor's decision state at a point in the exposure lineage.
- `DecisionDelta` is generic: `D1 + Intervention + D2 → Delta`.
- Dimension-specific delta engines such as ActorDelta, LegalDelta, AgeDelta or CostDelta are forbidden. Dimensions are metadata/configuration over the common mechanism.
- Principle First, Actor/Source Blind, Evidence/Source/Actor Reveal, Role Flip, Counterargument Exposure, Responsibility Analysis, Process Analysis, Incentive Map, Threshold Analysis, Fairness/Normative Model Comparison, Policy Simulator, Stakeholder Analysis and Reflection are reusable capability candidates, not case-specific features.
- Blind variants are optional methodological capabilities. **Commit First remains the global rule and is not equivalent to Blind First.**

### 4. Claims, arguments and ingestion

- Claim is a first-class entity and is distinct from its claimant.
- Initial Claim Types are `FACTUAL`, `CAUSAL`, `BEHAVIORAL`, `MOTIVE`, `NORMATIVE`, `LEGAL`, `PROCESS`, `PREDICTION`.
- Initial Claim States are `VERIFIED`, `SUPPORTED`, `CLAIMED`, `DISPUTED`, `UNVERIFIED`, `UNRESOLVED`, `FALSE`.
- Claim taxonomies and status semantics are methodology-versioned; the above values are an accepted starting taxonomy rather than eternal enums.
- Claim and Argument graphs must be able to record what proposition/claim an evidence item, reply or argument actually supports, opposes, qualifies or otherwise addresses.
- A source is not a Case. One source may yield zero or many Claims, decision problems and Candidate Cases.
- The normalized ingestion lineage is capable of expanding through `Source Artifact → Original Content → Media → Claims → External Evidence → Replies → Reply Claims → Argument Families → Decision Problems → Candidate Cases`.
- Source-specific services terminate at adapters; normalized domain semantics remain provider-neutral.

### 5. AI boundary

- AI may `EXTRACT`, `CLASSIFY`, `NORMALIZE`, `SUGGEST`, `COMPOSE` and `DETECT`.
- AI does not become KEFE's normative, political or moral voice; it does not autonomously publish or serve as the final truth authority.
- Motive must not be inferred merely from incentive. Rule, Process, Incentive, Observed Behavior and Motive Claim remain distinct semantics.

### 6. ME → WE → SIGNAL → IMPACT

- The existing Golden Path remains the consumer experience path.
- `ME → WE → SIGNAL → IMPACT` is the platform value lifecycle.
- **ME** covers individual decision, reason, confidence, DecisionRevision/Delta and reflection.
- **WE** covers descriptive Collective Results, reasons, segments, stakeholders, argument patterns, consensus and divergence.
- **SIGNAL** is a methodology-qualified collective finding and is not equivalent to a Collective Result.
- **IMPACT** tracks a qualified Signal toward Target, Institution Response, Action, Impact Evidence and Impact Verification.

### 7. Signal integrity

- Signal must not be reduced to a support percentage.
- Signal assessment considers at least agreement, sample strength, data quality/integrity, stability, counterargument exposure, counterargument resilience, stakeholder distribution/gap, scope alignment and freshness under a MethodologyVersion.
- Contribution classes `CORE_PRE_RESULT`, `EXPOSED` and `ADVOCACY_SUPPORT` are semantically distinct and must never be silently pooled.
- Seeing a community result/Signal before deciding permanently excludes that decision from the core pre-result sample for that exposure lineage.
- A mini-weigh entered from an already revealed Signal Card may exist, but it is `EXPOSED`.
- Challenge Card and Signal/Consensus Card are distinct product semantics. Their implementation inheritance/aggregate relationship is intentionally not locked by this ADR.
- Scope alignment is mandatory for Signal qualification. A broad unrelated population must not be presented as governance authority for a narrow target population.
- Stakeholder gaps must not be hidden behind an overall percentage.
- Consensus/Signal describes a qualified observed community pattern; it does not confer legal, contractual, corporate, electoral or governance authority.
- KEFE does not claim a normative position from a Signal. Product copy attributes the finding to the methodology-qualified community signal.

### 8. Impact and institutional dialogue

- Impact lifecycle is `Signal → Target → Institution Response → Action → Impact Evidence → Impact Verification`.
- Official institutional responses require provenance and identity/authority verification appropriate to the target.
- An Institution Response may become a reusable Intervention and trigger a new DecisionRevision/DecisionDelta measurement without a response-specific decision engine.
- Impact status records observed/verified real-world follow-through; it must not fabricate causality between KEFE Signal and an external change without evidence.

### 9. Methodology versioning

MethodologyVersion must be able to pin at least:
- Claim taxonomy and semantics,
- Argument taxonomy and graph semantics,
- Capability semantics that affect interpretation,
- Sample definitions and contribution-class rules,
- Signal/Consensus criteria and scoring,
- Scope-alignment and stakeholder rules,
- AI classification behavior relevant to stored classifications,
- composition/recommendation semantics when they affect reproducibility.

Historical published CaseVersions, Collective Results and Signals must remain interpretable/reproducible against their pinned versions rather than future live configuration.

## Consequences

- Existing CaseVersion, Content Configuration and ports/adapters foundations remain useful but require expansion before being treated as the final configurable decision engine.
- PR #45's PostgreSQL persistence design is not rejected; its aggregate must be reassessed against this ADR before merge.
- The next implementation work must first extend the machine-readable configuration/domain contracts for Primitive/Capability/Flow composition, then implement one generic vertical slice rather than a case-specific feature.
- DecisionRevision/Exposure/Intervention/Delta, first-class Claims/Arguments, Signal and Impact become explicit roadmap bounded contexts/capabilities.
- Existing case examples are retained as architecture stress/regression fixtures, not feature families.
