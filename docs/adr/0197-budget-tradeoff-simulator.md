# ADR-0197: Resource Allocation & Budget Tradeoff Simulator (CAP-027)

## Status

ACCEPTED

## Context

Many public policy and institutional dilemmas operate under a hard finite budget cap ($\sum c_i \le B$). Under `KEFE-PB-001`, `KEFE-ENG-001`, and `KEFE-ETG-001`, participants in KEFE Decide allocate finite point/currency envelopes across competing sectors (e.g. Healthcare, Education, Infrastructure, Green Transition).

## Decision

1. **Allocation Model**:
   - Total budget $B = 100$ points/percentage.
   - Dynamic validation enforcing $\sum_{i=1}^k c_i \le 100\%$.
2. **Tradeoff Profile**:
   - `HEALTH_EDUCATION_PRIORITY`: Human capital centric allocation.
   - `INFRASTRUCTURE_GROWTH`: Capital asset development priority.
   - `ECOLOGICAL_TRANSITION`: Decarbonization and conservation priority.
   - `DEFICIT_OVERFLOW`: Invalid allocation exceeding budget constraint.

## Consequences

- Direct confrontation with opportunity cost and real-world scarcity.
