# ADR-0090 — Feed pipeline activation governance and read-only preflight

Status: Accepted
Date: 2026-08-03

## Context

Slices 51–53 provide a PUBLIC permit path, strict RSS/Atom feed-snapshot capture, immutable evidence reading and deterministic feed-item proposal extraction. These executable components must not become active merely because their classes are importable or their registries can be populated. A production feed needs one immutable governance record that pins every dependency and a read-only preflight that proves the dependency graph before lifecycle activation.

The existing provider adoption profile is already uniquely keyed by the exact immutable adapter code. Rather than adding a second profile identity and breaking that contract, a feed definition pins the SHA-256 hash of the adoption profile’s immutable configuration. The same approach is used for the strict parser profile.

## Decision

1. Introduce an immutable `FeedPipelineDefinition` identified by an exact versioned `feed_code`.
2. The immutable definition pins:
   - exact PUBLIC provider `adapter_code`;
   - exact HTTPS `external_locator`;
   - exact SHA-256 adoption configuration hash;
   - exact SHA-256 parser configuration hash;
   - exact extraction pipeline code and version;
   - exact schedule interval and maximum dispatch attempts;
   - exact acquisition configuration hash;
   - exact raw-evidence capability reference.
3. Lifecycle is explicit: `DRAFT`, `PAUSED`, `ENABLED`, `RETIRED`. `RETIRED` is terminal.
4. Definitions are create-or-get immutable. Any semantic change requires a new versioned `feed_code`.
5. Enabling a DRAFT or resuming a PAUSED definition requires a successful read-only preflight in the same service operation before lifecycle transition.
6. Preflight verifies all of the following without side effects:
   - provider capability exists, is `ENABLED` and has credential mode `PUBLIC`;
   - exact adoption profile exists for the adapter and its immutable configuration hash matches;
   - no HTTP authentication profile exists for the adapter;
   - raw-evidence store reports configured capability and exact capability reference;
   - the strict RSS/Atom definition can be constructed with the pinned parser profile and the public HTTP adapter factory can construct the exact adapter;
   - exact ingestion runtime plan exists and contains only the expected deterministic feed-item extraction stage/version;
   - schedule interval and dispatch attempts are within the existing scheduler bounds.
7. Preflight never resolves a secret, performs DNS, opens a socket, sends HTTP, writes evidence, creates a schedule, dispatches acquisition, starts an ingestion run or emits a proposal.
8. Preflight returns only bounded dependency status and reason codes. It never returns external locator, evidence reference, adoption evidence, provider response, payload or user data.
9. A failed preflight does not mutate lifecycle or the last successful verification record.
10. A successful enable/resume records the exact dependency fingerprint and verification timestamp. Re-verification with changed dependencies fails closed until a new feed definition version is created.
11. Pausing and retiring do not create or mutate scheduler records. Actual scheduler materialization remains a later explicit activation-execution slice.
12. Production composition starts with an empty feed-definition repository and therefore zero enabled feeds.
13. Add durable PostgreSQL persistence with transactional row locking for immutable create-or-get and lifecycle transitions.

## Consequences

- Parser, adapter, evidence and worker code availability cannot activate a feed.
- Every enabled definition is tied to an exact dependency graph that can be audited without revealing sensitive configuration.
- Configuration drift cannot silently reuse an old feed identity.
- A later slice may materialize schedules only from an ENABLED, successfully verified definition.

## Rejected alternatives

- Registering feed schedules directly in application startup.
- Treating successful adapter construction as sufficient activation proof.
- Running a live HTTP request during preflight.
- Allowing mutable feed records or in-place endpoint changes.
- Reusing a credentialed HTTP auth profile for a PUBLIC feed.
- Creating schedules as part of this slice.

## Non-claims

This ADR does not register a concrete feed, perform live capture, create a scheduler record, prove provider terms or production egress, automate editorial review/materialization/publication, add an Admin UI, Case Builder, Flow Composer or phone-facing feed behavior.
