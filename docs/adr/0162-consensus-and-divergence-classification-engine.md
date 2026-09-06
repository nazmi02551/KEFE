# ADR-0162: Consensus and Divergence Classification Engine (CAP-039)

## Status

ACCEPTED

## Context

Raw percentage splits (e.g. 52% vs 48%) do not convey the structural nature of collective sentiment. Citizens benefit from an objective, mathematical categorization that describes whether an outcome represents broad social consensus, sharp polarization, or fragmented plurality.

## Decision

1. **Deterministic Typology**:
   - `BROAD_CONSENSUS`: Top option $\ge 70.0\%$.
   - `BIPOLAR_DIVERGENCE`: Top two options within $15.0\%$ differential and sum $\ge 80.0\%$.
   - `FRAGMENTED_PLURALITY`: Top option $\le 45.0\%$ with support distributed across multiple options.
   - `LEANING_MAJORITY`: Top option between $55.0\%$ and $70.0\%$.
2. **Neutral Descriptive Labeling**:
   - Classifications are purely descriptive mathematical summaries. They carry no normative judgment (e.g. consensus is not labeled "good" and divergence is not labeled "bad").

## Consequences

- Delivers instant macro-clarity on collective deliberation structure.
- Adheres to non-normative reporting invariants.
