# F4 Guest Merge Replay Key Rotation — 2026-08-05

## Scope

- Foundation wave: F4 — Consumer identity, privacy, reachability and production readiness
- Capability: CAP-084 — Guest-to-account conversion and data merge
- Issue: #318
- Parent runtime: PR #317 / `2e443eab972a15f88aed332b7cc58bc1bafac421`
- Branch: `feature/f4-guest-merge-key-rotation`

## Bounded advancement

This slice removes the single-secret rotation blocker from durable guest-account conversion replay without changing the public API or adding credential material to PostgreSQL.

Implemented boundary:

- legacy `kefe_v_...` verification tokens map to compatibility key `primary-v1` and retain the ADR-0110 v1 HMAC derivation;
- new verification tokens use `kefe_v2.<key-id>.<random>`;
- one configured active key issues new verification tokens and credentials;
- retained keys are read-only and reconstruct still-live older exact replays;
- actor ownership and replay expiry are checked before key lookup;
- missing key for a live replay fails closed with retryable dependency unavailability;
- expired replay is terminal and does not require a retired key;
- production keyrings reject malformed ids, weak or duplicated secrets and the repository development secret;
- the existing `identity.guest_merge_replay` table remains unchanged and stores no key id, secret or plaintext credential.

## Rotation procedure

1. Deploy keyring-capable runtime with the current key active and the future key retained on every instance.
2. Switch the future key to active while retaining the previous active key.
3. Retain the previous key through the maximum verification-token plus account-session replay window, deployment overlap and clock-skew margin.
4. Remove the previous key only after that window; expired replay no longer needs it.

## Contract evidence

- ADR-0111: `docs/adr/0111-versioned-guest-merge-replay-keyring.md`
- Contract: `docs/contracts/guest-account-merge-key-rotation.v1.json`
- Executable checker: `services/api/tools/check_guest_account_merge_key_rotation_contract.py`
- Memory proof: `services/api/tests/test_guest_merge_key_rotation.py`
- PostgreSQL proof: `services/api/tests/test_guest_merge_key_rotation_postgres.py`
- Dedicated workflow: `.github/workflows/guest-merge-key-rotation.yml`

## Evidence required before review-ready

The same exact head must pass:

- Guest Merge Key Rotation CI, memory and PostgreSQL jobs;
- Guest Merge Replay CI;
- Guest Session Rotation CI;
- Privacy Self Service CI;
- API CI;
- MVP Beta Gates;
- Global Readiness;
- all other workflows triggered by the exact head.

## Explicit non-claims and remaining CAP-084 gates

This slice does not prove:

- production secret-manager delivery or access policy;
- human/operator execution of rotation or rollback;
- real email/SMS OTP provider deliverability;
- deployed identity SLO, load, alerting or incident response;
- broader duplicate ownership and future product-data merge conflict policies.

CAP-084 remains `IMPLEMENTED_PARTIAL` until those relevant product and external gates are closed.