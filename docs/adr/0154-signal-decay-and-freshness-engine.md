# ADR-0154: Signal Decay and Freshness Engine (CAP-075)

## Status

ACCEPTED

## Context

Consensus and community sentiment are not static. Ethical dilemmas and public priorities shift as real-world circumstances evolve. If an older consensus signal retains perpetual authority without ongoing deliberation, it misrepresents historical snapshots as active consensus.

## Decision

1. **Exponential Decay Algorithm**:
   - Freshness score is computed as $S(t) = e^{-\lambda t}$ where $t$ is the elapsed time since the latest verified weigh session and $\lambda = \frac{\ln(2)}{T_{1/2}}$ ($T_{1/2}$ is the domain-specific half-life, default 30 days).
2. **Standardized Freshness Tiers**:
   - `FRESH` ($S \ge 0.85$): Active, ongoing deliberation.
   - `STABLE` ($0.50 \le S < 0.85$): Established consensus with recent engagement.
   - `DECAYING` ($0.20 \le S < 0.50$): Waning activity, warning prompt for fresh deliberation.
   - `ARCHIVED` ($S < 0.20$): Historical record only; cannot serve as current Signal authority.
3. **Re-activation Invariant**:
   - Fresh incoming verified weighs automatically refresh $t$ and restore freshness score.

## Consequences

- Prevents obsolete consensus signals from exerting undue policy influence.
- Maintains dynamic, living deliberation authority.
