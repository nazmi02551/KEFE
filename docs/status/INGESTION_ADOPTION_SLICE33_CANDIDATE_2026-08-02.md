# Active-Line Ingestion Adoption and Projection Bridge — Slice 33 Candidate

**Issue:** #189  
**Parent:** PR #183 / CAP-062  
**Capabilities:** CAP-055, CAP-057, CAP-058, CAP-059, CAP-061, CAP-062, CAP-065  
**Status:** candidate; exact-head CI pending

## Candidate boundary

This slice adopts the verified provider-neutral orchestration semantics from historical PR #68 onto the current active stacked line and connects its reviewed Proposal store to the existing Editorial Projection source port.

The candidate includes:

- replay-safe `IngestionRun` identity;
- append-only bounded `StageExecution` attempts;
- immutable typed `Proposal` records;
- one terminal human `ProposalReviewDecision` per proposal;
- accepted-only idempotent knowledge materialization;
- memory and PostgreSQL persistence;
- linear migration `20260802_0019 -> 20260802_0020`;
- active persistence composition;
- `IngestionReviewedProposalSource` for Candidate Case/dependency bundles;
- unit and PostgreSQL bridge tests;
- architecture fitness preserving provider neutrality and forbidding publication shortcuts.

## Preserved boundaries

This candidate does not add external source-provider calls, AI-provider calls, autonomous review, automatic Editorial Projection, Content Authoring submit/review/approval/publication, Admin queue UI, Case Builder, Flow Composer, consumer Claim Graph remapping or a second CMS.

PR #68 remains historical/excluded-stack evidence. Its domain semantics and compatible tested implementation are adopted through the current migration and composition boundaries; its stale migration parent and old delivery-line assumptions are not reused.

## Evidence rule

Do not call this slice PASS or mark CAP-055/CAP-061 verified until the exact runtime SHA succeeds in API CI, including one-head migration, orchestration and projection fitness, unit tests, PostgreSQL orchestration tests and the PostgreSQL Proposal-to-DRAFT bridge. MVP Beta Gates and Global Readiness must also succeed on the same runtime SHA.
