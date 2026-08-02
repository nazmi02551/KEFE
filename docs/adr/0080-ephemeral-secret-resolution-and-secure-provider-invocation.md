# ADR-0080: Ephemeral Secret Resolution and Secure Provider Invocation

- Status: Accepted
- Date: 2026-08-02
- Issue: #213
- Parent: PR #212 / ADR-0079

## Context

Slice 43 authorizes provider capture attempts through an exact immutable capability, quota, circuit and durable permit. It intentionally stores only an opaque secret reference and does not resolve a credential or invoke a credential-aware adapter.

A real adapter must eventually receive secret material, but returning a string from a resolver or adding the value to provider-neutral commands would create long-lived copies and leak paths through repr, logs, exceptions, results and persistence.

## Decision

Introduce a separate execution boundary with these invariants:

1. An exact active, unexpired permit is required before a secret reference can be obtained.
2. The trusted permit-context port returns the existing opaque secret reference only to the secure executor.
3. Resolver selection is exact by URI scheme; no fallback or provider-name inference is allowed.
4. Resolution creates an in-memory `SecretLease` with bounded expiry.
5. Secret bytes are accessed only through `use_bytes(callback)` while the lease is active.
6. The lease has redacted repr, is not serializable/hashable/comparable, and zeroizes its bytearray on close.
7. The secure executor closes the lease in `finally`, including adapter and callback failures.
8. Credential-aware adapters are selected by exact immutable `adapter_code`.
9. Resolution and invocation errors expose bounded codes only; secret values and references never enter exception text or operational output.
10. Production composition starts with empty resolver and credential-aware adapter registries.
11. Source Acquisition keeps permit completion before artifact persistence or failure return.

## Consequences

- A provider adapter cannot run merely because a capability or adapter implementation exists.
- Secret material remains process-local and short-lived.
- A later provider slice may add a concrete resolver/adapter explicitly without changing provider-neutral acquisition metadata.
- This slice does not prove provider terms, credential rotation, secret-manager availability, deployment, SLOs or rollback readiness.

## Rejected alternatives

- Returning credential strings from a resolver.
- Persisting decrypted credentials or resolved leases.
- Passing secret values through `SourceAcquisitionCommand` or `CapturedSource`.
- Selecting resolvers/adapters by provider-name branching.
- Enabling environment or secret-manager resolution by default.
