# ADR-0191: Signal Half-Life & Freshness Lifecycle Engine (CAP-045)

## Status

ACCEPTED

## Context

Societal consensus and moral signals decay over time as demographic, legal, and environmental contexts shift. Under `KEFE-TIM-001` (Trust & Integrity Bible), `KEFE-RM-001`, and `KEFE-PB-001`, a collective signal must never be treated as permanently valid truth authority. The system formalizes explicit Signal Half-Life ($T_{1/2}$) and time-decay weighting.

## Decision

1. **Decay Model**:
   - Exponential time-decay function: $W(t) = e^{-\lambda \Delta t}$ where $\lambda = \frac{\ln(2)}{T_{1/2}}$.
   - Configurable half-life per domain (e.g. Fast Tech Policy $T_{1/2} = 90$ days; Fundamental Constitutional Dilemmas $T_{1/2} = 365$ days).
2. **Freshness Taxonomy**:
   - `FRESH`: $W(t) \ge 0.85$
   - `STABLE`: $0.50 \le W(t) < 0.85$
   - `DEPRECATING`: $0.20 \le W(t) < 0.50$
   - `EXPIRED_NEEDS_RETEST`: $W(t) < 0.20$

## Consequences

- Prevents obsolete sentiment from masquerading as current consensus.
- Triggers automatic community re-test cycles.
