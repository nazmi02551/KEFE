# ADR-0182: Expert Testimony and Institutional Endorsement Engine (CAP-044)

## Status

ACCEPTED

## Context

In complex ethical debates, corporate PR statements are often conflated with independent scientific consensus. Under `KEFE-CQB-001` (Content & Question Design Bible) and `KEFE-TIM-001` (Trust & Integrity), the platform explicitly segregates independent peer-reviewed expertise from institutional, regulatory, and corporate advocacy.

## Decision

1. **Testimony Archetype Taxonomy**:
   - `INDEPENDENT_ACADEMIC_EXPERT`: Peer-reviewed scientific authority.
   - `GOVERNMENTAL_REGULATORY_BODY`: Official administrative and regulatory agencies.
   - `INDUSTRY_CORPORATE_STAKEHOLDER`: Commercial entities with financial stakes.
   - `CIVIL_SOCIETY_ADVOCATE`: NGOs, unions, and grassroots public advocates.
2. **Conflict-of-Interest Transparency Invariant**:
   - Every testimony mandates a declared conflict-of-interest risk index ($[0.0, 1.0]$) and epistemic credibility tier.

## Consequences

- Prevents corporate astroturfing and regulatory capture of public discourse.
- Fulfills epistemic integrity requirements.
