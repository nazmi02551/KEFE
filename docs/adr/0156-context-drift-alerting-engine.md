# ADR-0156: Context Drift Alerting Engine (CAP-076)

## Status

ACCEPTED

## Context

Social, legal, and technological contexts surrounding an ethical dilemma evolve. When legislation changes, new scientific data emerges, or key assumptions shift, continuing to present a Case without disclosing this shift risks skewing ongoing deliberations.

## Decision

1. **Structured Context Drift Record**:
   - Case versions support audited `ContextDriftNotice` entries containing:
     - `drift_type`: `LEGAL_REFORM`, `FACTUAL_UPDATE`, `ASSUMPTION_CHANGED`, `SUPERSEDED_BASELINE`.
     - `effective_date`: UTC timestamp of the external change.
     - `summary`: Non-normative summary of what factual or legal condition changed.
     - `recommended_action`: e.g. `CONTINUE_WITH_AWARENESS`, `REVIEW_AMENDMENT`, `CASE_SUPERSEDED`.
2. **Non-Coercive Prominence**:
   - The notice is displayed as an objective banner before user commits without invalidating historical pre-drift snapshots.

## Consequences

- Prevents obsolete real-world premises from misinforming current deliberation.
- Protects the editorial integrity of historical snapshots while transparently informing current participants.
