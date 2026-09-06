# ADR-0180: Secondary and Unintended Consequences Simulator (CAP-022)

## Status

ACCEPTED

## Context

Well-intentioned public interventions frequently produce second-order perverse incentives, behavioral rebound effects, or market distortions (e.g., Cobra effect). In accordance with `KEFE-CQB-001` (Content & Question Design Bible) and `KEFE-PB-001` (Product Bible), every major case option must include simulated second- and third-order ripple consequences.

## Decision

1. **Unintended Consequence Taxonomy**:
   - `PERVERSE_INCENTIVE`: System incentivizes the opposite of the intended goal.
   - `MARKET_DISTORTION`: Artificial shortages or supply misallocations.
   - `BEHAVIORAL_REBOUND`: Increased efficiency causing higher total consumption (Jevons paradox).
   - `SYSTEMIC_DISPLACEMENT`: Problem shifts to adjacent vulnerable groups or regions.
2. **Mitigation Scoring**:
   - Evaluates severity alongside mitigation feasibility ($[0.0, 1.0]$).

## Consequences

- Prevents naive linear policy thinking.
- Prepares citizens for complex systemic trade-offs.
