# ADR-0194: Impact Evidence & Artifact Verification (CAP-053)

## Status

ACCEPTED

## Context

To avoid superficial "greenwashing" or administrative PR claims, policy progress claimed by institutions must attach verifiable primary evidence artifacts (e.g. Official Gazette decree links, budget expenditure audit receipts, environmental sensor telemetry data). Under `KEFE-ADM-001`, `KEFE-ETG-001`, and `KEFE-PB-001`, Impact Evidence formalizes artifact attestation.

## Decision

1. **Evidence Media Types**:
   - `OFFICIAL_GAZETTE_DECREE`: Published legal statute or municipal order.
   - `AUDIT_EXPENDITURE_RECEIPT`: State Court of Accounts or independent financial audit.
   - `SENSOR_TELEMETRY_DATA`: Verified environmental/technical measurement data.
   - `THIRD_PARTY_ACADEMIC_STUDY`: Peer-reviewed impact assessment.
2. **Attestation Integrity**:
   - Every artifact includes immutable SHA-256 hash, URL provenance, and verification status.

## Consequences

- Grounded accountability based on objective records.
