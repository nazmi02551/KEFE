# ADR-0088 — Strict RSS/Atom parsing and evidence-backed public HTTP capture

Status: Accepted
Date: 2026-08-03

## Context

Slice 51 introduced an explicit `PUBLIC` provider credential mode and a permit-bound public capture path, but production still has no public HTTP adapter. The controlled HTTP transport, exact provider adoption profiles and immutable raw-evidence boundary already exist. A public feed adapter must reuse those controls without inventing a fake credential path or allowing XML parser behavior to become an unbounded or provider-specific trust boundary.

RSS and Atom documents are container snapshots that may contain many entries. Source Acquisition currently persists one immutable `SourceArtifact` per capture. This slice therefore validates and seals one feed snapshot; splitting entries into ingestion records or proposals remains a later worker responsibility.

## Decision

1. Add a credential-free evidence-backed public HTTP capture adapter that invokes `ControlledProviderHttpTransport` with no credential binding.
2. The adapter requires the existing PUBLIC permit path. It does not receive secret access, auth-header access, DNS, TLS, socket or retry primitives.
3. The exact provider adoption profile remains authoritative for HTTPS origin, method, media type, redirect, timeout and response-byte policy.
4. The raw HTTP body is sealed through `RawSourceEvidenceStore` before parser output can become a `CapturedSource`.
5. Trusted `content_hash` and `raw_storage_ref` are constructed only from the evidence seal. Parser output contains provider-neutral metadata only.
6. Introduce a reusable `StrictRssAtomCaptureDefinition` parameterized by exact immutable `adapter_code` and an immutable parser profile.
7. The parser accepts only RSS 2.0 or Atom 1.0. It validates UTF-8 XML, root identity, required feed fields, entry/item shape, timestamps and configured media types.
8. DTDs, entity declarations, processing instructions other than one leading XML declaration, non-UTF-8 encodings, XInclude elements and malformed XML fail closed.
9. Exact document-byte, element-count, depth, item-count, node-text, total-text, attribute-count and total-attribute budgets are enforced.
10. Feed descriptions and entry content are not executed, sanitized, interpreted as HTML or copied into operational output. Only bounded feed-level metadata is returned.
11. The canonical SourceArtifact URL is the exact requested HTTPS URL from the validated capture plan, not an untrusted URL declared inside the feed.
12. RSS item and Atom entry collections are validated but are not projected, reviewed or published by this slice.
13. Production composition exposes a public HTTP adapter factory but registers zero RSS/Atom adapters, zero provider adoption profiles and zero PUBLIC provider capabilities by default.

## Consequences

- A later provider-adoption slice can instantiate the generic definition with one exact adapter code and one exact adoption profile without changing parser semantics.
- Public feeds use the same SSRF, DNS/IP, exact-IP TLS/SNI, redirect and evidence controls as credentialed HTTP capture.
- XML parser resource use is bounded and unsafe XML constructs fail closed.
- A successful capture proves only that a bounded feed snapshot was acquired and sealed. It does not prove editorial truth, provider compliance or item-level ingestion.

## Rejected alternatives

- Fake secret references for public feeds.
- Direct `urllib`, `requests`, `httpx` or provider SDK access from the feed adapter.
- Parsing before durable evidence sealing.
- Trusting feed-declared URLs as the canonical acquisition URL.
- Emitting one SourceArtifact per item inside the capture adapter.
- Registering a real external feed in production without a separate adoption decision and evidence.

## Non-claims

This ADR does not introduce a concrete public feed, live endpoint access, production provider capability, legal/terms approval, deployed egress proof, item-to-proposal ingestion, automatic review/publication, Admin provider UI, Case Builder, Flow Composer or phone-facing provider behavior.
