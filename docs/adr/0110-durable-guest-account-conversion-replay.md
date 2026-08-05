# ADR-0110: Durable guest-account conversion replay

- **Status:** Accepted
- **Date:** 2026-08-05
- **Foundation phase:** F4
- **Capability:** CAP-084
- **Issue:** #316
- **Parent decision:** ADR-0109

## Context

ADR-0109 made account conversion a credential-rotation boundary. That closes session fixation, but it also means a client cannot authenticate a retry with the source guest bearer after the first conversion succeeds.

The existing conversion performs verification consumption, actor promotion/merge and account-session creation through separate repository calls. If the response is lost after any committed side effect, the same request cannot deterministically recover its account credential. Persisting the plaintext account token would create an unacceptable credential store.

## Decision

### Natural replay identity

The SHA-256 hash of the high-entropy OTP verification token is the operation's natural replay key. No separate generic idempotency subsystem or public `Idempotency-Key` field is introduced.

### Deterministic credential

The account bearer is derived using HMAC-SHA-256 over a versioned, domain-separated message containing:

- the verification-token hash;
- the source actor id;
- the account-session expiry instant.

The HMAC key is supplied through `KEFE_ACCOUNT_MERGE_REPLAY_SECRET`. Only the bearer hash is persisted in `identity.actor_session`; the plaintext bearer is reconstructed for an exact replay and is never stored.

### Atomic persistence

In PostgreSQL, one transaction must:

1. detect and validate an existing completed replay;
2. otherwise consume the verification token;
3. promote or merge the source guest actor;
4. revoke every source guest session;
5. create exactly one account session;
6. persist the completed replay metadata.

A failed transaction leaves the verification token and actor state unchanged. Concurrent requests using the same verification token converge through the locked verification row and completed replay record.

### Authorization after credential rotation

The normal authentication path continues to reject revoked bearers. The guest-merge endpoint uses a narrow resolution path that may identify the principal behind a revoked bearer. A revoked bearer is accepted only when a completed replay exists for the same source actor and verification token. It cannot initiate a new conversion.

### Conflict behavior

- Same verification token + same source actor: replay the exact credential result.
- Same verification token + different source actor: `AUTH_MERGE_REPLAY_MISMATCH`.
- Revoked bearer without a matching completed replay: `AUTH_TOKEN_REVOKED`.
- Invalid or expired verification token without a replay: `AUTH_VERIFICATION_INVALID`.

### Privacy lifecycle

Replay metadata is operational credential lineage, not user-visible product history. Account deletion removes replay records linked to the source or destination actor before deleting OTP verification material and account identifiers.

## Consequences

- The public request and response schema remain unchanged.
- Exact retries can recover the same credential after response loss or application restart.
- Production account conversion requires a stable, secret-managed HMAC key; the repository does not claim production readiness until that external deployment gate is evidenced.
- Rotation of the HMAC key invalidates reconstruction of previously replayable responses. Key rotation therefore requires an explicit replay-retention/rotation procedure before production activation.

## Verification

The executable contract and dedicated CI must prove:

- no plaintext bearer persistence;
- deterministic replay equality;
- one account session under concurrency;
- restart-safe PostgreSQL replay;
- actor-mismatch rejection;
- revoked-without-replay rejection;
- privacy cleanup;
- unchanged OpenAPI.