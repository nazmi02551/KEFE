# ADR-0087 — Public provider credential mode and permit-bound capture

Status: Accepted
Date: 2026-08-03

## Context

The provider admission runtime currently requires every capability to contain a secret reference. Public RSS/Atom-style sources do not require credentials, but they still require lifecycle, quota, circuit-breaker and permit enforcement. Using a fake secret reference would misrepresent the security boundary; bypassing admission would remove operational controls.

## Decision

1. Provider capabilities declare exactly one credential mode: `PUBLIC` or `SECRET_REF`.
2. `PUBLIC` capabilities must have `secret_ref = None`. `SECRET_REF` capabilities must carry an exact opaque allowed secret reference.
3. Existing persisted capabilities migrate to `SECRET_REF` without semantic change.
4. Admission, quota, lifecycle, circuit-breaker and permit completion remain shared across both modes.
5. Active permit execution context carries the exact credential mode. Secret material remains represented only as an opaque reference and is redacted.
6. The credentialed executor rejects `PUBLIC` contexts before resolver lookup.
7. A separate permit-bound public executor validates an active, unexpired permit for an enabled `PUBLIC` capability before invoking a public adapter.
8. Public adapters receive no secret, auth-header access, DNS resolver, TLS backend, evidence store or retry authority through this boundary.
9. Production composition registers zero public adapters.
10. Downgrade refuses to remove credential mode while any `PUBLIC` capability exists.

## Consequences

- Public sources can use the same provider governance without fake credentials.
- Credentialed and public execution cannot silently cross modes.
- RSS/Atom parsing and real endpoint adoption remain separate later decisions.
- The migration is additive and preserves all existing provider rows as `SECRET_REF`.

## Non-claims

This ADR does not introduce a real public provider, RSS/Atom parsing, live network access, production egress, durable storage deployment, provider legal approval, editorial automation or phone-facing behavior.
