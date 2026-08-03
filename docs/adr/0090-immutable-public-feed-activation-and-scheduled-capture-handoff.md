# ADR-0090: Immutable public feed activation and scheduled capture handoff

- Status: Accepted
- Date: 2026-08-03
- Slice: 54

## Context

Slices 51–53 provide a provider-neutral PUBLIC permit route, controlled HTTP transport, immutable raw-evidence sealing, strict RSS/Atom feed-snapshot parsing and deterministic feed-item proposal extraction. The individual pieces are intentionally unregistered in production. A later concrete feed must not be activated by independently editing provider capability, HTTP policy, parser budgets, scheduler inputs and ingestion pipeline configuration because partial or drifting configuration could bypass the intended controls.

## Decision

KEFE introduces one immutable `PublicFeedActivationDefinition` that binds:

1. one versioned activation identity;
2. one versioned adapter identity;
3. one exact HTTPS feed locator and its single allowed origin;
4. one PUBLIC, secret-free and ENABLED provider capability;
5. one GET-only `ProviderAdoptionProfile`;
6. one strict RSS/Atom parser profile;
7. one source schedule definition; and
8. the exact `RSS_ATOM_FEED_ITEM_EXTRACTION` pipeline and version.

The activation computes a canonical lowercase SHA-256 configuration hash over every immutable field. The source schedule uses that exact hash. HTTP media types must equal parser media types and the HTTP response byte budget must equal the parser document byte budget. The feed locator origin must be the only allowed origin. Query parameters with credential-like names, userinfo, fragments and non-443 ports are rejected.

`PublicFeedActivationBundleFactory` is a pre-start composition primitive. It builds immutable activation, adoption and public-capture registries plus capability and schedule seeds. It does not mutate a running registry, perform network access, install a provider or create a schedule by itself. Explicit bootstrap code may persist the returned capability and schedule seed through existing repositories/services.

The scheduled vertical path remains exact:

`due schedule -> provider admission permit -> credential-mode routing -> controlled PUBLIC HTTP -> immutable raw evidence -> SourceArtifact -> ingestion run -> feed-item worker proposals`.

Human review remains mandatory. Activation never reviews, materializes, projects or publishes a proposal.

## Production boundary

Production composition registers zero public feed activations, zero concrete RSS/Atom public adapters and zero feed-item worker plans. No external feed, provider terms approval, deployed egress, durable object-store capability, editorial usability proof or phone-facing feed behavior is claimed by this ADR.

## Consequences

A concrete feed can later be adopted only by supplying one coherent activation definition and separate operational evidence. Configuration drift fails before capture. Tests may build a complete in-memory vertical path without weakening production defaults or using live network access.