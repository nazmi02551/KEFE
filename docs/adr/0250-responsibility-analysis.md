# ADR-0250: Responsibility and Accountability Matrix Engine (CAP-020)

## Status

ACCEPTED

## Context

In complex societal dilemmas, governance debates, and institutional crises, accountability often breaks down through the diffusion of responsibility (the "bystander effect of governance" or jurisdictional finger-pointing). In accordance with `KEFE-PB-001` (Product Bible) and `KEFE-CQB-001` (Content & Question Design Bible), deliberators must be provided an objective, non-normative map of who bears what type of responsibility in a given dilemma.

Rather than assigning subjective moral blame, the Responsibility Analysis Engine decomposes institutional and civic accountability into distinct, verifiable dimensions:
1. Actor Categorization: Central ministries, local municipalities, regulatory oversight bodies, private operators, and civic communities.
2. Nature of Duty:
   - `LEGAL_LIABILITY`: Statutory liability and enforceable duty of care.
   - `REGULATORY_OVERSIGHT`: Supervisory, auditing, and compliance enforcement duty.
   - `OPERATIONAL_EXECUTION`: Day-to-day execution and implementation responsibility.
   - `FIDUCIARY_ETHICAL_DUTY`: Fiduciary stewardship and public interest trusteeship.
3. Accountability Gaps: Explicitly flags ambiguous regulatory boundaries or legal vacuums where no entity has enforceable responsibility.
4. Institutional Redress: Identifies specific formal channels (Administrative Courts, Ombudsman, Consumer Arbitration) available for citizen remedy.

## Decision

1. **Responsibility Allocation Matrix**:
   - For any case version, define an array of actor allocations with proportional responsibility shares $[0.0, 1.0]$.
   - Compute an overall `clarity_score` indicating the precision of legal jurisdictions.
   - Flag `has_accountability_gap` with an explanatory note when jurisdictions overlap or leave blind spots.

2. **API Specification**:
   - Expose `GET /v1/cases/{case_version_id}/responsibility-analysis` returning the complete allocation matrix, duty types, accountability gaps, and legal redress channels.

3. **Mobile Presentation**:
   - Render `ResponsibilityAnalysisCard` within the post-commit analytical perspective suite, showing proportional actor distribution, duty pills, clarity gauges, and redress pathways.

## Consequences

- Resolves jurisdictional confusion and empowers informed citizen deliberation.
- Maintains constitutional neutrality by focusing strictly on legal mandates and operational roles rather than political blame.
