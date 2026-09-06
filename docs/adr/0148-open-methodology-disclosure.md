# ADR-0148: Open Methodology Disclosure per Result and Signal (CAP-074)

## Status

ACCEPTED

## Context

Trust in collective deliberation and community signal depends entirely on methodological transparency. Users must have immediate, in-context access to the principles, sample metrics, confidence levels, and anti-distortion safeguards governing the numbers they see on screen.

## Decision

1. **In-Context Access**: Every collective result card and Signal surface provides an interactive methodology trigger opening a governed `OpenMethodologySheet`.
2. **Standardized Methodological Disclosures**:
   - Sample provenance and layer classification (`TRUSTED`, `RAW`, `DEGRADED`);
   - Sample size $n$ and confidence assessment;
   - Structural safeguards (Commit First, Pre-Result Isolation, Sybil & Brigading mitigation);
   - Non-psychometric invariant (no personality or ideological profiling).
3. **Locale Governance**: All methodological explanations are delivered through governed locale catalogs in Turkish and English.

## Consequences

- Direct compliance with the KEFE constitutional transparency layer.
- Establishes durable user trust without cluttering standard cards.
