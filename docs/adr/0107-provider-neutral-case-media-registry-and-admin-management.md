# ADR-0107 — Provider-neutral Case Media Registry and Admin Management

- **Status:** Accepted implementation boundary
- **Date:** 2026-08-05
- **Issue:** #310
- **Capabilities:** CAP-094 (primary), CAP-126 (supporting)
- **Foundation wave:** F3
- **Parent candidate:** PR #309 exact head `d2644bbcc2c7eb970c507f72e610ae35000c3798`
- **Related authority:** ADR-0031 and `docs/contracts/case-media-presentation.v1.yaml`

## Context

ADR-0031 already accepts a generic, optional and presentation-only `CASE_MEDIA` capability. Product Preview has a provider-neutral `CaseMediaRepository` backed only by packaged review fixtures. Production deliberately has no Preview fallback, no media registry, no Admin management surface and no concrete storage/CDN implementation.

F3 requires media operations to become administratively operable without turning a storage provider, CDN, upload endpoint or generated asset into a second content lifecycle. A production-side metadata boundary is therefore needed before any provider can be adopted.

## Decision

Introduce one bounded **Case Media Registry** that owns immutable media metadata and exact CaseVersion presentation bindings. It is an additive media authority only; existing Content Authoring, CaseVersion lifecycle, Content Configuration, Flow, publication resolver and consumer decision runtime remain authoritative for their existing concerns.

### Media asset identity

A media asset record is immutable after registration and contains:

- server-generated `media_asset_id`;
- stable bounded `asset_key`;
- exact media kind `IMAGE | VIDEO`;
- opaque provider-neutral `delivery_ref`;
- exact lower-case SHA-256 `content_hash`;
- exact positive `byte_length`;
- canonical `media_type` allowlisted for the declared kind;
- mandatory bounded `title`, `alt_text`, `credit_label` and `source_label`;
- optional bounded `caption` and `poster_asset_key`;
- server-derived registering Admin actor and UTC registration time;
- lifecycle `REGISTERED | READY | RETIRED`.

`delivery_ref` is an opaque reference, not a public URL, storage object key, credential, signed URL or provider proof. It may be resolved only by a separately configured production delivery adapter. Registration proves metadata integrity only; it does not prove bytes were uploaded, scanned, transformed, licensed or globally reachable.

Exact replay of the full immutable registration is idempotent. Reuse of `asset_key`, `delivery_ref` or `content_hash` with conflicting immutable data fails closed.

### Lifecycle

- `REGISTERED → READY` is an explicit Admin command after external/provider checks performed outside this slice.
- `REGISTERED → RETIRED` and `READY → RETIRED` are explicit Admin commands.
- `RETIRED` is terminal.
- No background task, provider callback or Case operation changes lifecycle automatically.
- Lifecycle transitions append immutable audit entries.

`READY` means only that an authorized operator has made the registry record eligible for Case binding. It is not a production availability, licensing, malware-scan, CDN, SLO or legal-compliance certification.

### CaseVersion binding

Bindings are immutable records keyed by exact `case_version_id`, presentation slot and asset identity. A binding contains:

- slot `HERO | CONTEXT | REVEAL | IMPACT`;
- exact positive priority;
- presentation flags `autoplay`, `muted`, `looping`;
- server-derived Admin actor and UTC bind time.

Rules:

- only `READY` assets may be newly bound;
- video autoplay is forbidden;
- `muted` and `looping` are allowed only for video;
- a CaseVersion may have at most one active binding for the same `(slot, asset_key)`;
- exact replay is idempotent; conflicting replay fails closed;
- bindings never mutate the CaseVersion body, lifecycle, Flow, questions, Commit, Reveal or publication provenance;
- retiring an asset removes it from production projection but preserves binding history and audit.

### Production projection

A read-only production projection returns only READY bound assets, ordered by `priority DESC, asset_key ASC`, mapped to the accepted ADR-0031 presentation model.

Projection includes opaque delivery references and metadata only. A separate provider-neutral delivery resolver may translate the opaque reference at the edge. If no resolver/provider is configured, production fails closed with no media; it must never use packaged Product Preview fixtures as fallback.

### Admin security

Add dedicated capabilities:

- `MEDIA_ASSET_READ` for bounded inventory/detail/audit reads;
- `MEDIA_ASSET_MANAGE` for register, mark-ready, bind and retire commands.

Write commands require the existing authenticated Admin write principal, same-session CSRF and recent step-up. Actor identity is server-derived. Browser requests cannot supply actor, role, lifecycle authority, storage credentials, public URLs or Case publication state.

### Admin Studio

Add an explicit `/case-media` workspace with separate commands for session verification, inventory/detail/audit reads, registration, readiness, binding and retirement.

The route performs no request on mount, navigation, focus, selection or query-prefill changes. It has no polling, autosave, browser token persistence, binary file input, upload, signed-URL generation, transformation, bulk action, automatic binding or publication control.

## Persistence

Use one additive `media` PostgreSQL schema with:

- immutable media asset metadata;
- one-way lifecycle state plus append-only audit;
- immutable CaseVersion binding history;
- uniqueness and check constraints matching the executable contract.

Memory and PostgreSQL adapters must have equivalent behavior. PostgreSQL evidence must prove restart continuity and reject direct immutable-field mutation, lifecycle rollback and audit mutation.

## Privacy and safety

Admin and projection surfaces must not expose:

- credentials, secrets, signed URLs, provider SDK objects or backend object keys;
- raw media bytes;
- user, author, reporter, decision-session or device identities;
- personality, ideology, psychometric, morality, bias or causal inference;
- Preview fixture paths in production responses.

## Explicit exclusions

This ADR does not implement or prove:

- binary or multipart upload;
- object-store/CDN provider, bucket/container or public delivery;
- signed URL generation;
- image transformation, thumbnailing, video transcoding, DRM or streaming;
- malware scanning, EXIF stripping, encryption/KMS, retention/deletion/legal hold;
- provider activation, licensing review or external availability;
- automatic Case mutation, review, approval, publication or consumer fallback;
- production deployment, SLO, alerting, rollback, store compliance or human CQB/usability acceptance.

## Implementation enforcement

- The runtime injects an unavailable delivery gate until a separately reviewed provider-neutral resolver exists; therefore production projection is empty by default even when READY bindings are present.
- Memory and PostgreSQL repositories re-check READY state at binding insertion so a concurrent retirement cannot create a newly eligible binding.
- PostgreSQL insert guards also reject autoplay and image-only misuse of `muted` or `looping`, while append-only and immutable-field triggers protect asset, binding and audit history from direct mutation.
- An allow-all test gate is used only inside repository tests to prove deterministic eligible projection ordering; it is not wired into application runtime or treated as provider activation evidence.

## Consequences

- CAP-094 advances through a contract-verified metadata and management slice, but remains partial until provider/storage/CDN operation and human/external gates are separately proven.
- Product Preview continues using packaged local assets through its explicit repository.
- Production obtains a canonical, provider-neutral and fail-closed media metadata boundary without creating a second CMS or weakening CaseVersion immutability.
