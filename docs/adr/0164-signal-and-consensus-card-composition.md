# ADR-0164: Signal and Consensus Card Composition (CAP-016)

## Status

ACCEPTED

## Context

Once a civic deliberation meets strict sample size, agreement, and temporal stability criteria, it qualifies as an official KEFE Signal. To present this milestone to consumers and civic leaders in a clear, trustworthy format, the platform needs a specialized `SignalConsensusCard`.

## Decision

1. **Structured Signal Presentation**:
   - Displays: `signal_id`, `case_title`, `consensus_statement`, `agreement_percentage`, `sample_size`, `confidence_tier` (`GOLD`, `SILVER`, `BRONZE`), `certification_date`.
2. **Constitutional Guardrails**:
   - Signal cards display an official verification badge while explicitly noting that collective consensus represents deliberative agreement, not empirical truth or normative coercion.

## Consequences

- Provides a clean, authoritative card presentation for mature community consensus.
- Preserves platform neutrality and credibility.
