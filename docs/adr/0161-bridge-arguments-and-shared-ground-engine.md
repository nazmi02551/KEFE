# ADR-0161: Bridge Arguments and Shared Ground Engine (CAP-034)

## Status

ACCEPTED

## Context

When ethical dilemmas create sharp polarization between opposing camps, citizens tend to perceive opponents as wholly incompatible. However, deep analysis of underlying justifications often reveals shared core values (e.g., child safety, procedural fairness, public health) interpreted through different trade-off lenses.

## Decision

1. **Bridge Argument Entity**:
   - A bridge argument represents a synthesis that resonates with significant cross-cutting portions of otherwise divergent voter groups.
   - Contains: `bridge_id`, `case_version_id`, `synthesis_thesis`, `connecting_values`, `cross_group_support_rate`, `provenance`.
2. **Strict Editorial Neutrality & Anti-Astroturfing**:
   - Bridge arguments require audited cross-distribution consensus metrics ($\ge 40\%$ concurrent resonance across opposing segments).
   - Platform algorithms never fabricate or force artificial compromises where fundamental rights differ.

## Consequences

- Fosters mutual understanding and de-escalation across entrenched divides.
- Surges shared-ground discovery while respecting deep principled differences.
