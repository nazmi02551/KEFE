# F4 Mobile Privacy Actor-Bound Delete — 2026-08-09

Status: IMPLEMENTED_CANDIDATE / EXACT_HEAD_CI_PENDING

Issue: #362  
Parent: PR #361 / `4f9d1a6357fc240cd8ce92a4c9f4a492279b8fcb`  
Capabilities: CAP-084, CAP-085, CAP-095  
ADR: ADR-0131  
Contract: `docs/contracts/mobile-privacy-actor-bound-deletion.v1.json`

## Finding

The canonical API requires destructive confirmation as:

`X-KEFE-Delete-Confirm: DELETE:<authenticated actor_id>`

The production mobile privacy repository previously sent only `DELETE`, while mobile secure credential persistence retained only the opaque bearer token. Because ADR-0004 deliberately makes the token opaque, the actor ID cannot safely be reconstructed from it.

This meant the user-facing mobile delete control could fail with the canonical server even for a valid authenticated user.

## Implemented candidate

- `CredentialStore` now retains actor ID separately from the opaque token;
- in-memory and secure stores clear token + actor ID together;
- guest issuance persists returned actor ID;
- restoring a credential returns the stored actor ID when available;
- guest→account merge replaces both account token and actor ID;
- mobile privacy delete sends exact `DELETE:<actor_id>` confirmation;
- legacy token-only installs may resolve actor ID once through the authenticated privacy export and persist it;
- deletion receipt must match the requested actor and confirm both private-data deletion and aggregate-contribution anonymization;
- credentials are cleared only after a valid receipt is parsed and accepted;
- mismatched/false receipt data fails closed and leaves local credentials intact;
- focused mobile repository tests cover guest issuance, account merge, exact header, legacy fallback and invalid-receipt handling;
- executable repository guard added to existing Mobile CI;
- no new GitHub Actions workflow.

## Security boundary

Actor ID remains **metadata, not authorization authority**. Protected server operations still derive the authenticated principal exclusively from the opaque bearer token.

The server-side comparison to `DELETE:<principal.actor_id>` is unchanged. No client-supplied actor ID can select another user's principal.

The legacy export fallback is authenticated and exists only to migrate older token-only installs to the actor-aware mobile credential model.

## Architecture scope

No changes to:

- server privacy API shape;
- privacy service confirmation requirement;
- OpenAPI;
- PostgreSQL schema/migrations;
- token format or token hashing;
- identity authorization semantics;
- Product Preview/production isolation;
- CAP lifecycle status.

## Verification state

GitHub Actions remains disabled at account level, therefore no exact-head PASS is claimed.

After Actions access is restored, existing Mobile CI must execute on the exact reviewed head and prove:

- actor-bound privacy deletion guard;
- Dart formatting;
- Flutter analyze;
- full mobile test suite including `mobile_privacy_actor_bound_delete_test.dart`;
- existing Context trust and RAW-result presentation guards;
- Connected Alpha compile-only boundary;
- Product Preview build boundary.

Until then this remains an implemented candidate.
