# ADR-0231: AI Hallucination & Cognitive Bias Auditing (CAP-091)

## Status

ACCEPTED

## Context

AI assistance across ethical dilemma synthesis cannot be treated as infallible truth authority. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE enforces automated hallucination detection and ideological bias scoring on all generated background syntheses and perspective summaries before editorial presentation.

## Decision

1. **Audit Health Status Taxonomy**:
   - `AUDIT_VERIFIED_GROUNDED`: High factual grounding and balanced neutrality.
   - `POTENTIAL_HALLUCINATION_FLAG`: Unsubstantiated factual claim detected.
   - `ASYMMETRIC_BIAS_SKEW`: Statistically skewed perspective weighting flagged.
2. **Grounding Invariant**:
   - Every AI synthesis requires citations to verifiable primary empirical evidence or explicit constitutional principles.

## Consequences

- Prevents AI hallucinations from distorting public deliberation.
- Enforces strict neutrality and factual rigor across all AI-generated content.
