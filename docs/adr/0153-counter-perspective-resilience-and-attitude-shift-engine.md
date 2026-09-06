# ADR-0153: Counter-Perspective Resilience and Attitude Shift Engine (CAP-116)

## Status

ACCEPTED

## Context

A fundamental goal of KEFE is deliberative maturity—enabling citizens to confront opposing arguments, understand nuanced trade-offs, and either reinforce their convictions or thoughtfully revise their stance.

To measure the effectiveness of deliberative exposure without evaluating or profiling individual psychological traits, the system requires an aggregated metric for cognitive resilience and attitude shifting.

## Decision

1. **Governed Deliberation Metrics**:
   - `PerspectiveResilienceMetric` measures aggregate stability versus revision rates following exposure to `COUNTER_PERSPECTIVE` or `OPPOSING` interventions.
   - `resilience_index`: Proportion of participants whose core decision remains stable after counter-argument exposure.
   - `attitude_shift_rate`: Proportion of participants who revised their choice or confidence level after deliberation.
2. **Strict Privacy Invariant**:
   - Computations operate exclusively on aggregated diff snapshots (`DecisionDelta.diff_snapshot['changed']`) and exposure links.
   - No individual psychometric scoring, ideological labeling, or political orientation is derived or stored.

## Consequences

- Provides research-grade deliberative quality metrics.
- Preserves complete anonymity and user privacy.
