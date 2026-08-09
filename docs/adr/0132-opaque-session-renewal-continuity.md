# ADR-0132 — Opaque session renewal preserves guest/account continuity

Status: ARCHITECTURE CANDIDATE  
Date: 2026-08-09  
Issue: #364  
Capabilities: CAP-084, CAP-085, CAP-095  
Foundation wave: F4

## Context

KEFE currently issues opaque access credentials with a default 30-day TTL for both guest and account actors. Authentication explicitly distinguishes expired, revoked and invalid tokens, but there is no renewal credential or renewal endpoint.

This conflicts with two accepted continuity principles:

- ADR-0012 keeps guest use non-blocking and makes progress actor-owned;
- ADR-0004 keeps credentials opaque and revocable.

When a guest access token expires today, issuing a new guest token would create a different actor and would not restore access to the previous actor-owned progress. For account actors, silently falling back to a guest would similarly violate account continuity.

The mobile client also does not retain the exact server access expiry or actor kind, so it cannot model the lifecycle accurately.

## Decision

### 1. Introduce one session family per actor session

`identity.actor_session.id` remains the session-family identifier. A session family belongs to exactly one actor. Renewal can produce new credentials only for that same actor; actor ID is never supplied as a client-side selection parameter.

A revoked session, retired actor or privacy-deleted actor cannot renew.

### 2. Separate access and renewal authority

An access token remains an opaque bearer credential for protected API access.

A separate opaque renewal token exists only to renew the same session family. It is not accepted as a bearer credential for normal APIs. The server stores only token hashes and derivation metadata; plaintext access/renewal secrets are never persisted.

### 3. Deterministic token derivation for retry safety

New token pairs are derived with HMAC-SHA256 from a dedicated session-token keyring and the tuple:

`purpose-domain + session-family-id + actor-id + rotation-counter`

Access and renewal use distinct purpose domains.

The database stores the active derivation key id and monotonic rotation counter. This lets the server reproduce the current token pair from non-secret session metadata plus the external secret key, without persisting plaintext credentials.

The session-renewal keyring is separate from account-merge replay keys and all other cryptographic domains.

### 4. Rotate with bounded previous-pair retry

A successful renewal atomically:

1. locks the session row;
2. verifies active actor/session state;
3. promotes the current access and renewal hashes to previous-hash slots;
4. marks the previous pair retryable for 60 seconds;
5. increments the rotation counter;
6. optionally advances to the active derivation key id;
7. derives/stores the new hashes and access expiry;
8. returns the new pair.

If the same previous renewal token is retried within the 60-second response-loss window, the server returns the already-current pair and **does not rotate again**. This handles a lost HTTP response and converges concurrent same-token renewal requests without storing plaintext responses.

An older token or a previous token outside the grace period is rejected. Rejection must not create a new actor.

The short previous access-token grace allows in-flight requests to finish during rotation.

### 5. Provide two API entry points

`POST /v1/identity/session/renew`

- does not require a still-valid access bearer;
- accepts only the opaque renewal token;
- does not accept actor ID;
- returns actor ID/kind, access token/expiry, rotated renewal token and rotation counter.

`POST /v1/identity/session/continuity/bootstrap`

- requires a currently active access bearer;
- upgrades a legacy access-only session to the renewal model before that access token expires;
- is migration compatibility, not an alternate authentication method.

New guest issuance and guest→account conversion return the renewal bundle directly.

### 6. Mobile stores one atomic credential bundle

Mobile secure storage moves from multiple loosely coordinated fields to one versioned credential bundle containing:

- actor id;
- actor kind;
- access token;
- exact access expiry returned by server;
- renewal token;
- rotation counter.

No expiry is synthesized locally and no token is decoded.

The client renews proactively shortly before access expiry and may renew after an `AUTH_TOKEN_EXPIRED` response. Renewal is single-flight so concurrent API calls do not race multiple rotations.

Renewal failure never silently issues a different guest actor. Account renewal failure enters explicit reauthentication. Guest renewal failure enters a continuity error state rather than orphaning progress behind a new actor.

### 7. Guest→account conversion retires guest continuation authority

The existing merge transaction already revokes guest actor sessions. Renewal metadata remains in the same session rows, so revoking those rows retires guest access and renewal together.

The newly created account session receives its own session-family token pair. A merge replay may reproduce the initial account pair from stored session/replay identity plus derivation metadata; it must not silently expose a later rotated renewal pair.

### 8. Privacy deletion revokes continuation authority

Privacy deletion must leave no access or renewal path to the deleted actor. Renewal secrets are never included in privacy export or deletion receipts.

## Why not silently create a new guest on expiry?

A new guest is a new actor. It would make the app appear recovered while severing access to the prior guest's actor-owned history. That is a data-continuity bug disguised as resilience.

A user may explicitly start over after an unrecoverable continuity failure, but the client must present that as a separate destructive/identity decision rather than automatic error recovery.

## Why deterministic HMAC derivation?

Simple one-time refresh-token rotation has a response-loss trap: the server may rotate successfully while the client never receives the new token. Retrying the old token would then fail and strand the session.

Persisting plaintext new tokens to solve that would increase secret exposure. Deterministic derivation plus a bounded previous-token retry window allows the same current pair to be reproduced without plaintext persistence.

## Security properties

- bearer and renewal secrets remain opaque;
- database-only compromise cannot derive plaintext tokens;
- client cannot select actor identity during renewal;
- renewal cannot cross actor/session family;
- revoked/deleted sessions cannot renew;
- old-token replay is bounded and rejected outside a narrow response-loss window;
- no credential is placed in URL/query/log/privacy export;
- token-derivation secrets are isolated in a dedicated keyring.

## Implementation sequence

This ADR intentionally separates architecture lock from runtime implementation:

1. canonical migration extends `identity.actor_session`;
2. domain/ports + in-memory renewal behavior;
3. PostgreSQL transactional renewal and concurrency tests;
4. guest issuance + account merge renewal bundle;
5. renew/bootstrap API contracts and OpenAPI;
6. atomic mobile credential bundle + legacy migration;
7. single-flight mobile renewal/retry behavior;
8. privacy/merge revocation regression coverage;
9. exact-head core API CI + Mobile CI;
10. real Connected Alpha expiry/renewal proof before capability promotion.

No dedicated GitHub Actions workflow is introduced.

## Non-goals

This ADR does not add social login, passwords, cross-device session management or a specific external auth provider. It does not claim production auth operability or promote CAP-084/F4 lifecycle status.
