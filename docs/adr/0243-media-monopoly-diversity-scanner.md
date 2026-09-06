# ADR-0243: Media Monopoly & Source Diversity Scanner (CAP-111)

## Status

ACCEPTED

## Context

Democratic deliberation is vulnerable to media ownership concentration and narrative cartelization. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE introduces a Media Monopoly & Source Diversity Scanner to quantify corporate holding concentration, editorial independence, and ideological pluralism across news sources covering a dilemma.

## Decision

1. **Media Pluralism Level Taxonomy**:
   - `PLURALISTIC_INDEPENDENT_DIVERSE`: Balanced coverage from independent non-conglomerate news outlets.
   - `CORPORATE_CONGLOMERATE_CONCENTRATION`: Over 60% of narrative coverage owned by a single holding group.
   - `STATE_CONTROLLED_MONOPOLY_ALERT`: Monopolistic state or single-patron narrative dominance detected.
2. **Diversity Measurement Invariant**:
   - Analyzes Herfindahl-Hirschman Index (HHI) of parent ownership without indexing or censoring editorial content.

## Consequences

- Informs citizens about the ownership interests framing public dilemmas.
- Strengthens information ecosystem resilience against oligopolistic narrative monopolies.
