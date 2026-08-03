# ADR-0090 — Validated public feed definitions and manual capture runtime

- Status: Accepted
- Date: 2026-08-03
- Slice: 54

## Context

Slices 51–53 established PUBLIC permit routing, controlled HTTP capture, immutable raw evidence, strict RSS/Atom validation and deterministic feed-item proposal extraction. The remaining gap is an explicit configuration boundary that ties those generic primitives together without silently selecting or activating a real publisher.

A public feed definition is security-sensitive configuration. It controls the outbound locator, provider adoption profile, quota/circuit settings, parser identity and ingestion pipeline. Treating these values as scattered startup arguments would make drift and accidental activation difficult to detect.

## Decision

KEFE introduces an immutable, versioned `PublicFeedDefinition` and an explicit runtime-bundle builder.

A definition contains one unique feed code and one unique adapter code. The external locator must be canonical HTTPS, must not contain userinfo or fragments, must use port 443, and must not contain query parameter names commonly used for credentials or signatures. The locator origin must exactly match the single origin derived into the provider adoption profile.

The definition owns every provider HTTP budget, evidence reference and provider admission quota/circuit value. The builder derives:

1. one exact `ProviderAdoptionProfile` per definition;
2. one strict RSS/Atom public capture adapter per definition;
3. one exact PUBLIC provider-capability template with no secret reference;
4. the Slice 53 deterministic feed-item ingestion registry;
5. an immutable feed-definition registry.

The builder rejects duplicate feed codes, duplicate adapter codes and configuration conflicts. It performs no network call and does not mutate provider admission persistence.

`ManualPublicFeedCaptureService` resolves an exact definition and emits exactly one `SourceAcquisitionCommand` to the existing acquisition service. It does not create schedules, run ingestion workers, review proposals, materialize content or publish Cases. The existing permit, evidence, Commit First and Blind First boundaries remain authoritative.

Production startup continues to register zero concrete public feed definitions. This slice provides an explicit activation primitive, not an activation decision.

## Consequences

- A later provider-adoption change can be reviewed as one immutable definition instead of scattered wiring.
- Public-feed activation remains fail-closed until a concrete definition, terms evidence, rate-limit evidence, adoption profile and PUBLIC capability are deliberately supplied.
- Manual capture can be tested end to end without live network access.
- Recurring schedules and Admin UI remain separate product decisions.

## Non-goals

This ADR does not select a publisher, approve terms, prove production egress or object-storage durability, add automatic scheduling, automate editorial review/materialization/publication, create Claims/Cases, or add phone-facing feed controls.