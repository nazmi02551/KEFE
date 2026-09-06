# ADR-0213: Temporal Flow & Animated Opinion Migration (CAP-100)

## Status

ACCEPTED

## Context

Public sentiment is not static; it evolves dynamically as new evidence, bridge arguments, or external real-world events unfold. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE provides a Temporal Opinion Flow engine that tracks collective aggregate shifts between dilemma alternatives over discrete chronological epochs without tracking individual trajectories.

## Decision

1. **Migration Epoch Taxonomy**:
   - `INITIAL_BLIND_RESONANCE`: Baseline pre-deliberation distribution.
   - `MID_DELIBERATION_SHIFT`: Opinion flow during evidence inspection.
   - `MATURED_CONSENSUS_STATE`: Stabilized distribution following bridge synthesis.
2. **Privacy Invariant**:
   - Flows represent bulk population percentages only ($N \ge 100$). No individual movement tracing.

## Consequences

- Reveals the temporal velocity of collective opinion shifts.
- Shows how constructive arguments precipitate macro-level consensus.
