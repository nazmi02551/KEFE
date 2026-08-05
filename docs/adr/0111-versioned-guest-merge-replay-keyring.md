# ADR-0111: Versioned guest-merge replay keyring

- **Status:** Accepted
- **Date:** 2026-08-05
- **Foundation phase:** F4
- **Capability:** CAP-084
- **Issue:** #318
- **Parent decision:** ADR-0110

## Context

ADR-0110 reconstructs the exact account bearer for a completed guest-to-account conversion with a server-side HMAC secret. A single unversioned secret is safe while stable, but rotating it makes still-live completed conversions unreplayable. Persisting plaintext credentials is forbidden, and persisting another user-linked key-selection record would expand operational identity lineage without being necessary.

The client already retains and resubmits the high-entropy OTP verification token for the merge request. That token is stored only as a SHA-256 hash and its public contract is an opaque string.

## Decision

### Versioned verification-token envelope

New OTP verification tokens use:

`kefe_v2.<key-id>.<high-entropy-random-value>`

The key id is non-secret, validated as 1–64 ASCII alphanumeric/hyphen characters and is covered by the persisted hash of the complete token. Changing the key id changes the verification-token hash and cannot redirect an existing verification or replay record.

Legacy `kefe_v_...` tokens are mapped to the compatibility key id `primary-v1`. Their account credential continues to use the ADR-0110 v1 derivation byte-for-byte.

### Keyring

Runtime configuration contains:

- one active key id;
- one active HMAC secret;
- zero or more retained key-id/secret pairs.

The active key id is embedded in newly issued verification tokens. Retained keys are available only when a caller presents an older token that names them. They are never selected for new token issuance.

The service rejects malformed key ids, padded or short secrets, duplicate key ids, duplicate secret values and the known development secret anywhere in a production keyring.

### Versioned credential derivation

- Legacy tokens use the existing `kefe:guest-account-merge:v1` message exactly.
- Versioned tokens use `kefe:guest-account-merge:v2` and include the key id in the HMAC message.

Only the resulting account-token hash remains persisted in `identity.actor_session`. No secret, key id or plaintext account token is added to PostgreSQL.

### Replay and expiry behavior

For a completed replay, actor ownership is validated first. The persisted account-session expiry is then checked before key lookup.

- A still-live replay whose named key is unavailable fails closed with retryable `DEPENDENCY_TEMPORARILY_UNAVAILABLE`.
- An expired replay returns terminal `AUTH_TOKEN_EXPIRED` without requiring the retired key.
- An invalid or malformed verification token returns `AUTH_VERIFICATION_INVALID`.

The public guest-merge request and response schemas do not change.

### Two-phase rotation procedure

1. Deploy this keyring-capable runtime while the current key remains active; preload the future key as retained on every instance.
2. Switch the future key to active and retain the former active key on every instance.
3. Keep the old key for at least the maximum OTP-verification lifetime plus account-session replay lifetime, including deployment overlap and clock-skew margin.
4. Remove the old key after the retention window. Any later replay is already expired and does not require the retired key.

A production secret manager and deployed operator runbook remain external gates; repository CI proves configuration and behavioral boundaries, not secret-manager delivery or operator execution.

## Rejected alternatives

### Persist plaintext or encrypted replay credentials

Rejected because it creates a recoverable credential store and a new encryption-key lifecycle.

### Persist key ids in a new replay column

Rejected for this boundary because the client-supplied verification token already carries authenticated-by-hash operation identity. A new database field would duplicate key-selection lineage and require a migration without improving replay correctness.

### Try every configured key

Rejected because it makes key identity implicit, complicates retirement, and can hide configuration mistakes.

## Consequences

- Existing ADR-0110 replays remain compatible through `primary-v1`.
- New rotations can preserve exact replay across restarts without database schema changes.
- Key removal before the retention window causes an explicit fail-closed dependency error rather than issuance under the wrong key.
- CAP-084 remains `IMPLEMENTED_PARTIAL`; real OTP provider operation, deployed secret management, operator rotation evidence and broader merge-conflict policy remain pending.

## Verification

Dedicated memory and PostgreSQL evidence must prove:

- legacy v1 reconstruction;
- v2 token key-id issuance;
- exact replay after active-key rotation and restart;
- new conversions use the new active key;
- missing live key fails closed;
- expired replay does not require a retired key;
- production keyring validation;
- no plaintext secret or credential persistence;
- unchanged OpenAPI.