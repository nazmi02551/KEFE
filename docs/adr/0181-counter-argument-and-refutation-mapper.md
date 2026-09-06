# ADR-0181: Counter-Argument and Refutation Mapper (CAP-043)

## Status

ACCEPTED

## Context

Civic deliberation is not a collection of isolated monologues; arguments dialectically target, refute, or qualify opposing claims. Under `KEFE-CQB-001` (Content & Question Design Bible) and `KEFE-TIM-001` (Trust & Integrity), the platform implements an explicit refutation graph connecting arguments to their specific counter-theses.

## Decision

1. **Refutation Type Taxonomy**:
   - `DIRECT_EMPIRICAL_REBUTTAL`: Challenges factual premises with newer data.
   - `LOGICAL_INVALIDATION`: Exposes formal flaws in the inference step.
   - `VALUE_HIERARCHY_CHALLENGE`: Concedes facts but prioritizes a higher-order right.
   - `BOUNDARY_QUALIFICATION`: Shows the argument only holds under narrow edge conditions.
2. **Dialectical Pairing Structure**:
   - Stores `source_argument_id`, `target_argument_id`, `refutation_type`, `refutation_strength` ($[0.0, 1.0]$), and explanatory thesis.

## Consequences

- Visualizes true argumentative discourse rather than parallel shouting matches.
- Elevates civic dialectic literacy.
