# ADR-0011 — CaseVersion-pinned Context and Source read layer

**Status:** Accepted  
**Date:** 2026-07-27

## Context

The canonical KEFE journey places Context before Weigh. Users must be able to inspect relevant context and sources without seeing community results, Perspective cards or any post-Commit signal. Context also has to remain reproducible: a decision must be traceable to the same immutable CaseVersion and evidence set the user saw.

KEFE already separates factual status from opinion and uses the claim states `VERIFIED`, `CLAIMED`, `DISPUTED` and `UNKNOWN`. The Context slice must preserve that distinction without turning source metadata into an implicit truth score.

## Decision

### API boundary

- Context is read through the immutable CaseVersion identifier, not through the mutable current Case alias.
- The endpoint is `GET /v1/case-versions/{case_version_id}/context`.
- The endpoint is public/read-only in the M0, just like Case discovery/detail; no decision identity is required to inspect evidence.
- The response contains only Context/Source material pinned to that CaseVersion. It must not contain result distributions, Perspective cards, participant reasons, expert comparisons or other post-Commit data.

### Context blocks

- A CaseVersion can expose ordered Context blocks.
- Each block has a stable ID, explicit display order, disclosure level, title, body, claim status and source references.
- Initial disclosure levels are `ESSENTIAL` and `DETAIL`.
- Initial claim states are exactly:
  - `VERIFIED`
  - `CLAIMED`
  - `DISPUTED`
  - `UNKNOWN`
- Claim status describes the evidentiary status of the statement represented by the block. It is not a popularity score and is not user-votable.

### Sources

- Sources are CaseVersion-pinned metadata snapshots.
- Initial fields are source ID, label/title, publisher, optional URL, optional publication timestamp and source kind.
- Initial source kinds are `OFFICIAL`, `NEWS`, `RESEARCH`, `EDITORIAL` and `OTHER`.
- A source kind is provenance metadata. It is not itself a truth verdict.
- Source quality/trust methodology, when introduced, must use an explicit independent contract and must not be inferred from claim status.

### Progressive disclosure

- `ESSENTIAL` blocks are intended for the default Context surface.
- `DETAIL` blocks are intended for explicit expansion.
- The server preserves editorial order; clients must not locally re-rank evidence by engagement or ideology.
- A Context response may contain zero blocks and zero sources for an evergreen low-risk DILEMMA.

### Bounds and safety

- The read is bounded to at most 20 Context blocks and 20 Source records per CaseVersion in this M0 contract.
- Block bodies are plain text in the M0; executable HTML is not part of the contract.
- URLs are returned only as source metadata. Clients must open them using platform-safe external navigation and must not embed untrusted remote HTML into the KEFE surface.

### Versioning and analytics

- Context/Source records are linked to the immutable CaseVersion so a decision can later be interpreted against the information set available at that time.
- Future `context.expanded` and `source.opened` analytics events may reference IDs from this contract, but analytics are not required to serve the read model.

## Consequences

- A newly published CaseVersion may carry a different Context/Source set without mutating prior decisions.
- The mobile client can progressively disclose evidence before Commit without leaking results.
- Claim status and source provenance remain separate concepts.
- Fact-check scoring, source trust tiers, full editorial authoring workflow, external-page caching and legal jurisdiction-specific source rules remain later slices.
