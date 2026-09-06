# ADR-0189: Versioned Decision Receipt Engine (CAP-012)

## Status

ACCEPTED

## Context

Under `KEFE-PB-001`, `KEFE-DGS-001`, and `KEFE-SEC-001`, users who deliberate and commit a verdict receive a cryptographically verifiable, timestamped, versioned Decision Receipt. This receipt durably proves their pre-result commitment without revealing private deliberations to unauthenticated third parties.

## Decision

1. **Receipt Cryptographic Payload**:
   - `receipt_id`: Unique identifier formatted as `kefe-rcpt-<hash>`.
   - `case_version_id`: Immutable case version pinned.
   - `committed_choice`: Sealed verdict chosen.
   - `integrity_digest`: SHA-256 hash of (case_id + user_pseudonym + choice + timestamp).
   - `timestamp_utc`: ISO-8601 UTC timestamp of commit.
2. **Verifiability**:
   - The user can export or present this receipt to verify participation in collective signal formation.

## Consequences

- Durable proof of deliberation integrity.
- Preserves zero-knowledge privacy.
