# ADR-0081 — Controlled outbound HTTP transport and provider adoption conformance

**Status:** Accepted for Slice 45 implementation  
**Date:** 2026-08-02  
**Issue:** #215  
**Parent:** ADR-0080 / PR #214

## Context

Slices 39–44 establish provider-neutral acquisition, durable scheduling and supervision, provider capability admission, quota/circuit/permit control, and callback-scoped ephemeral secret execution. A real provider adapter would still require outbound network access. Allowing each adapter to create its own HTTP client would reintroduce ambient proxy behavior, DNS rebinding/SSRF risk, inconsistent timeout and response limits, redirect ambiguity, and secret-bearing operational logs.

The product authority does not yet select RSS, X, YouTube or any other first provider. Therefore this slice must create a provider-neutral safety and conformance boundary without claiming external provider compliance or enabling a live provider.

## Decision

An exact versioned adapter may use outbound HTTP only through an immutable `ProviderAdoptionProfile` and a controlled one-hop-at-a-time transport service.

The profile authorizes exact HTTPS origins, GET/HEAD methods, response media types, timeout budgets, maximum response bytes, redirect hops, and opaque terms/rate-limit evidence references. Wildcards, HTTP, userinfo, ambiguous ports and mutable profile replacement are forbidden.

Each request is validated against the exact profile. DNS resolution is delegated to a port. Every resolved address must be syntactically valid and globally routable; mixed public/private results are rejected. The service deterministically selects one approved address and hands a pinned request containing exact host/SNI plus selected IP to a backend port. The backend may not silently re-resolve or follow redirects.

Redirects are interpreted by the service one hop at a time, revalidated against the same profile and re-resolved/pinned. Response status, elapsed time, media type and body size are enforced before the provider adapter receives the body.

Operational observations contain only adapter identity, bounded outcome/error code, status class, redirect count, byte count and elapsed duration. They contain no URL path/query, headers, credentials, response body/text or exception text.

Production composition remains inert: the adoption registry is empty and both DNS/backend ports are unconfigured. No live network call can occur merely because this transport code exists.

## Consequences

- A provider-specific adapter cannot bypass exact origin and resource budgets.
- DNS rebinding and private-address targets fail closed before backend execution.
- Redirect policy remains explicit and observable without exposing locations.
- Provider terms/rate-limit references are recorded as evidence pointers only; KEFE does not claim legal or operational compliance from their presence.
- The first real provider requires a separate contract, profile registration, resolver/backend activation and provider-specific evidence.

## Explicit exclusions

No real provider adapter, external network call, system DNS activation, TLS/socket implementation, browser automation, scraping, secret-manager SDK, credential rotation, provider compliance certification, autonomous retry/backoff, Admin UI, automatic editorial action, deployment/SLO proof or phone behavior is introduced.