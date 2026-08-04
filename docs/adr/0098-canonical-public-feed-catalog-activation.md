# ADR-0098 — Canonical Public Feed Catalog and Activation Projection

- Status: Accepted for execution
- Date: 2026-08-04
- Issue: #291
- Parent runtime: PR #290 / `140960ac80881faec5841008eac9444ab67d9b7a`
- Capabilities: CAP-055, CAP-056, CAP-061, CAP-065, CAP-094, CAP-095, CAP-123, CAP-126

## Context

Two green candidate lines diverge after PR #232:

- PR #273 provides a durable Admin-governed public-feed catalog with immutable definitions, lifecycle and audit;
- PR #267 provides immutable RSS/Atom manifests and capability-first, schedule-second activation into the generic provider/scheduler runtime.

They overlap in source identity, runtime composition and migration numbering. Merging both would create parallel catalog/subscription families and conflicting `20260803_0026` migrations.

## Decision

KEFE will use one authoritative, versioned **Public Feed Catalog** and one distinct **Activation Projection** into the existing provider, scheduler, evidence, ingestion and Proposal runtime.

### Catalog aggregate

A catalog definition is immutable and versioned by `(feed_code, definition_version)`. The complete definition includes:

- display name and exact versioned adapter code;
- canonical HTTPS locator;
- strict RSS/Atom parser profile identity;
- HTTP timeout, redirect, media and byte budgets;
- provider quota, circuit and permit policy;
- interval and maximum dispatch attempts;
- opaque terms and rate-limit evidence references;
- optional locale and jurisdiction.

Its canonical configuration hash covers every immutable field plus the exact Feed Item pipeline/stage identities. The catalog hash pins the existing immutable `PublicFeedDefinition.configuration_hash`; no parallel ingestion hash field is introduced.

Catalog lifecycle:

1. `DRAFT` — created by a source manager;
2. `APPROVED` — maker-checker approval after deterministic preflight;
3. `RETIRED` — terminal catalog state.

A definition is never edited in place. Any change creates the next integer definition version and requires new approval.

### Preflight

Preflight is read-only and performs no network, provider registration, schedule creation or worker execution. It validates that the definition can deterministically construct:

- a PUBLIC provider capability template;
- an exact provider adoption profile;
- an RSS/Atom capture definition;
- a Feed Item acquisition command;
- a generic schedule command.

### Maker-checker approval

Approval requires:

- authenticated Admin session;
- `SOURCE_APPROVE` capability;
- recent step-up;
- an actor different from the creator;
- exact expected configuration hash;
- successful preflight against the same immutable definition.

Approval does not activate a feed.

### Activation projection

Activation is a separate, explicit, `SOURCE_ACTIVATE` and step-up-protected command over one exact APPROVED version. It projects in this order:

1. exact PUBLIC provider capability registration through the existing `PublicProviderCapabilityTemplate` and provider admission service;
2. exact adoption/capture/worker runtime profile registration or verified equality;
3. exact generic source schedule creation.

Capability-first and schedule-second ordering is mandatory. Exact replay returns the existing projection. Partial projection may be retried only when every already-existing identity equals the approved version. The canonical line does not introduce another provider capability factory or scheduler lifecycle.

Activation state is separate from catalog state:

- `ACTIVE`;
- `PAUSED`;
- terminal `RETIRED`.

Pause/resume delegates to the existing scheduler/provider lifecycle rather than creating a parallel scheduler state machine. Definition retirement does not silently delete runtime or evidence history.

### Production composition

Production composition contains:

- the catalog repository and secured Admin service;
- zero seeded definitions;
- zero startup activation;
- no automatic network operation.

A real source requires separate externally evidenced provider/legal/egress/storage approval and an explicit catalog registration/approval/activation sequence.

## Migration resolution

The canonical migration revision is `20260804_0026`, based on canonical head `20260803_0025`. Neither alternative `20260803_0026` migration is adopted. The new migration owns only the canonical catalog, audit and activation-projection tables.

## Downstream review

The existing PR #290 flow remains authoritative:

`capture → immutable evidence → SourceArtifact → FEED_ITEM Proposal → human review → explicit Source Brief build → human review`.

Catalog approval or activation never reviews, normalizes, creates a Candidate Case, projects to Content Authoring, approves or publishes content.

## Supersession

After exact integrated evidence:

- PR #267 and PR #273 become superseded implementation sources;
- compatible tests/behavior may be retained;
- their duplicate aggregates, composition and migration identities must not enter the canonical line.

## Evidence required

Completion requires one exact SHA to pass:

- canonical public-feed architecture and behavior CI;
- memory and PostgreSQL lifecycle/idempotency/concurrency/migration tests;
- Admin authorization, CSRF, step-up and maker-checker tests;
- no-live-network approved-version → capability → schedule → review-required FEED_ITEM vertical proof;
- provider admission/secret/HTTP/pinned/capture/evidence/RSS/extraction/worker parent gates;
- API CI, Mobile CI, MVP Beta Gates and Global Readiness.

## Claims not made

Automation does not prove a real provider, terms compliance, deployed egress or storage, production scheduling, editorial acceptance, human usability, SLO/load/observability, rollback or store readiness.