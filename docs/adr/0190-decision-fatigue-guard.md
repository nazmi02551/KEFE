# ADR-0190: Decision Fatigue & Healthy Pacing Guard (CAP-014)

## Status

ACCEPTED

## Context

High-frequency moral weighing leads to ego depletion, cognitive fatigue, and superficial heuristic clicking ("doom-weighing"). Under `KEFE-PB-001`, `KEFE-DS-001`, and `KEFE-CQB-001`, the system implements a gentle, non-punitive Decision Fatigue Guard that tracks session duration, consecutive weighs, and recommends healthy pacing and reflection intervals.

## Decision

1. **Pacing States**:
   - `OPTIMAL_PACING`: Well-rested, high deliberation depth.
   - `PACING_RECOMMENDED`: 5+ consecutive complex dilemmas; gentle suggestion to reflect.
   - `REST_INTERVAL_ACTIVE`: High session volume; deliberation cool-down encouraged.
2. **Ethical Constraints**:
   - No hard lockout or punitive dark patterns.
   - Preserves user autonomy while promoting deliberate, mindful engagement.

## Consequences

- Promotes deep, thoughtful weighing over addictive engagement loops.
- Protects epistemic data quality.
