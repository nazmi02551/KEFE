# ADR-0225: Civic Petition & Legislative Impact Simulator (CAP-079)

## Status

ACCEPTED

## Context

Citizens and civil society organizations require a sandbox to draft citizen-sponsored legislative proposals and simulate their systemic economic, constitutional, and social consequences before gathering official ballot signatures. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE provides a Civic Petition & Legislative Impact Simulator.

## Decision

1. **Legislative Committee Stage Taxonomy**:
   - `DRAFT_IMPACT_SIMULATION`: Modeling economic, environmental, and rights impacts.
   - `SIGNATURE_GATHERING_CAMPAIGN`: Active citizen signature collection.
   - `SUBMITTED_TO_PARLIAMENT`: Official parliamentary hearing docketed.
2. **Simulation Invariant**:
   - Simulation models both positive utility gains and potential unintended negative externalities.

## Consequences

- Elevates raw petitions into well-structured, evidence-backed legislative drafts.
- Gives citizens direct insight into complex statutory trade-offs.
