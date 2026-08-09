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

The same audit also found a credential-continuity split: DecisionRepository kept a process-local bearer cache in addition to secure storage. That cache could outlive guest→account replacement or privacy deletion until process restart.

## Implemented candidate

- `CredentialStore` now retains actor ID separately from the opaque token;
- persisted credential storage is the sole mobile bearer source of truth; DecisionRepository no longer keeps a parallel token cache;
- in-memory and secure stores clear token + actor ID together;
- guest issuance persists returned actor ID;
- restoring a credential returns the stored actor ID when available;
- guest→account merge replaces both account token and actor ID and is visible to subsequent requests without restart;
- clearing the credential store forces a fresh guest identity rather than reusing an in-memory deleted credential;
- mobile privacy delete sends exact `DELETE:<actor_id>` confirmation;
- legacy token-only installs may resolve actor ID once through the authenticated privacy export and persist it;
- deletion receipt must match the requested actor, confirm both private-data deletion and aggregate-contribution anonymization, and contain parseable required receipt metadata;
- credentials are cleared only after the complete receipt is accepted;
- mismatched, false-flag or malformed receipt data fails closed and leaves local credentials intact;
- focused mobile repository tests cover guest issuance, no-restart account replacement, post-clear fresh issuance, account merge, exact header, legacy fallback and invalid-receipt handling;
- executable repository guard added to existing Mobile CI;
- no new GitHub Actions workflow.

## Security boundary

Actor ID remains **metadata, not authorization authority**. Protected server operations still derive the authenticated principal exclusively from the opaque bearer token.

The server-side comparison to `DELETE:<principal.actor_id>` is unchanged. No client-supplied actor ID can select another user's principal.

The legacy export fallback is authenticated and exists only to migrate older token-only installs to the actor-aware mobile credential model.

Removing the parallel DecisionRepository bearer cache prevents stale credential reuse; it does not alter server authentication semantics.

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
