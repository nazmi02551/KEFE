# ADR-0131 — Mobile privacy deletion preserves actor-bound confirmation

Status: CANDIDATE  
Date: 2026-08-09  
Issue: #362  
Capabilities: CAP-084, CAP-085, CAP-095  
Foundation wave: F4

## Context

The canonical privacy service deliberately requires `X-KEFE-Delete-Confirm: DELETE:<authenticated actor_id>`. The authenticated principal still comes exclusively from the opaque bearer credential.

The mobile privacy repository previously sent plain `DELETE`, while the secure credential store persisted only the bearer token. Guest issuance and guest-to-account merge both return `actor_id`, but mobile persistence discarded it.

A related continuity issue existed after account conversion or deletion: `HttpDecisionRepository` also cached the bearer token in process memory. A guest token could therefore outlive an account merge, or a deleted/revoked credential could outlive secure-store clearing until process restart.

ADR-0004 makes bearer tokens opaque, so mobile must not decode or infer actor identity from the token.

## Decision

1. Keep the server actor-bound deletion requirement unchanged.
2. Keep bearer tokens opaque and authoritative only through server authentication.
3. Extend mobile credential persistence with a separate actor-id field while retaining existing token read/write methods for compatibility.
4. Persist actor ID when a guest credential is issued.
5. Replace actor ID when guest-to-account merge returns a new account credential.
6. Make persisted credential storage the sole mobile bearer source of truth; `HttpDecisionRepository` must not retain a parallel in-memory bearer cache.
7. Clear token and actor ID together.
8. Before deletion, mobile resolves the stored actor ID. For legacy installs that have an existing token but no actor ID, it may use the authenticated privacy export's `actor_id` once as a compatibility migration source.
9. Mobile sends exact `DELETE:<actor_id>`.
10. Mobile treats a deletion response as success only when the returned actor ID matches, both `private_data_deleted` and `aggregate_contributions_anonymized` are true, and required receipt metadata parses correctly.
11. Credentials are cleared only after complete receipt validation succeeds.

## Security reasoning

Persisted actor ID is metadata, not authorization authority. A forged actor ID cannot select another principal because the server derives the principal from the bearer token and compares the destructive confirmation to that authenticated principal.

The legacy export fallback does not weaken this boundary: the export itself is authenticated and its actor ID is used only to construct the confirmation string expected by the same authenticated principal.

Using one persisted bearer source of truth prevents post-merge/post-delete split-brain state. It does not change server authorization; it only removes a stale client-side copy of a credential that the authoritative store has already replaced or cleared.

## Consequences

- Existing token-only installs remain compatible without a new server endpoint.
- New guest/account credentials retain the actor identity required for destructive confirmation.
- Completed guest→account conversion is visible to subsequent decision requests without process restart.
- Successful privacy deletion cannot leave a reusable in-memory bearer credential behind.
- Invalid, mismatched or malformed deletion receipts fail closed and do not erase local credentials.
- No server API, OpenAPI, database or migration change is required.
- No bearer-token decoding is introduced.

## Verification

Focused tests and an executable guard must prove guest persistence, persisted-account replacement without restart, no DecisionRepository bearer cache, legacy fallback, exact actor-bound header, complete receipt validation, post-success credential clearing and no new workflow.

Exact-head Mobile CI is required before PASS can be claimed.
