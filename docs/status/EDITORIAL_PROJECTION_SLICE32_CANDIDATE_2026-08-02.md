# Editorial Projection Runtime — Slice 32 Verification

**Issue:** #182  
**Capability:** CAP-062  
**Base:** `feature/app-preferences-reliability-slice30`  
**Verified runtime SHA:** `6a984431b29fe7b9978eb72565f3b531b299c82e`  
**Status:** bounded first executable ADR-0029 slice — PASS

## Verified boundary

This slice implements and verifies:

`ACCEPTED provider-neutral Candidate Case bundle -> explicit Editorial Projection command -> existing Content Authoring DRAFT + immutable projection record`

The runtime includes:

- versioned `EditorialProjectionProfile` identity;
- provider-neutral reviewed-Proposal source port;
- terminal ACCEPTED Candidate Case and dependency validation;
- explicit versioned Flow selection with no title/domain/provider inference;
- deterministic mapping into the existing Content Authoring aggregate;
- one Candidate Case -> one logical DRAFT invariant;
- immutable input hash and idempotent replay;
- concurrent same-key conflict recovery as replay;
- atomic PostgreSQL creation of authoring Case, DRAFT CaseVersion, lifecycle audit and projection lineage;
- linear migration `20260730_0018 -> 20260802_0019`;
- in-memory, concurrency and PostgreSQL tests;
- architecture fitness forbidding provider/AI dependencies and lifecycle shortcuts.

## Exact-SHA evidence

### API CI — SUCCESS

Run `30724097085`:

- lint/unit job `91432549533` — SUCCESS;
- PostgreSQL integration job `91432604359` — SUCCESS;
- migration to one head — SUCCESS;
- Editorial Projection contract fitness — SUCCESS;
- unit and concurrency tests — SUCCESS;
- PostgreSQL projection/atomicity test — SUCCESS;
- OpenAPI drift gate — SUCCESS.

### MVP Beta Gates — SUCCESS

Run `30724097088`:

- API contract job `91432549518` — SUCCESS;
- mobile job `91432549557` — SUCCESS;
- PostgreSQL job `91432608311` — SUCCESS;
- mobile format/analyze/accessibility/locale/theme/regression tests — SUCCESS;
- production-entry APK build — SUCCESS;
- one-head migration and MVP continuity/privacy checks — SUCCESS.

### Global Readiness — SUCCESS

Run `30724097086`:

- API global job `91432549608` — SUCCESS;
- phone-candidate job `91432549618` — SUCCESS;
- PostgreSQL global job `91432549624` — SUCCESS;
- production-copy boundary, phone acceptance and mobile regressions — SUCCESS;
- internal phone candidate build/upload — SUCCESS;
- global-head migration and existing PostgreSQL regression — SUCCESS.

A separate Mobile CI workflow was not triggered by this backend-only path set. Mobile coverage was nevertheless executed successfully inside both MVP Beta Gates and Global Readiness. No phone-facing behavior changed, so the generated artifacts are regression evidence and are not a new user APK release.

## Rejected or superseded candidates

The following SHAs are not PASS:

- `9c541d6a4970f89af8ac7c1ea57b086d52bdcafc` — error codes were not registered;
- `03d351bf64923f7ce1cb0bdc2f00574dbe913795` — migration created multiple Alembic heads;
- `82737b3e69c5c0a7b9f03c114616dab3d5841420` — migration still branched before global metadata;
- `d120c7d1d9168f669a1575f5ce6f8769bab0e632` — API/PostgreSQL passed but was superseded before final verification to close the concurrent replay gap.

## Explicit exclusions and remaining gates

This slice does not include:

- a production adapter for the excluded-stack PR #68 Proposal store;
- external provider or AI calls;
- automatic projection after Proposal acceptance;
- automatic submit-for-review, approval or publication;
- consumer materialization;
- an Admin HTTP command surface or Admin UI;
- Case Builder, Flow Composer or bulk projection;
- new runtime Case classes;
- human editorial usability/acceptance evidence;
- production provider, deployed SLO or operator rollback evidence.

Therefore this record proves the first executable CAP-062 domain and persistence slice. It does not claim the full content-supply foundation, production editorial operation or all of CAP-062's downstream integrations are complete.
