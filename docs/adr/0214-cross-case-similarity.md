# ADR-0214: Cross-Case Similarity & Comparative Matrix (CAP-101)

## Status

ACCEPTED

## Context

Citizens and policy analysts often benefit from comparing active dilemmas against topologically similar historical or international precedents. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE provides a Cross-Case Similarity & Comparative Matrix based on cosine similarity over ethical vector spaces, stakeholder tension profiles, and policy domains.

## Decision

1. **Similarity Domain Metric**:
   - $\text{CosineSim}(V_{case1}, V_{case2}) \in [0.0, 1.0]$.
2. **Alignment Tier Taxonomy**:
   - `HIGH_TOPOLOGICAL_ANALOGUE`: Near identical ethical tension and trade-off structure.
   - `PARTIAL_DOMAIN_OVERLAP`: Shared stakeholder tensions in distinct institutional settings.
   - `DISTANT_PRECEDENT`: Analogous abstract principle with divergent factual dynamics.

## Consequences

- Facilitates comparative precedent analysis.
- Connects disparate dilemmas through universal ethical structures.
