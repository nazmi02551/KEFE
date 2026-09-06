# ADR-0220: Privacy Budget Consumption Monitor & Differential Telemetry (CAP-090)

## Status

ACCEPTED

## Context

Differential privacy guarantees mathematically bounded privacy loss across aggregate queries. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE provides a real-time Privacy Budget Consumption Monitor tracking global epsilon ($\epsilon$) and delta ($\delta$) depletion across analytical epochs with automated query throttling.

## Decision

1. **Budget Health State Taxonomy**:
   - `BUDGET_HEALTHY_AMPLE`: $\epsilon_{\text{spent}} \le 0.50 \cdot \epsilon_{\text{total}}$.
   - `BUDGET_APPROACHING_LIMIT`: $0.50 \cdot \epsilon_{\text{total}} < \epsilon_{\text{spent}} \le 0.85 \cdot \epsilon_{\text{total}}$.
   - `BUDGET_EXHAUSTED_THROTTLED`: Analytical query rate severely constrained to preserve anonymity.
2. **Mathematical Invariant**:
   - $\epsilon_{\text{total}} \le 1.00$ per 24h sliding window for public aggregate releases.

## Consequences

- Prevents reconstruction and linkage attacks on deliberation datasets.
- Guarantees provable mathematical privacy for all citizen participants.
