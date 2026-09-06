# ADR-0155: Signal Verification Audit Trail (CAP-048)

## Status

ACCEPTED

## Context

When community deliberation reaches statistical and stability thresholds, it elevates to a verified KEFE Signal. Because Signals inform institutional decisions and public awareness, the transition from raw aggregate to verified Signal must be backed by an immutable, tamper-evident audit trail.

## Decision

1. **Append-Only Audit Log**:
   - Every state change in the Signal lifecycle (`THRESHOLD_CROSSED`, `EDITORIAL_CERTIFIED`, `METRIC_REFRESHED`, `AUTHORITY_REVOKED`) appends an immutable `SignalAuditEvent`.
2. **Cryptographic Chaining & Provenance**:
   - Each audit entry records an evidence snapshot, actor reference, UTC timestamp, and a SHA-256 integrity hash chained to the previous entry.
3. **Public Verifiability**:
   - Audit logs are accessible for external verification without disclosing private individual voter identities.

## Consequences

- Guarantees transparency and non-repudiation for all published Signals.
- Enforces strict institutional audit readiness.
