# ADR-0217: Session & Active Device Security Hub (CAP-087)

## Status

ACCEPTED

## Context

Users must have granular, transparent control over all active login tokens, paired devices, and authorization sessions. Under `KEFE-PB-001`, `KEFE-ETG-001`, and `KEFE-ENG-001`, KEFE provides a Session & Device Security Hub enabling instant remote revocation, hardware attestation verification, and session trust scoring.

## Decision

1. **Device Trust Tier Taxonomy**:
   - `HARDWARE_ATTESTED_SECURE`: Hardware keystore / Secure Enclave verified.
   - `STANDARD_AUTHENTICATED`: Software-backed authenticated session.
   - `UNRECOGNIZED_STALE`: Dormant or unverified session pending challenge.
2. **Revocation Invariant**:
   - Remote revocation invalidates all issued JWT tokens within $\le 500\text{ ms}$.

## Consequences

- Grants users total sovereignty over their account sessions.
- Detects unauthorized access or session hijacking immediately.
