# ADR-0236: Conflict-of-Interest & Lobbying Transparency Radar (CAP-104)

## Status

ACCEPTED

## Context

When powerful special interest groups, corporations, or lobbyists inject arguments into public deliberations, hidden financial ties can corrupt civic discourse. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE provides an automated Conflict-of-Interest & Lobbying Transparency Radar cross-referencing public registries, campaign contributions, and organizational benefactors.

## Decision

1. **Lobbying Exposure Level Taxonomy**:
   - `CLEAN_INDEPENDENT_DISCLOSURE`: Full disclosure with zero identified commercial ties.
   - `DECLARED_STAKEHOLDER_FINANCING`: Self-declared funding ties and sector affiliation.
   - `HIGH_CONFLICT_EXPOSURE_ALERT`: Material undisclosed commercial lobbying influence detected.
2. **Attribution Invariant**:
   - Funding sources and commercial affiliations must be transparently rendered alongside institutional perspective claims.

## Consequences

- Exposes Astroturfed commercial advocacy while protecting authentic grassroots advocacy.
- Elevates civic trust through rigorous open financial transparency.
