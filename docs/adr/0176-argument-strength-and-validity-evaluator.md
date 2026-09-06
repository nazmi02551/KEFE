# ADR-0176: Argument Strength and Validity Evaluator (CAP-041)

## Status

ACCEPTED

## Context

Under `KEFE-CQB-001` (Content & Question Design Bible) and `KEFE-TIM-001` (Trust & Integrity), civic arguments must be evaluated not by rhetorical emotionalism or popularity, but by logical soundness, empirical groundedness, and dialectical robustness.

## Decision

1. **Soundness Dimensions**:
   - `EMPIRICAL_FOUNDATION`: Backed by verifiable evidence ($[0.0, 1.0]$).
   - `LOGICAL_CONSISTENCY`: Absence of internal non-sequiturs or contradictions ($[0.0, 1.0]$).
   - `REPRESENTATIVE_BALANCE`: Accounts for counter-arguments ($[0.0, 1.0]$).
2. **Composite Strength Tier**:
   - Computes weighted composite score:
     - `TIER_A_ROBUST` ($\ge 0.80$).
     - `TIER_B_PLAUSIBLE` ($[0.50, 0.79]$).
     - `TIER_C_WEAK_RHETORICAL` ($< 0.50$).

## Consequences

- Promotes high-quality deliberative debate.
- Prevents populist rhetorical manipulation.
