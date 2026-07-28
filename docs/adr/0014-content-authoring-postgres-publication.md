# ADR-0014 — PostgreSQL authoring persistence and publication materialization

**Status:** Accepted  
**Date:** 2026-07-28

## Context

ADR-0013 established a provider-neutral Content Authoring lifecycle while deliberately withholding any public Admin HTTP surface. The consumer database already contains immutable published CaseVersion read models used by Explore, Context, Weigh and historical decisions. Persisting mutable editorial drafts directly into those consumer tables would enlarge the draft-leakage surface and make publication boundaries harder to prove.

The durable adapter therefore needs to preserve two different concerns: mutable editorial workflow state and immutable consumer-visible publication state.

## Decision

- Mutable authoring state is persisted under a dedicated PostgreSQL `editorial` schema behind `ContentAuthoringRepository`.
- The authoring aggregate is stored as a versioned JSONB document plus indexed lifecycle metadata. This is an infrastructure representation; the domain remains typed and vendor-neutral.
- The consumer `content` schema remains the published read model. Draft, review and approved authoring aggregates are never materialized there.
- Publishing is one PostgreSQL transaction that:
  1. locks the target editorial CaseVersion and verifies the expected `APPROVED` state,
  2. locks the stable Case publication set,
  3. supersedes any previously published editorial and consumer CaseVersion,
  4. materializes the approved aggregate into immutable consumer Case/Issue/Question/Context/Source rows using the same CaseVersion identity,
  5. updates stable consumer Case routing metadata,
  6. appends lifecycle audit records,
  7. marks the target editorial version `PUBLISHED`.
- Consumer CaseVersion rows receive version-owned `base_format_code`, `primary_domain_code` and `content_risk` fields. Existing rows are backfilled from `content.case_item`; consumer reads move to the version-owned fields so historical metadata cannot drift when a newer revision publishes.
- Published authoring aggregates cannot be edited. Corrections create a new editorial CaseVersion and new version-owned nested IDs.
- Public Context reads may return only consumer materialized `PUBLISHED` or `SUPERSEDED` CaseVersions; mutable editorial states cannot be observed by guessing an ID.
- No Admin HTTP endpoint is added by this decision. Authentication, authorization and threat modeling remain a separate prerequisite.

## Consequences

- A database-level boundary separates mutable editorial work from consumer publication.
- Publication and supersede are atomic across authoring lifecycle, consumer materialization and audit.
- Historical decisions retain the exact version-owned format/domain/risk and content they saw.
- The JSONB authoring representation can later be replaced by a more normalized editorial store without changing application/domain ports.
- Consumer read models stay optimized independently of editorial workflow complexity.
