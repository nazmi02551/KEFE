# ADR-0168: Evidence Builder and Verification Engine (CAP-098)

## Status

ACCEPTED

## Context

Deliberative public discussions frequently degenerate into unsubstantiated claims and rumor propagation. To anchor arguments in verifiable reality, participants and curators must be able to attach structured, auditable evidence records to perspectives and reasoning.

## Decision

1. **Structured Evidence Entity**:
   - Contains: `evidence_id`, `case_version_id`, `category` (`ACADEMIC_PEER_REVIEWED`, `OFFICIAL_GOVERNMENT_STAT`, `INVESTIGATIVE_JOURNALISM`, `INSTITUTIONAL_REPORT`), `title`, `publisher`, `source_url`, `doi_or_doc_ref`, `verification_status`.
2. **Quality Verification Hierarchy**:
   - `UNVERIFIED`: Raw user submission.
   - `COMMUNITY_VERIFIED`: Verified by multiple independent participants.
   - `EXPERT_AUDITED`: Certified by institutional/academic editorial auditors.

## Consequences

- Increases the epistemic quality of reasons and perspective cards.
- Fosters evidence-based civic discourse.
