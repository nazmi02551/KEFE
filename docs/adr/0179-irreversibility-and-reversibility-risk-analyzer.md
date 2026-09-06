# ADR-0179: Irreversibility and Reversibility Risk Analyzer (CAP-021)

## Status

ACCEPTED

## Context

Decisions carrying permanent or irreversible consequences (such as species extinction, nuclear proliferation, or fundamental rights abolition) demand a higher evidentiary standard than readily reversible operational choices. In accordance with `KEFE-CQB-001` and `KEFE-PB-001`, the system implements a Precautionary Principle reversibility index.

## Decision

1. **Reversibility Taxonomy**:
   - `FULLY_REVERSIBLE`: Instant low-friction rollback.
   - `CONDITIONALLY_REVERSIBLE`: Reversible within 1-3 years with modest cost.
   - `SUBSTANTIALLY_IRREVERSIBLE`: High hysteresis and institutional entrenchment.
   - `PERMANENTLY_IRREVERSIBLE`: Irrevocable permanent consequence.
2. **Precautionary Burden Score**:
   - Computes risk factor ($[0.0, 1.0]$) where lower reversibility mandates explicit warning badges.

## Consequences

- Applies the Precautionary Principle to high-stakes civic decisions.
- Protects public well-being from catastrophic irreversible policies.
