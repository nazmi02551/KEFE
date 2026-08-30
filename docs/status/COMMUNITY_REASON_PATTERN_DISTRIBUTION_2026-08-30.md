# Community Reason pattern distribution — 2026-08-30

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #391  
Pull request: pending  
Capability: CAP-032 (`IMPLEMENTED_PARTIAL`)  
Stack base: PR #390 exact-green head
`448379b3f6521e821192d6dbf322012b5a41493b`

ADR: ADR-0140  
Contract: `docs/contracts/community-reason-pattern-distribution.v1.json`

## User-visible outcome

The post-Commit Community Reasons surface replaces raw tag-count chips with a
localized descriptive summary. Each ordered row shows the exact number of
currently published reasons carrying that tag over the complete readable
sample, together with a restrained determinate bar. Turkish and English copy
explains that contributions may carry several tags, so rows are not exclusive
parts of a 100% whole.

The presentation is shared by Production and Product Preview and supports
light/dark themes, compact phones, enlarged text and explicit screen-reader
semantics. Existing publish, moderation receipt, reaction and report behavior
is unchanged.

## Correctness and methodology boundary

The previous repositories counted `sample_size` over every publicly readable
reason but derived `tag_pattern_counts` only from the bounded latest-item
window. This candidate aligns both fields to the same complete readable
CaseVersion population while keeping the returned item window bounded and
latest-first.

- only `NOT_REQUIRED` and `ALLOWED` contributions participate;
- each contribution counts once per distinct raw tag;
- deterministic presentation order is count descending, then raw tag code
  ascending;
- malformed count/sample combinations fail closed in the production HTTP
  client;
- no database migration or response-shape change is introduced.

The summary is descriptive only. It is not popularity, truth, importance,
quality, agreement, recommendation, representativeness, Signal or Impact. It
contains no author identity, demographic split or inferred trait.

## Local candidate evidence

- scoped and full Ruff: PASS;
- API contract sync: PASS;
- API regressions: 576 PASS / 110 opt-in PostgreSQL skips;
- focused in-memory population/window test: PASS;
- focused existing Community Reasons HTTP behavior: PASS;
- PostgreSQL aggregate test is implemented but awaits configured CI because
  this workspace has no `KEFE_DATABASE_URL`;
- Flutter format, analyze and widget regressions await the repository-pinned CI
  toolchain because this workspace currently has no Flutter SDK.

No PASS claim is made yet. API CI, Mobile CI, MVP Beta Gates and Global
Readiness must all succeed on the same published candidate SHA. PostgreSQL and
Flutter evidence will be recorded from that exact head.

## Deferred and non-claims

CAP-032 remains `IMPLEMENTED_PARTIAL`. Trend history, demographic and
stakeholder distributions, author identity, ranking, recommendation,
representative estimation, Signal/Impact qualification, human methodology or
editorial acceptance, production SLO, store release and human usability remain
separate gates. This candidate does not update `docs/status/CURRENT.md`.

