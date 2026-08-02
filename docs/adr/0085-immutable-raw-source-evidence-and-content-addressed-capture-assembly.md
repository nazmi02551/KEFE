# ADR-0085 — Immutable raw source evidence and content-addressed capture assembly

- Status: Accepted
- Date: 2026-08-02
- Parent: ADR-0084 / Slice 48

## Context

Slice 48 isolates provider-specific HTTP request planning and bounded response parsing from secrets, DNS, TLS, sockets, redirects and retry control. Its transitional parser contract can still return a complete `CapturedSource`, including `content_hash` and `raw_storage_ref`. A concrete provider parser must not be trusted to choose either value. The raw response body is the evidence; KEFE must seal it before semantic parsing and must be the only authority that assigns its content hash and storage reference.

## Decision

Introduce a separate evidence-backed capture path without changing the accepted Slice 48 primitive.

1. `RawSourceEvidenceStore` receives an exact versioned adapter code, owned immutable response bytes, an optional exact media type and a timezone-aware UTC sealing time.
2. KEFE computes lowercase SHA-256 over the exact response bytes. The canonical identifiers are `sha256:<64 lowercase hex>` and `evidence://sha256/<64 lowercase hex>`.
3. `RawSourceEvidenceSeal` is immutable, slotted and repr-redacted. It contains only the canonical hash, canonical opaque reference, byte length, optional media type and UTC sealed time.
4. The in-memory store is deterministic test infrastructure only. It stores an owned immutable byte copy, returns owned copies for inspection, is idempotent for identical bytes and fails closed if a digest is ever associated with different bytes.
5. The unconfigured store fails with a bounded retryable storage-unavailable error. No production durability is claimed by this slice.
6. `ProviderHttpParsedSource` is metadata-only. It has no `content_hash` or `raw_storage_ref` field.
7. `EvidenceBackedProviderHttpCaptureDefinition` may only build a request plan and parse a bounded `ProviderHttpResponse` into metadata-only output. It cannot access storage credentials, storage backends, mutable evidence buffers, secret material, DNS, TLS, sockets, redirects or retry control.
8. Execution order is exact: build plan, secure HTTP execute, seal raw evidence, parse bounded response, then KEFE assembles the exact `CapturedSource`.
9. `CapturedSource.content_hash` and `CapturedSource.raw_storage_ref` are copied only from the validated evidence seal. Parser output cannot override them.
10. Raw bytes, URLs and storage internals do not enter repr, operational results or bounded error text.
11. Slice 48 remains available only as a stack-compatible transitional primitive. A future concrete HTTP provider adoption must use the evidence-backed path or a later contract that provides equivalent or stronger evidence integrity.

## Consequences

- Raw evidence integrity is independent of parser correctness.
- Parser bugs cannot forge provenance identifiers.
- Evidence may be sealed even when parsing later fails; content-addressing makes repeated sealing idempotent.
- A durable object-store backend, encryption/KMS, retention, legal hold, malware scanning and deletion policy remain separate decisions.

## Explicit non-claims

This ADR does not claim S3/GCS/Azure/MinIO/filesystem durability, encryption at rest, KMS custody, retention or deletion policy, legal hold, malware scanning, compression, a real provider parser, a live external request, deployed storage monitoring, provider compliance or automatic editorial publication.