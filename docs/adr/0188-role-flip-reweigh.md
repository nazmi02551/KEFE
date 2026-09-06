# ADR-0188: Role Flip & Stakeholder Position Reweigh (CAP-007)

## Status

ACCEPTED

## Context

Cognitive empathy and perspective-taking are central to moral maturation. Under `KEFE-CQB-001`, `KEFE-PB-001`, and `KEFE-DGS-001`, the system provides Role Flip flows where the user is asked to occupy the exact shoes and vulnerability of the opposite stakeholder and re-weigh the dilemma.

## Decision

1. **Role Flip Architecture**:
   - `initial_role`: User's default or chosen perspective.
   - `flipped_role`: Inverse stakeholder bearing the burden or cost of the policy.
   - `empathy_delta`: Measure of perspective shift or deepened nuance after experiencing the flipped position.
2. **Strict Invariants**:
   - Role flip is an educational perspective exercise, not a psychological diagnosis.
   - Non-judgmental language describing shifts in empathy.

## Consequences

- Enhances moral imagination without forcing artificial consensus.
