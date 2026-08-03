# ADR-0091 — Durable public feed catalog and secured Admin lifecycle

- Status: Accepted
- Date: 2026-08-03
- Slice: 55

## Context

Slice 54 introduced immutable public-feed definitions and an explicit manual-capture runtime bundle, while production composition continued to register zero concrete feeds. The next boundary is durable governance: an authorized Admin must be able to register an exact definition, inspect it, approve it for a future manual-capture operation, or retire it without editing the immutable definition in place.

A catalog entry is operational policy, not editorial content. It controls whether a definition may later be supplied to a capture runtime, so registration and lifecycle transitions require explicit authorization, CSRF protection, auditability and database constraints.

## Decision

KEFE introduces a durable `PublicFeedCatalogEntry` with lifecycle:

`REGISTERED → MANUAL_CAPTURE_APPROVED → RETIRED`

No backward transition exists. The embedded `PublicFeedDefinition`, its canonical configuration hash, feed code and adapter code are immutable. Reconfiguration requires a new versioned feed code and adapter code.

Registration is idempotent only when the existing entry has the exact same immutable definition and configuration hash. A conflicting feed code or adapter code fails closed. Every successful mutation is committed atomically with an ordered `PublicFeedCatalogAuditEntry`.

A new Admin capability, `SOURCE_MANAGE`, authorizes catalog reads and registration. Approval and retirement also require fresh step-up authentication because they change operational eligibility. CSRF-protected Admin write authentication remains mandatory for all mutations.

Memory and PostgreSQL repositories implement equivalent semantics. PostgreSQL stores the immutable definition as JSONB plus a canonical SHA-256 configuration hash, unique feed and adapter codes, constrained lifecycle state and append-only audit rows.

The internal Admin API exposes strict endpoints for list, detail, registration, manual-capture approval, retirement and audit reading. It never constructs a feed runtime bundle, registers an adapter, issues a provider permit, performs network access, creates schedules, runs ingestion, reviews proposals or publishes content.

Production startup composes the empty catalog repository and secured service. Zero catalog entries are seeded.

## Consequences

- Public-feed governance becomes durable and auditable.
- Operational eligibility is explicit and step-up protected.
- Immutable definitions cannot be silently edited after review.
- A later manual-capture endpoint can require the approved lifecycle state.
- No real feed or provider is activated by this slice.

## Non-goals

This ADR does not select a publisher, approve external terms on KEFE's behalf, activate capture runtime, execute manual capture, schedule recurring capture, automate editorial actions, create Cases, or add an Admin web UI or phone-facing feed controls.