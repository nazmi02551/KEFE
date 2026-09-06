# ADR-0160: Multi-Party Perspective Clustering Engine (CAP-033)

## Status

ACCEPTED

## Context

In high-volume public dilemmas, hundreds of diverse user reasons and viewpoints emerge. If presented as an uncurated stream, users experience information overload, and nuanced minority perspectives become drowned out.

## Decision

1. **Semantic Perspective Cluster**:
   - Groups reasoned arguments into distinct semantic archetypes (`NEAR_CONSENSUS`, `OPPOSING_PRINCIPLE`, `BRIDGE_SYNTHESIS`, `ALTERNATIVE_PARADIGM`).
2. **Deterministic Cluster Archetypes**:
   - Each cluster includes `cluster_id`, `archetype_name`, `core_thesis`, `sample_size`, and `support_percentage`.
3. **Neutral Balanced Presentation**:
   - When presenting deliberation clusters, UI displays archetypes in balanced representation without algorithmically favoring any single faction.

## Consequences

- Prevents argument saturation and echo-chamber dynamics.
- Empowers users to see the full semantic spectrum of public reasoning.
