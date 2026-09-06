# ADR-0166: Stakeholder Impact Matrix Engine (CAP-023)

## Status

ACCEPTED

## Context

Complex civic dilemmas never affect all citizens equally. A policy that benefits the majority may impose severe disproportionate burdens on vulnerable minorities, municipal employees, or future generations. Without explicit stakeholder impact mapping, utilitarian majoritarianism can obscure structural injustices.

## Decision

1. **Multi-Stakeholder Impact Mapping**:
   - Evaluates each policy option across distinct stakeholder groups (`stakeholder_group`: e.g. `DIRECT_USERS`, `WORKERS`, `VULNERABLE_GROUPS`, `TAXPAYERS`, `FUTURE_GENERATIONS`).
   - Assesses impact nature (`BENEFIT`, `BURDEN`, `NEUTRAL`, `PROTECTION`) with a structured impact score (-5 to +5).
2. **Equity Balance Visualization**:
   - Highlights asymmetries where benefits accrue to one group while costs are shifted to another.

## Consequences

- Promotes empathetic, multi-stakeholder consideration (WE and IMPACT layers).
- Protects against invisible cost-shifting and disproportionate minority burden.
