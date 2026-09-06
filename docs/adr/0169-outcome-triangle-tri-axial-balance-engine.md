# ADR-0169: Outcome Triangle Tri-Axial Balance Engine (CAP-102)

## Status

ACCEPTED

## Context

Civic decisions involve trade-offs among three fundamental, non-reducable ethical dimensions: Rule of Law / Fundamental Rights, Empathy / Compassion for the Vulnerable, and Public Utility / Collective Efficiency. Projecting choices onto a tri-axial coordinate system provides users with profound clarity on the ethical balance of their stance.

## Decision

1. **Tri-Axial Coordinates**:
   - `rules_weight` ($0.0 - 1.0$): Prioritization of universal rules, constitutional rights, and legal consistency.
   - `empathy_weight` ($0.0 - 1.0$): Prioritization of compassion, protecting the vulnerable, and individual mercy.
   - `utility_weight` ($0.0 - 1.0$): Prioritization of public good, economic efficiency, and systemic order.
   - Constraint: $rules + empathy + utility = 1.0$.
2. **Dominant Archetype Classification**:
   - `RIGHTS_CENTRIC` ($\ge 0.50$ rules).
   - `EMPATHY_CENTRIC` ($\ge 0.50$ empathy).
   - `UTILITY_CENTRIC` ($\ge 0.50$ utility).
   - `TRI_BALANCED_HARMONY` (no axis $> 0.45$).

## Consequences

- Provides a visual geometric framework for multi-dimensional ethical trade-offs.
- Avoids reductionist 1D left-right political spectrums.
