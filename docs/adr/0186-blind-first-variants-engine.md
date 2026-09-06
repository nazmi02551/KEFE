# ADR-0186: Blind-First Variants Engine (CAP-005)

## Status

ACCEPTED

## Context

Tribal affinity and partisan bias frequently distort moral judgment when the political identity of the actor or victim is known. Under `KEFE-CQB-001` (Content & Question Design Bible), `KEFE-MPD-001`, and `KEFE-PB-001`, the system implements Blind-First Variants where identifying attributes are systematically abstracted.

## Decision

1. **Blind Mode Taxonomy**:
   - `ACTOR_BLIND`: Mask specific politician/party/nation identity with generic structural roles.
   - `SOURCE_BLIND`: Mask media outlet or publisher branding to focus purely on argument content.
   - `OUTCOME_BLIND`: Mask retrospective historical outcomes to test pure ethical principle at the moment of choice.
2. **Reveal Protocol**:
   - The user commits their verdict under the blinded condition before the explicit real-world identity is revealed.

## Consequences

- Eliminates tribal identity heuristics.
- Preserves epistemic integrity and Rawlsian veil-of-ignorance reasoning.
