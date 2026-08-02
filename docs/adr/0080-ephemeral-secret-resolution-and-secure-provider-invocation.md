# ADR-0080: Ephemeral Secret Resolution and Secure Provider Invocation

- Status: Accepted
- Date: 2026-08-02
- Amended: 2026-08-03 by ADR-0087
- Issue: #213
- Parent: PR #212 / ADR-0079

## Context

Slice 43 authorizes provider capture attempts through an exact immutable capability, quota, circuit and durable permit. Credentialed capabilities store only an opaque secret reference and do not resolve a credential or invoke a credential-aware adapter. Public capabilities, introduced by ADR-0087, carry no secret reference and must use a separate execution path.

A credential-aware adapter must eventually receive secret material, but returning a string from a resolver or adding the value to provider-neutral commands would create long-lived copies and leak paths through repr, logs, exceptions, results and persistence.

## Decision

Introduce a separate credentialed execution boundary with these invariants:

1. An exact active, unexpired permit is required before a secret reference can be obtained.
2. The trusted permit-context port returns the exact credential mode and the opaque secret reference only to the trusted execution boundary.
3. `SecureProviderCaptureExecutor` accepts only `SECRET_REF` context. It rejects `PUBLIC` before resolver-registry lookup.
4. Resolver selection is exact by URI scheme; no fallback or provider-name inference is allowed.
5. Resolution creates an in-memory `SecretLease` with bounded expiry.
6. Secret bytes are accessed only through `use_bytes(callback)` while the lease is active.
7. The lease has redacted repr, is not serializable/hashable/comparable, and zeroizes its bytearray on close.
8. The secure executor closes the lease in `finally`, including adapter and callback failures.
9. Credential-aware adapters are selected by exact immutable `adapter_code`.
10. Resolution and invocation errors expose bounded codes only; credential mode, secret values and references never enter operational output.
11. Production composition starts with empty resolver and credential-aware adapter registries and reaches this executor only through the credential-mode router.
12. Source Acquisition keeps permit completion before artifact persistence or failure return.

## Consequences

- A credentialed provider adapter cannot run merely because a capability or adapter implementation exists.
- A public permit can never enter secret resolution, even if routing is misconfigured.
- Secret material remains process-local and short-lived.
- A later provider slice may add a concrete resolver/adapter explicitly without changing provider-neutral acquisition metadata.
- This slice does not prove provider terms, credential rotation, secret-manager availability, deployment, SLOs or rollback readiness.

## Rejected alternatives

- Returning credential strings from a resolver.
- Persisting decrypted credentials or resolved leases.
- Passing secret values through `SourceAcquisitionCommand` or `CapturedSource`.
- Resolving a fake secret for public providers.
- Selecting resolvers/adapters by provider-name branching.
- Enabling environment or secret-manager resolution by default.
