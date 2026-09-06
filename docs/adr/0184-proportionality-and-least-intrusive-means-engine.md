# ADR-0184: Proportionality and Least Intrusive Means Engine (CAP-025)

## Status

ACCEPTED

## Context

A fundamental rule of modern democratic constitutionalism (ECHR, German Federal Constitutional Court, and Turkish Constitutional Court jurisprudence) is that state or collective restrictions on rights must pass the tripartite proportionality test (*Elverişlilik, Gereklilik, Orantılılık*). Under `KEFE-CQB-001` (Content & Question Design Bible) and `KEFE-PB-001` (Product Bible), the platform applies this three-prong test to policy options.

## Decision

1. **Three Prongs of Proportionality**:
   - `suitability_score` ($[0.0, 1.0]$): Efficacy toward the stated legitimate goal.
   - `necessity_least_intrusive_score` ($[0.0, 1.0]$): Absence of less intrusive alternative means.
   - `strict_proportionality_score` ($[0.0, 1.0]$): Balance between public gain and individual burden.
2. **Composite Classification**:
   - `PROPORTIONAL_VALID` (Composite $\ge 0.70$).
   - `EXCESSIVELY_BURDENSOME` ($0.40 \le$ Composite $< 0.70$).
   - `DISPROPORTIONATE_INVALID` (Composite $< 0.40$).

## Consequences

- Grounded in canonical constitutional proportionality jurisprudence.
- Prevents disproportionate authoritarian overreach.
