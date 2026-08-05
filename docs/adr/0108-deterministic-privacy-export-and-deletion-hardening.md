# ADR-0108 — Deterministic Privacy Export and Deletion Hardening

- **Status:** Accepted implementation boundary
- **Date:** 2026-08-05
- **Issue:** #312
- **Capabilities:** CAP-085 (primary), CAP-126 (supporting)
- **Foundation wave:** F4 / P0
- **Parent candidate:** PR #311 exact head `4f31fb894c153b9bc5c90a5a0dc6fce534db04b8`

## Context

KEFE already exposes authenticated self-service privacy operations through `GET /v1/me/privacy-export` and `DELETE /v1/me`. The existing authority exports product data and removes actor-partitioned private data while retaining a bounded deletion receipt and anonymized audit exception.

The current behavior is functional but not sufficiently executable as a stable privacy contract:

- export has no explicit schema version, canonical manifest or deterministic digest;
- the destructive confirmation value is the generic literal `DELETE` rather than being bound to the authenticated actor;
- PostgreSQL permits more than one deletion receipt for the same actor;
- concurrent repository calls do not have an explicit one-receipt replay contract;
- guest/account merge linkage may remain after deletion;
- no dedicated exact contract, OpenAPI check or PostgreSQL concurrency/restart proof exists for CAP-085.

## Decision

Strengthen the existing `PrivacyService` and `/v1/me` routes. They remain the sole self-service privacy authority. No parallel privacy state machine, export job queue, downloadable archive store or secondary user-data copy is introduced.

### Versioned deterministic export

The export response remains backward-compatible and adds:

- `schema_version = privacy-export.v2`;
- a deterministic `manifest`;
- `data_sha256`, a lower-case SHA-256 digest.

The canonical digest document is exactly:

```json
{
  "schema_version": "privacy-export.v2",
  "actor_id": "<authenticated actor UUID>",
  "actor_kind": "<authenticated actor kind>",
  "retention": {},
  "manifest": {},
  "product_data": {}
}
```

`generated_at` and `data_sha256` are excluded from the digest. Canonical encoding uses recursively sorted JSON object keys, compact separators, UTF-8 and no ASCII escaping. Arrays retain their repository-defined semantic order. Repository adapters must therefore return stable ordering for every exported collection.

The manifest contains:

- `dataset_counts`, keyed by sorted top-level `product_data` dataset name;
- `total_records`, the sum of those counts;
- `empty_datasets`, sorted lexicographically.

Array and object datasets use their cardinality, `null` counts as zero and any other scalar counts as one. The export payload is calculated on demand and is never persisted by this slice.

### Actor-bound destructive confirmation

`DELETE /v1/me` requires the exact header value:

```text
X-KEFE-Delete-Confirm: DELETE:<authenticated_actor_uuid>
```

The actor UUID is derived from the authenticated principal. The browser cannot choose a different deletion subject. Comparison is exact and constant-time. A generic `DELETE` value, another actor UUID, malformed value or missing header fails closed with the existing confirmation error code.

This confirmation hardening does not claim recent reauthentication, legal consent certification or jurisdiction-specific compliance. Those require separate identity and legal decisions.

### One append-only receipt per actor

Deletion remains transactional and preserves the existing policy boundary:

- actor-partitioned private product rows are removed;
- guest/account merge linkage involving the deletion subject is removed;
- retained audit/outbox records lose direct actor identifiers and carry only the bounded deletion marker;
- actor sessions and verified account identifiers are removed;
- the actor is marked `DELETED` rather than physically removed;
- exactly one deletion receipt is retained per actor.

PostgreSQL must lock the actor row before destructive work. If a receipt already exists, the repository returns that same receipt without repeating deletion. A unique constraint on `actor_id` and an append-only update/delete guard provide database-level enforcement. Concurrent calls must converge on one receipt ID and one policy version.

The in-memory adapter must provide equivalent behavior using one repository lock and an actor-keyed receipt store. Its identity cleanup must remove merge aliases where the actor is either the source guest or destination account.

Deletion receipts use `PRIVACY_SELF_SERVICE_V2`. Existing historic `MVP_PRIVACY_V1` receipts remain readable and are not rewritten.

### Response boundary

The deletion response remains backward-compatible and additionally returns the server-derived `actor_id` and `actor_kind` from the receipt. It contains no identifiers belonging to another actor, private content, export payload or reusable profile data.

### Data coverage

The canonical repository remains responsible for the existing actor-partitioned domains:

- identity sessions, account identifiers and guest/account merge linkage;
- decision sessions and their cascading responses, private reasons, revisions, drafts, exposure, intervention, delta and reflection rows;
- Community Reason authoring, reactions and reports;
- sharing records;
- consensus participation;
- direct actor references retained in audit/outbox payloads.

This slice does not silently claim deletion of future tables. The executable contract and PostgreSQL test must fail when the declared deletion coverage and actual migration/catalog boundary drift.

## Security, privacy and product invariants

- Actor identity is server-derived.
- No export payload, digest input document or private content is stored by the privacy layer.
- The deletion receipt is append-only and contains no reusable profile data.
- No personality, ideology, psychometric, morality, bias, causal or normative inference is produced.
- Commit First, Blind First, immutable CaseVersion, generic runtime and Product Preview/production isolation remain unchanged.
- My KEFE remains observed/descriptive history only.

## Verification

The implementation must provide:

- an executable architecture/contract checker;
- memory HTTP tests for deterministic export, digest reproducibility, actor-bound confirmation and same-receipt replay;
- PostgreSQL 17 migration, restart, concurrent deletion, receipt uniqueness, merge-link cleanup and append-only mutation proof;
- an exact focused OpenAPI contract for the two existing privacy operations plus composed 0.19 and 0.20 drift gates;
- exact-head API, Mobile, MVP and Global regression evidence.

No CI evidence means no PASS.

## Explicit exclusions

This ADR does not implement or prove:

- legal or regulatory compliance certification;
- jurisdiction-specific response or deletion deadlines;
- recent reauthentication or MFA for consumer deletion;
- asynchronous/background export jobs;
- downloadable ZIP/archive storage;
- email or external delivery of exports;
- a retention scheduler or automated legal-hold engine;
- export payload persistence or a privacy warehouse;
- CAP-084 guest/account merge behavior changes;
- production deployment;
- deployed load, SLO, alerting or rollback behavior;
- human legal/CQB/usability acceptance;
- store compliance or released mobile artifacts.

## Consequences

- CAP-085 advances through a deterministic and concurrency-safe repository candidate but receives no lifecycle promotion in this slice.
- Existing clients keep the original export and receipt fields while gaining additive verification metadata.
- Deletion becomes actor-bound and converges on a single append-only receipt without creating a second privacy workflow.
