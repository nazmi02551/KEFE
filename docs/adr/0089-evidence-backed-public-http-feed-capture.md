# ADR-0089 — Evidence-backed public HTTP feed capture

Status: Accepted
Date: 2026-08-03
Issue: #238
Parent: PR #237 / ADR-0088

## Context

KEFE now has an exact PUBLIC provider execution mode and a hostile-input RSS/Atom parser. A public feed adapter must still use the existing controlled HTTP transport and immutable raw-evidence boundary; it must not create a parallel network client, bypass adoption profiles or let parsed metadata invent integrity fields.

## Decision

Introduce a provider-neutral public HTTP feed capture adapter.

1. The adapter implements the existing public capture protocol and receives no secret or authentication capability.
2. A definition builds one exact `ProviderHttpCapturePlan`; adapter and request codes must match.
3. The existing `ControlledProviderHttpTransport` executes the request with `credential=None`.
4. Existing adoption-profile, origin, method, query, DNS/IP, TLS, redirect, timeout, status, media-type and response-size controls remain authoritative.
5. The exact response body is sealed through `RawSourceEvidenceStore` before feed parsing.
6. The adapter independently verifies evidence content hash, byte length, media type and seal time.
7. Only after a valid seal does the strict Slice 52 RSS/Atom parser run.
8. The parser cannot set content hash or storage reference. The adapter constructs `CapturedSource` from the trusted seal.
9. The captured artifact represents the immutable feed document; its external identity is the parsed canonical feed URL when present, otherwise the exact bounded external locator.
10. HTTP, evidence and parser failures map to bounded source-capture codes without response bodies, URLs, headers or exception text.
11. Production public adapter and adoption registries remain empty.

## Consequences

- Public feed capture follows the same SSRF, exact-IP TLS and evidence-integrity chain as credentialed capture.
- Malformed or unsupported feed bodies may be retained as immutable evidence but cannot produce a SourceArtifact.
- Entry extraction and staging remain a later explicit ingestion slice.

## Non-claims

No real feed, endpoint approval, live request, provider compliance proof, production egress, automatic scheduling, entry staging, proposal generation, editorial acceptance, publication or phone-facing provider behavior is introduced.