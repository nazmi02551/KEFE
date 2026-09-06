# ADR-0172: Case Objection and Challenge Engine (CAP-068)

## Status

ACCEPTED

## Context

Under `KEFE-TIM-001` (Trust & Integrity Methodology Standard) and `KEFE-CIV-001` (Civic Integrity Standard), no editorial team holds monopoly over truth. If a dilemma is framed with subtle bias, ignores a crucial stakeholder, or relies on superseded factual claims, the public must possess a formal, structured mechanism to challenge the case.

## Decision

1. **Formal Objection Taxonomy**:
   - `EDITORIAL_BIAS_FRAMING`: Slanted question or description.
   - `FACTUAL_INACCURACY`: Verifiable empirical error.
   - `EXCLUDED_STAKEHOLDER`: Critical affected group omitted from options.
   - `AMBIGUOUS_OPTIONS`: Choices that overlap or misrepresent positions.
   - `DEPRECIATED_CONTEXT`: Context invalid due to legal/factual drift.
2. **Auditable Challenge Lifecycle**:
   - Objections require a typed reason, detailed statement ($\ge 20$ chars), and optional supporting evidence URL.
   - State transition: `SUBMITTED` $\rightarrow$ `UNDER_REVIEW` $\rightarrow$ (`ACCEPTED_CORRECTION_FILED` | `REJECTED_WITH_REASON`).

## Consequences

- Empowered participatory civic scrutiny.
- Direct feedback loop into editorial correction pipelines (`CAP-072`).
