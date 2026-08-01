# Editorial Projection Runtime — Slice 32 Candidate

**Issue:** #182  
**Capability:** CAP-062  
**Base:** `feature/app-preferences-reliability-slice30`  
**Status:** candidate; exact-head CI pending

## Scope

This slice implements the first executable ADR-0029 boundary:

`ACCEPTED provider-neutral Candidate Case bundle -> explicit Editorial Projection command -> existing Content Authoring DRAFT + immutable projection record`

It adds:

- versioned projection profile identity;
- provider-neutral reviewed-proposal source port;
- ACCEPTED Candidate Case and dependency validation;
- explicit versioned Flow selection;
- deterministic mapping into existing Content Authoring models;
- one Candidate -> one logical DRAFT;
- idempotent replay using an immutable input hash;
- atomic PostgreSQL creation of authoring Case, DRAFT CaseVersion, lifecycle audit and projection lineage;
- in-memory and PostgreSQL tests;
- architecture fitness forbidding provider/AI dependencies and lifecycle shortcuts.

## Explicit exclusions

No provider or AI call, automatic projection, submit-for-review, approval, publication, consumer materialization, Admin UI, Case Builder, Flow Composer, bulk projection, new runtime Case class or phone UI is included.

## Evidence state

Do not call this slice PASS until the exact runtime head succeeds in API CI including migration, unit tests, architecture fitness and PostgreSQL integration.
