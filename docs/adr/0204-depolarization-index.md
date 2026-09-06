# ADR-0204: Depolarization & Bridge Efficacy Index (CAP-117)

## Status

ACCEPTED

## Context

Social platforms often optimize for engagement that inadvertently amplifies affective polarization. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-TIM-001`, KEFE evaluates whether deliberation systematically reduces inter-group hostility and increases cross-group resonance through a mathematical Depolarization Index ($D_{index} \in [0.0, 1.0]$).

## Decision

1. **Index Formulation**:
   - $D_{index} = 1.0 - \text{BimodalityCoeff}(\Delta \text{Opinion}) \times \text{AffectiveDistance}$.
   - Measures narrowing of sentiment distance between opposed clusters post-deliberation.
2. **Efficacy State**:
   - `HIGH_DEPOLARIZATION`: Significant convergence across opposed groups.
   - `MODERATE_BRIDGE_RESONANCE`: Constructive dialogue without total synthesis.
   - `PERSISTENT_POLARIZATION`: Rigid adherence to polarized extremes.

## Consequences

- Direct quantitative measurement of healthy civic dialogue.
