# ADR-0237: Public Procurement & Resource Allocation Oversight Hive (CAP-105)

## Status

ACCEPTED

## Context

Municipal contracts and major public tenders frequently suffer from lack of civic oversight, leading to cost overruns and patronage. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE provides a Public Procurement Oversight Hive enabling crowdsourced civic auditing of government procurement awards and spending efficiency.

## Decision

1. **Procurement Integrity Level Taxonomy**:
   - `OPEN_COMPETITIVE_VERIFIED`: Multi-bidder open tender with transparent milestone delivery.
   - `ANOMALOUS_SOLE_SOURCE_REVIEW`: Non-competitive sole-source contract flagged for community audit.
   - `CRITICAL_OVERRUN_ALERT`: Significant budgetary divergence exceeding 25% tolerance.
2. **Civic Audit Invariant**:
   - Every procurement record links directly to verifiable municipal financial ledgers and milestone artifacts.

## Consequences

- Prevents municipal corruption through distributed crowdsourced civic vigilance.
- Protects public funds and optimizes municipal capital allocation.
