# ADR-0201: Moderator Action Audit Log & Transparency (CAP-067)

## Status

ACCEPTED

## Context

Platform governance must avoid arbitrary, opaque, or politically motivated censorship. Under `KEFE-CQB-001`, `KEFE-ADM-001`, and `KEFE-SEC-001`, every administrative and moderation action (reason removal, flag dismissal, dispute resolution) must generate an immutable, cryptographically chained audit log entry accessible to public oversight.

## Decision

1. **Moderation Action Taxonomy**:
   - `REASON_REMOVED_POLICY_BREACH`: Hate speech, doxxing, or harassment removal.
   - `FLAG_DISMISSED_VALID`: False flag dismissed; content retained.
   - `CASE_VERSION_FREEZE`: Case locked for factual correction.
   - `USER_WARNING_ISSUED`: Formal warning regarding platform guidelines.
2. **Audit Invariant**:
   - Each entry contains moderator public key/ID, policy rule reference, justification text, and SHA-256 integrity hash.

## Consequences

- Absolute accountability for platform administrators.
- Prevents silent moderation abuse.
