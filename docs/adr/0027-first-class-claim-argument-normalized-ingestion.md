# ADR-0027 — First-Class Claim, Argument and Normalized Ingestion Boundary

- Status: Accepted
- Date: 2026-07-29
- Depends on: ADR-0013, ADR-0019, ADR-0020, ADR-0022

## Context

KEFE already has CaseVersion-pinned Context blocks and Source metadata for the consumer pre-Commit experience, plus version-owned editorial source references during Case authoring. Those structures were deliberately narrow: they support a published Case, but they are not a canonical knowledge graph.

The approved product/methodology baseline now requires a reusable Claim/Argument layer and a provider-neutral ingestion pipeline:

- Claim is first-class and Claim is not its claimant.
- one source artifact may yield zero or many Claims, decision problems and Candidate Cases;
- Claim state cannot be inferred directly from source or claimant reputation;
- Evidence and Claim-to-Claim relationships must preserve provenance;
- Argument relationships must distinguish SUPPORTS, OPPOSES, REBUTS, QUALIFIES and BRIDGES;
- replies must be linkable to the Claim, Question or Argument they actually address;
- AI may extract/classify/normalize/suggest/compose/detect, but is neither truth authority nor autonomous publisher.

Without a dedicated boundary, adding TODAY/real-event ingestion would either overload CaseVersion-owned Context rows or couple provider-specific scraping/social APIs directly to editorial and consumer models.

## Decision

### 1. Claim is independent of CaseVersion, Source and claimant

A canonical `Claim` is an immutable semantic atom with its own identity. It may be referenced by many source artifacts, assertions, evidence links, Arguments, decision problems and CaseVersions.

A Claim is not owned by a CaseVersion. A later publication may pin/reference accepted Claims, but publishing or revising a Case must not mutate canonical Claim history.

### 2. Claim evaluation is versioned, not a mutable truth flag

Claim semantic identity is separated from methodology/editorial evaluation.

An immutable `ClaimAssessment` records, at minimum:

- Claim identity;
- Claim Type;
- Claim State;
- taxonomy/methodology version reference;
- review/provenance metadata;
- assessment timestamp.

Initial Claim Types are:

- FACTUAL
- CAUSAL
- BEHAVIORAL
- MOTIVE
- NORMATIVE
- LEGAL
- PROCESS
- PREDICTION

Initial Claim States are:

- VERIFIED
- SUPPORTED
- CLAIMED
- DISPUTED
- UNVERIFIED
- UNRESOLVED
- FALSE

Taxonomy/state semantics are versioned. A new assessment appends history rather than rewriting an old assessment.

Source kind, source reputation, claimant reputation, popularity or user voting may be inputs to review, but none may directly determine Claim State.

### 3. Assertion/claimant lineage is separate

`ClaimAssertion` represents that an external claimant/actor asserted a Claim.

It stores an opaque claimant reference + claimant kind and may reference the SourceArtifact/NormalizedArtifact carrying the assertion. It does not embed a trust score into the Claim and does not change Claim State by itself.

KEFE does not require a global person/institution identity model in this slice. Claimant references remain provider/domain-neutral until a dedicated identity/entity-resolution contract is accepted.

### 4. Evidence links are first-class and non-authoritative

`EvidenceLink` connects a Claim to a source/normalized artifact using the initial relation family:

- SUPPORTS
- CONTRADICTS
- CONTEXTUALIZES

An EvidenceLink records provenance and review state. Creating a SUPPORTS link does not automatically mark a Claim VERIFIED/SUPPORTED; ClaimAssessment remains the evaluation authority.

### 5. Claim-to-Claim graph uses a versioned relation taxonomy

`ClaimRelation` connects one Claim to another and carries a relation code + taxonomy version + provenance.

ADR-0027 does not invent a closed Claim-to-Claim relation vocabulary beyond what the canonical documents already require. Relation codes are registry/version governed and can be extended without schema branching.

### 6. Argument is first-class and targets an explicit semantic object

An immutable `Argument` is distinct from a Claim. It may originate from editorial synthesis, a normalized reply, accepted human content or an AI proposal that later receives human review.

`ArgumentRelation` targets exactly one of:

- Claim
- Question
- Argument

Initial relation families are:

- SUPPORTS
- OPPOSES
- REBUTS
- QUALIFIES
- BRIDGES

The relation stores taxonomy version and provenance. When a reply target is known, it must be preserved. Parallel/unrelated replies must not be silently chained as one discussion thread.

### 7. Ingestion has a provider-specific edge and a provider-neutral core

Provider/source-specific logic ends at `SourceAdapter`.

The canonical normalized path is:

`SourceAdapter → SourceArtifact → NormalizedArtifact → Claims/Evidence/Replies/Arguments → Decision Problems → Candidate Cases`

`SourceArtifact` preserves immutable external provenance such as provider, external identifier/locator, capture time and payload/content hash.

`NormalizedArtifact` is provider-neutral and may represent original content, reply/thread items, external evidence or media metadata. A single SourceArtifact/NormalizedArtifact may produce zero or many downstream semantic nodes.

No adapter may create or publish a Case directly.

### 8. AI output is proposal lineage, not accepted truth

AI-derived extraction/classification/normalization output must carry enough provenance to reproduce the proposal, including task identity and available model/prompt/taxonomy/configuration versions.

AI proposals and editorial acceptance are separate auditable states. AI may not:

- autonomously publish a Case;
- become final Claim State authority;
- convert claimant reputation into truth;
- express KEFE's political, moral or normative verdict.

### 9. Editorial publication remains a separate boundary

Claim/Argument/Ingestion records live upstream of immutable consumer CaseVersion publication.

Accepted knowledge may be referenced by an editorial Case draft, but the existing authoring lifecycle remains authoritative for DRAFT → IN_REVIEW → APPROVED → PUBLISHED.

One accepted Claim or source artifact may contribute to multiple Candidate Cases and multiple published CaseVersions over time.

### 10. Existing Context claim status remains a presentation contract

The existing consumer `ContextBlock.claim_status` contract (`VERIFIED`, `CLAIMED`, `DISPUTED`, `UNKNOWN`) remains backward-compatible in this slice.

It is not redefined as the canonical seven-state ClaimAssessment model. Mapping canonical ClaimAssessment to consumer Context presentation requires a later explicit projection/publication contract.

This prevents a hidden breaking change and keeps the current pre-Commit Context API stable.

### 11. PostgreSQL remains canonical; graph database is deferred

The first implementation uses PostgreSQL relational tables with explicit graph edges and indexes. A specialized graph database is not introduced unless measured query requirements justify a separate ADR.

Provider SDKs, crawlers, social APIs and AI SDKs remain behind adapters.

### 12. Privacy and historical reproducibility remain mandatory

Knowledge records store minimum necessary claimant/source metadata. Sensitive identity resolution is not added implicitly.

Accepted semantic records and assessments are append-only/immutable where history matters. Corrections create new assessments/relations or compensating records rather than silently mutating published provenance.

No Claim/Argument activity may be used to infer personality, ideology or psychometrics without a separately approved methodology/consent contract.

## First implementation slice

The first executable M4 slice may implement:

1. Claim, ClaimAssessment, ClaimAssertion, EvidenceLink, ClaimRelation, Argument and ArgumentRelation domain models;
2. SourceArtifact and NormalizedArtifact ingestion models;
3. provider-neutral repository ports plus in-memory and PostgreSQL adapters;
4. append-only persistence and uniqueness/idempotency constraints;
5. contract/fitness tests proving Claim ≠ claimant, EvidenceLink ≠ ClaimAssessment and provider-specific logic stops at the adapter boundary.

It does **not** need to expose a consumer Claim Graph screen, alter Context API Claim statuses, publish Candidate Cases automatically or implement AI provider calls.

## Consequences

- TODAY and future real-event ingestion can grow without making source providers part of the Case domain.
- Claim provenance can be reused across multiple Cases and updates.
- Claim state history remains reproducible and is not collapsed into a mutable truth flag.
- Claimant identity/reputation is structurally separated from Claim evaluation.
- Argument/discussion topology can be analyzed without treating every reply as a factual Claim.
- Existing consumer Context and Content Authoring contracts remain compatible while first-class knowledge infrastructure is introduced upstream.

## Rejected alternatives

### Store Claims only inside CaseVersion

Rejected. One source/Claim can feed multiple decision problems and Cases, and Claim state can evolve independently of a published CaseVersion.

### Treat SourceReference or ContextSource as the canonical source artifact

Rejected. Those records are CaseVersion/editorial presentation projections and cannot safely carry provider ingestion lifecycle for multiple Cases.

### Store `claim_state` as a mutable field on Claim

Rejected. It destroys historical methodology/review reproducibility and makes later corrections overwrite prior state.

### Let source/claimant trust score determine Claim State

Rejected. It violates Claim ≠ claimant and turns reputation into a truth oracle.

### One generic `relation_type` table for Claims, Arguments, Evidence and replies

Rejected for the first slice. Their invariants differ. Shared storage can be reconsidered later, but semantic ports remain distinct.

### Build provider-specific ingestion services in the domain layer

Rejected. Provider logic must end at SourceAdapter.

### Let AI publish extracted Claims/Cases automatically

Rejected. AI proposal lineage and human/editorial acceptance remain separate.
