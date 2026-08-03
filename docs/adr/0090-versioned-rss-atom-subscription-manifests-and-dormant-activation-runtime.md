# ADR-0090: Versioned RSS/Atom subscription manifests and dormant activation runtime

- Status: Accepted
- Date: 2026-08-03
- Slice: 54
- Supersedes: none
- Extends: ADR-0088 and ADR-0089

## Context

Slices 52 and 53 established a strict evidence-backed RSS/Atom capture adapter and a deterministic feed-item extraction stage. The generic source acquisition scheduler can already execute an admitted capture, persist an immutable `SourceArtifact`, admit an ingestion run and later execute the exact ingestion worker plan. What is missing is a controlled configuration boundary that binds these existing components without hard-coding a concrete feed or silently enabling live capture.

## Decision

KEFE introduces an immutable, versioned `RssAtomSubscriptionManifest` and a registry of those manifests.

A manifest owns only declarative configuration:

- a versioned subscription code and adapter code;
- one exact HTTPS feed locator;
- fixed-interval schedule and bounded dispatch attempts;
- PUBLIC provider quota, permit and circuit settings;
- controlled HTTP timeout, redirect and byte budgets;
- opaque terms and rate-limit evidence references;
- optional locale and jurisdiction metadata.

The manifest never contains credentials. It never contains a backend object key, raw response body, secret reference, review decision or publication instruction.

Multiple subscriptions may share one adapter. They may do so only when all adapter-level provider capability and HTTP-policy fields are exactly equal. Their allowed HTTP origins are derived from their exact feed locators, canonicalized, deduplicated and sorted. A manifest cannot add an origin that is not represented by one of its exact locators.

The runtime assembly is deterministic:

1. group manifests by adapter code;
2. create one `ProviderAdoptionProfile` per adapter;
3. create one strict RSS/Atom public capture adapter per adapter through `EvidenceBackedPublicHttpCaptureAdapterFactory`;
4. create the exact Slice 53 ingestion runtime when at least one manifest exists;
5. expose an explicit activation service.

The extraction pipeline identity, stage identity and parser profile remain exactly those accepted in Slice 53. Slice 54 does not create a second parser or a second feed extraction pipeline.

Activation is explicit. Application startup composes the registry and activation service but does not call activation. The production registry is initially empty. Therefore startup registers zero RSS/Atom provider adoption profiles, zero RSS/Atom public adapters, zero feed ingestion plans/processors and zero schedules.

When activation is explicitly invoked, ordering is exact:

1. register or verify the PUBLIC provider capability;
2. create or verify the fixed-interval source acquisition schedule.

Capability-first ordering is intentional. If schedule creation fails, the partial capability is inert because no schedule exists. Repeating the same activation is idempotent through the existing immutable provider and schedule repositories. Configuration drift fails closed.

A subscription configuration hash is lowercase SHA-256 over its canonical immutable manifest payload. That hash is used as the source acquisition schedule configuration hash and therefore enters the ingestion run key.

## Consequences

- The generic scheduler, acquisition service, controlled HTTP transport, evidence store and ingestion worker remain the only execution path.
- A future concrete feed requires an explicit manifest addition plus separate legal/compliance and deployed capability evidence.
- Dynamic runtime mutation and an Admin subscription API are not introduced here.
- No live network test or provider-specific registration is introduced.
- Human review remains mandatory for extracted `FEED_ITEM` proposals.
- No automatic materialization, Case creation or publication is added.

## Rejected alternatives

### Hard-code a feed in application startup

Rejected because it would silently enable an external dependency and bypass explicit adoption evidence.

### Create a second feed scheduler or ingestion worker

Rejected because the existing generic scheduler and worker already provide lease, retry, idempotency and persistence guarantees.

### Allow each subscription to define a custom parser profile under pipeline version 1.0.0

Rejected because that would create semantic drift under one immutable pipeline identity. A profile change requires a later explicit pipeline-version decision.

### Activate all registered manifests automatically at startup

Rejected because configuration presence is not operational approval. Activation remains an explicit command boundary.
