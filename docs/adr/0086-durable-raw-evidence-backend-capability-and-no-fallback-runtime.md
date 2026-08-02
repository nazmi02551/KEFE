# ADR-0086: Durable raw-evidence backend capability and no-fallback runtime

- Status: Accepted
- Date: 2026-08-02
- Parent: ADR-0085 / Slice 49

## Context

Slice 49 proves that KEFE, not provider-specific parser code, computes the canonical SHA-256 identity of exact HTTP response bytes and assembles the resulting evidence reference into `CapturedSource`. Its in-memory store is intentionally test-only and does not prove durable object custody.

A concrete cloud or storage vendor must not be selected before the generic durability, immutability and startup-failure boundary is executable. In particular, enabling durable evidence must never silently fall back to process memory or to a disabled/unconfigured store.

## Decision

KEFE introduces an exact raw-evidence runtime mode with only `DISABLED` and `EXTERNAL_DURABLE` values.

`DISABLED` composes the existing bounded `UnconfiguredRawSourceEvidenceStore`. `EXTERNAL_DURABLE` requires an exact registered capability profile and exact registered backend. Missing selection, profile or backend is a startup error. No fallback is permitted.

A durable capability profile is immutable and versioned. It fixes a canonical namespace, object-byte budget, read/write timeout budgets and opaque capability evidence reference. Atomic put-if-absent, immutable-object semantics and read-after-write verification are mandatory invariants and cannot be disabled by configuration.

The storage-vendor-neutral backend port is limited to two operations:

1. `put_if_absent` for one deterministic content-addressed object key;
2. `read_exact` for that same key.

The backend receives owned immutable bytes, a canonical optional media type and bounded timeout. It receives no provider secret, HTTP credential, parser, external locator, trace context or publication authority.

`DurableRawSourceEvidenceStore` computes the canonical SHA-256 locally, derives the deterministic object key, performs one atomic put-if-absent, then always reads the object back. It validates the exact object key, body bytes and media type before returning the Slice 49 `RawSourceEvidenceSeal`. Existing identical objects are idempotent. Missing or mismatched read-back evidence fails closed.

Backend failures are translated to bounded retryable/final raw-evidence codes without exception text, endpoint, credential, bucket/container or body disclosure. No autonomous retry loop is introduced.

Production composition registers zero durable profiles and zero durable backends in this slice. Therefore the default remains disabled, while selecting `EXTERNAL_DURABLE` fails startup until a later separately reviewed vendor-adoption slice registers an exact profile and backend.

## Consequences

- A later S3/GCS/Azure/MinIO or other implementation must satisfy the same atomicity and verification contract.
- Provider parsers remain unable to select content hashes, evidence references or storage locations.
- The process-memory store remains available only for explicit unit tests and cannot be selected by runtime configuration.
- This ADR does not prove deployed durability, encryption/KMS custody, retention, legal hold, replication, lifecycle policy, monitoring, SLOs or rollback readiness.
