# ADR-0091: Immutable public feed activation catalog and read-only Admin inspection

- Status: Accepted
- Date: 2026-08-03
- Slice: 55

## Context

Slice 54 defines a coherent pre-start activation bundle, but production intentionally registers zero public feeds. Before any future feed can be operationally adopted, KEFE needs an auditable catalog that records the exact immutable activation manifest independently from a running process. Storing arbitrary mutable dictionaries or exposing activation writes over Admin HTTP would allow configuration drift, secret leakage or accidental runtime activation.

## Decision

KEFE introduces an insert-only `PublicFeedActivationCatalogEntry` and repository boundary.

Each entry stores:

1. a stable UUID;
2. one exact versioned activation code;
3. one exact versioned adapter code;
4. one canonical lowercase SHA-256 configuration hash;
5. one canonical JSON manifest string using schema `kefe.public-feed-activation-manifest/1.0.0`;
6. one opaque evidence reference;
7. the recording Admin actor reference; and
8. a UTC recording timestamp.

The manifest is produced only from `PublicFeedActivationDefinition.configuration_payload`. Canonical JSON uses sorted keys, compact separators and ASCII escaping. Construction and repository reads recompute SHA-256 and require equality with the stored configuration hash. Manifest JSON is returned to callers only as a newly parsed owned object.

Secret references, authorization or cookie headers, credential-bearing query names, backend object keys and private exception text are forbidden in catalog manifests. The repository exposes `create_or_get`, exact lookup and bounded deterministic listing only. It exposes no update, delete, enable, schedule, capture or activation operation. Re-recording the exact immutable entry is idempotent; reuse of an activation code or adapter code with different immutable content fails closed.

Memory and PostgreSQL implementations follow the same contract. Migration `20260803_0026` creates an insert-only catalog table after `20260803_0025`. Repository code never issues UPDATE or DELETE against that table.

Admin inspection is authenticated and authorized with `SOURCE_VERIFY`. The HTTP surface is read-only:

- `GET /internal/admin/v1/public-feed-activations`
- `GET /internal/admin/v1/public-feed-activations/{activation_code}`

No write route is introduced. Responses expose immutable manifest metadata and an owned parsed manifest; they do not expose runtime controls, secrets or provider execution context.

## Production boundary

Production builds an empty catalog repository. It does not seed test activations, build Slice 54 activation bundles, install schedules, register adapters or start workers. Recording a catalog entry is not provider approval and does not activate a feed.

## Consequences

Future provider adoption can reference an auditable immutable manifest while operational activation remains a separate explicit decision. Admin users can inspect exact catalog evidence without gaining a hidden activation API. PostgreSQL downgrade is blocked while catalog entries exist, preventing silent loss of audit records.