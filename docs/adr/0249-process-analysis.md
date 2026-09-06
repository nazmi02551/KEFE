# ADR-0249: Process Analysis Engine (CAP-021)

## Status

ACCEPTED

## Context

In complex socio-political and institutional dilemmas, the legitimacy of an outcome is deeply intertwined with the legitimacy of the decision-making process itself (procedural justice). In accordance with `KEFE-PB-001` (Product Bible) and `KEFE-CQB-001` (Content & Question Design Bible), citizens and deliberators must be able to inspect *how* decisions are reached, distinct from their substantive agreement or disagreement with the policy.

Traditional reporting frequently conflates procedural illegitimacy with ideological opposition. The Process Analysis Engine introduces a structured, objective, and non-normative lens into the deliberation lifecycle:
1. Procedural Steps & Stages (e.g. Public Consultation, Impact Assessment, Legal Drafting, Public Hearings, Enactment, Independent Oversight).
2. Procedural Integrity & Transparency Level (`HIGH`, `MODERATE`, `RESTRICTED`, `OPAQUE`).
3. Public Participation Breadth (`OPEN_CONSULTATION`, `INVITED_STAKEHOLDERS_ONLY`, `FORMAL_NOTICE_ONLY`, `EXECUTIVE_BYPASS`).
4. Attribution of Independent Oversight and bottlenecks.

## Decision

1. **Procedural Justice Framework**:
   - Every published case or decision problem optionally defines or deterministically computes a `ProcessAnalysis` record.
   - Evaluates adherence to due process, public commentary windows, and institutional checks and balances.
   - Strictly preserves constitutional invariants: non-normative, descriptive, and politically neutral.

2. **API Specification**:
   - Expose `GET /v1/cases/{case_version_id}/process-analysis` returning structured stage progression, procedural integrity score ($[0.0, 1.0]$), transparency level, and participation status.

3. **Mobile Presentation**:
   - Render `ProcessAnalysisCard` within the post-commit analytical perspective suite and case explorer, providing a clean step-by-step audit trail, procedural score gauge, and transparency badges.

## Consequences

- Elevates civic literacy by distinguishing procedural flaws from substantive policy disagreements.
- Fosters institutional accountability through transparent audit trails.
- Complies with KEFE core invariants: Commit First, descriptive non-normative reporting, and zero psychometric profiling.
