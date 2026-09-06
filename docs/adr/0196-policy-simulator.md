# ADR-0196: Policy Simulator & Parameter Tuning Engine (CAP-017)

## Status

ACCEPTED

## Context

Complex societal dilemmas involve adjustable policy knobs (e.g. tax rate $\tau \in [0, 50\%]$, subsidy level $s \in [0, 100\%]$, inspection frequency $f \in [1, 12]$ / year). Under `KEFE-PB-001`, `KEFE-ENG-001`, and `KEFE-ETG-001`, static binary choices fail to capture systemic tradeoffs. Policy Simulator allows users to adjust continuous policy parameters and observe projected outcome metrics before committing a weigh.

## Decision

1. **Knob & Metric Model**:
   - Discrete/continuous parameter knobs with baseline vs tuned values.
   - Outcome projections calculated dynamically across Fiscal, Social, and Environmental axes.
2. **Equilibrium State**:
   - `OPTIMAL_BALANCE`: Balanced trade-offs without severe negative externalities.
   - `HIGH_DEFICIT_RISK`: Excessive expenditure exceeding fiscal constraints.
   - `SEVERE_SOCIAL_IMPACT`: Excessive cost transferred to vulnerable stakeholders.
   - `ENVIRONMENTAL_DEGRADATION`: Insufficient green safeguards.

## Consequences

- Enhances user deliberation by revealing systemic interdependence.
- Replaces ideology with quantitative parameter exploration.
