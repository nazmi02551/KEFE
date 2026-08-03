# ADR-0090: Immutable RSS/Atom route assembly and exact parser-profile pinning

- Status: Accepted
- Date: 2026-08-03
- Slice: 54

## Context

KEFE now has separate, tested primitives for PUBLIC provider admission, controlled HTTP capture, immutable raw evidence, strict RSS/Atom feed-snapshot parsing, SourceArtifact persistence, ingestion-run admission and deterministic feed-item proposal extraction. Those primitives can still be assembled incorrectly: capture and extraction could use different parser budgets, callers could inject an unrelated pipeline/configuration pair, or an adapter could be registered without its matching worker runtime.

A concrete provider must not be adopted until the provider-neutral route assembly itself is exact, immutable and fail-closed.

## Decision

Introduce an immutable `RssAtomRouteProfile` and a provider-neutral route factory.

1. The profile pins one versioned route code, one versioned adapter code and one exact `StrictRssAtomParseProfile`.
2. The factory creates the strict capture definition, evidence-backed public adapter, feed-item extraction processor and one-stage ingestion worker registry as one `RssAtomRouteBundle`.
3. Capture validation and feed-item extraction use the exact same parser-profile object and immutable configuration.
4. The route configuration hash is canonical SHA-256 derived from the full immutable route profile plus the exact feed-item pipeline/stage/schema identities. Callers cannot supply an arbitrary configuration hash.
5. `acquisition_command()` accepts only the external locator. It always targets `RSS_ATOM_FEED_ITEM_EXTRACTION` version `1.0.0` and carries the route-derived configuration hash.
6. Route registries reject duplicate route codes, duplicate adapter codes and any bundle whose capture/processor/runtime identities drift from its profile.
7. Production composition may construct the route factory and an empty route registry, but registers zero route bundles, zero concrete RSS/Atom public adapters and zero feed-item worker plans.
8. Human review remains mandatory. The route ends at review-required `FEED_ITEM` proposals and cannot review, materialize, project, create Cases or publish.

## Execution order

The validated vertical path is exact:

`PUBLIC permit → controlled HTTP → immutable evidence seal → strict feed snapshot → SourceArtifact → exact ingestion run → evidence read → same-profile strict validation → FEED_ITEM proposals`

## Security and isolation

The route layer receives no secret resolver, credential bytes, DNS resolver, socket backend, raw object key, review authority or publication authority. It does not add retries, network fallbacks or preview fallbacks. The evidence store used for capture is also the evidence reader used by extraction, preventing split-store assembly.

## Consequences

A future provider adoption can supply an approved adapter/adoption profile and register one validated route bundle without reconstructing the pipeline ad hoc. Until that explicit decision, the production route registry remains empty and no live feed is captured.

This ADR does not prove provider terms/compliance approval, deployed egress, durable object-storage operations, scheduling, editorial usability, Case Builder, Flow Composer or phone-facing behavior.