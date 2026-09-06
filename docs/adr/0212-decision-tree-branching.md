# ADR-0212: Decision Tree & Scenario Branching Graph (CAP-099)

## Status

ACCEPTED

## Context

Citizens and policy makers must understand how intermediate choices propagate into downstream branching consequences. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE provides a structured Decision Tree & Scenario Branching Graph illustrating probabilistic decision forks, contingency paths, and cascading externalities.

## Decision

1. **Branch Node Taxonomy**:
   - `PRIMARY_DECISION_FORK`: Initial policy choice root.
   - `CONTINGENCY_BRANCH`: Downstream policy adjustment node.
   - `TERMINAL_OUTCOME_LEAF`: Final steady-state outcome scenario.
2. **Graph Consistency**:
   - Probabilities across child branches must sum to $1.00 \pm 0.01$.

## Consequences

- Visualizes cause-and-effect chains clearly.
- Prevents short-sighted policy choices by exposing second-order branches.
