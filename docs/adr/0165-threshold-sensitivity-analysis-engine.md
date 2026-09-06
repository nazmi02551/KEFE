# ADR-0165: Threshold Sensitivity Analysis Engine (CAP-018)

## Status

ACCEPTED

## Context

Many ethical and public policy dilemmas are not binary absolutes; they hinge on acceptable quantitative risk or cost thresholds (e.g., "At what accident probability is autonomous operation acceptable?" or "What tax increase is justified for free public transit?").

## Decision

1. **Parametric Sensitivity Model**:
   - Analyzes user decision curves across a defined parameter range (e.g. `min_value`, `max_value`, `unit`).
   - Identifies the critical `tipping_point_threshold` where aggregate preference transitions across options.
2. **Deterministic Curve Calculation**:
   - Computes preference shares at discrete sample steps along the continuum.

## Consequences

- Replaces static binary voting with rich parametric policy simulation.
- Uncovers the exact numeric consensus tipping points for decision-makers.
