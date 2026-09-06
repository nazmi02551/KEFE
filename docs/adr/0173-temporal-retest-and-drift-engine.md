# ADR-0173: Temporal Retest and Drift Engine (CAP-013)

## Status

ACCEPTED

## Context

Human values and civic opinions evolve over time as new life experiences, economic conditions, and societal events unfold. In accordance with `KEFE-PB-001` (Product Bible) and `KEFE-RM-001` (Research Methodology), re-evaluating the exact same dilemma blindly after a designated temporal delta ($\Delta t \ge 14$ days) yields deep insight into cognitive consistency vs attitude drift without shaming or inconsistency penalization.

## Decision

1. **Blind Retest Invariant**:
   - The user is presented with the case again without seeing their previous choice or notes until after re-committing.
2. **Drift Metrics**:
   - `is_shifted`: Whether the chosen option changed.
   - `confidence_delta`: Change in confidence level ($[-1.0, 1.0]$).
   - `time_elapsed_days`: Integer days since initial commitment.
   - `drift_nature`: `STABLE_CONVICTION`, `MATURED_REVISION`, `EXPLORATORY_SHIFT`, `REINFORCED_CERTAINTY`.

## Consequences

- Fosters self-reflection without moralistic judgment (My KEFE invariant).
- Captures longitudinal societal belief evolution.
