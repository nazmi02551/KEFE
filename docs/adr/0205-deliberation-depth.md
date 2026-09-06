# ADR-0205: Deliberation Depth & Reflection Score (CAP-118)

## Status

ACCEPTED

## Context

In addition to participation counts, democratic health requires measuring the intellectual rigor and reflection depth invested by citizens in weighing complex dilemmas. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, the Deliberation Depth engine evaluates multi-perspective engagement, counter-argument exploration, and evidence inspection density.

## Decision

1. **Depth Formulation**:
   - $\text{DepthScore} = 0.40 \times \text{ArgumentDensity} + 0.35 \times \text{EvidenceInspected} + 0.25 \times \text{CounterPerspectiveRatio}$.
2. **Depth Level Taxonomy**:
   - `PROFOUND_DELIBERATION`: Holistic exploration of trade-offs, evidence, and counter-views.
   - `STRUCTURED_REFLECTION`: Methodical inspection of primary perspectives.
   - `SUPERFICIAL_SKIMMING`: Rapid, low-engagement decision casting.

## Consequences

- Distinguishes considered judgment from unreflective click-activism.
- Informs community quality metrics without penalizing brief sessions.
