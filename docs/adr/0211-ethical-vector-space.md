# ADR-0211: Multi-Dimensional Ethical Vector Space (CAP-096)

## Status

ACCEPTED

## Context

Complex moral dilemmas rarely collapse onto a 1D left-right or binary axis. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE models dilemmas and collective weighing in an $N$-dimensional ethical vector space spanning Utilitarian Impact, Deontological Rights, Communitarian Harmony, and Intergenerational Care without reducing moral complexity.

## Decision

1. **Vector Coordinates**:
   - `utilitarian_weight` $\in [0.0, 1.0]$: Consequential welfare and harm minimization.
   - `deontological_weight` $\in [0.0, 1.0]$: Inalienable rights and duties.
   - `communitarian_weight` $\in [0.0, 1.0]$: Social cohesion and collective solidarity.
   - `intergenerational_weight` $\in [0.0, 1.0]$: Future posterity and ecological foresight.
2. **Dominant Moral Attractor**:
   - Determined by highest vector magnitude coordinate without ideological profiling.

## Consequences

- Expresses rich multi-dimensional ethical nuance visually.
- Avoids oversimplified binary political polarization.
