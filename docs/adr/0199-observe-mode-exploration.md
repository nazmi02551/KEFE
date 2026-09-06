# ADR-0199: Observe Mode & Non-Binding Exploration (CAP-029)

## Status

ACCEPTED

## Context

Users occasionally encounter sensitive, specialized, or unfamiliar policy questions where they wish to explore arguments, evidence, and community perspectives without submitting a binding vote or registering a premature public stance. Under `KEFE-PB-001`, `KEFE-SEC-001`, and `KEFE-TIM-001`, Observe Mode ensures a completely isolated, non-contributing read-only experience.

## Decision

1. **Isolation Invariant**:
   - Zero contribution to collective signal tally ($w = 0$).
   - Access to arguments, evidence, and neutral context without modifying aggregation metrics.
2. **Exploration Mode State**:
   - `OBSERVE_ONLY`: Pure read-only inspection.
   - `STUDY_AND_LEARN`: Deep-dive with educational notes.
   - `TRANSITION_TO_WEIGH`: User explicitly elects to end observer mode and cast a binding weigh.

## Consequences

- Lowers barrier for curious or under-informed citizens.
- Guarantees zero pollution of democratic consensus tallies.
