# ADR-0158: Offline-First Secure Draft Queue (CAP-078)

## Status

ACCEPTED

## Context

Mobile users often deliberate while in intermittent connectivity (e.g. transit, rural areas). If network failure causes an in-progress weigh decision or carefully articulated reason to be lost upon submission, trust is broken.

## Decision

1. **Local Resilient Draft Queue**:
   - When network requests fail or connectivity is offline, the decision attempt is captured as an immutable `QueuedDecisionSubmission` in local storage.
2. **Idempotency & Non-Loss Guarantee**:
   - Each submission carries a deterministic client-generated `idempotency_key`.
   - The queue executes exponential-backoff retry upon network reconnection.
   - Idempotent API replay semantics (`IDEMPOTENT_REPLAY`) ensure no duplicate records or corrupted sequences.
3. **Privacy Invariant**:
   - Queued drafts remain stored only within private app sandbox storage.

## Consequences

- Deliberation is never lost due to transient network drops.
- Provides seamless offline-to-online reconciliation.
