# ADR-0013 — Content authoring and publication boundary

**Status:** Accepted  
**Date:** 2026-07-28

## Context

KEFE now has a consumer walking skeleton with immutable CaseVersion decisions, Context/Sources, typed Questions, private Reason, Commit-gated Reveal/Perspective and actor-scoped Progress. The next foundation is an editorial/content boundary that can create and review Case, Issue, Question, Context and Source structures without allowing mutable drafts to leak into the consumer read path.

The approved product documents require an Admin Studio, publication workflow, CaseVersion audit trail, configurable taxonomy and source/claim review. Final admin UI, organization roles and production authentication are not yet authorized for implementation. Therefore the first slice must establish domain/application contracts without exposing an insecure public admin endpoint or locking a vendor-specific CMS.

## Decision

- Content authoring is a separate capability from consumer Case reads and decision writes.
- A stable Case identity may have many draft/review versions, but at most one consumer-visible `PUBLISHED` version.
- Published CaseVersion content is immutable. Editorial changes create a new version.
- Draft lifecycle is `DRAFT → IN_REVIEW → APPROVED → PUBLISHED`; rejection returns the same version to `DRAFT` with an audit entry.
- A publish command must validate the complete aggregate: Case metadata, at least one Issue, at least one active Question, Context requirements and Source/claim requirements appropriate to risk/configuration.
- Publication supersedes the previously published version atomically but does not delete it.
- Consumer repositories continue reading only published immutable versions.
- Every lifecycle command records actor reference, timestamp, command, previous/new state and optional rationale in an append-only audit trail.
- Taxonomy codes, formats, risk levels, claim states and compatibility rules are validated through configuration/registries rather than hard-coded UI branches.
- No public HTTP authoring endpoint is introduced in this slice. The application boundary and repository port are implemented first; production admin authentication/authorization requires a separate threat-model ADR.
- External CMS or workflow providers may later implement the same port. Domain rules remain provider-independent.

## Consequences

- Consumer reads cannot observe partially edited content.
- Editorial corrections preserve the exact CaseVersion seen by existing decisions.
- Admin UI and authentication can evolve independently from publication invariants.
- Publication validation failures become stable machine-readable domain outcomes.
- The initial implementation may use an in-memory adapter and domain tests; PostgreSQL persistence and authenticated Admin API can follow as separate coherent slices.
