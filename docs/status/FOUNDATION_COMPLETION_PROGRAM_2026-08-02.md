# KEFE Foundation Completion Program — 2026-08-02

**Status:** WORKING execution checkpoint  
**Issue:** #180  
**Capabilities:** CAP-055, CAP-057–065, CAP-069–073, CAP-079, CAP-084–085, CAP-092–095, CAP-103–125  
**Executable program:** `docs/contracts/foundation-completion-program.v1.json`

## Decision

KEFE infrastructure will not be treated as one vague, never-ending task. It is divided into eight evidence-backed completion waves:

1. **F0 — Delivery-line and contract convergence**
2. **F1 — Provider-neutral content supply and reviewed Proposal runtime**
3. **F2 — Editorial Projection into the existing Content Authoring DRAFT lifecycle**
4. **F3 — Admin authoring, review, moderation, media and operational reporting**
5. **F4 — Identity, privacy, production reachability, accessibility and operations**
6. **F5 — Analytics, reporting, experimentation, research export and FinOps**
7. **F6 — Methodology-qualified WE → SIGNAL → IMPACT**
8. **F7 — Entitlement, billing, B2B/research products and distribution**

A feature may begin before every wave is complete, but it may not bypass the wave that provides its required guarantees.

## Current audit finding

The highest-leverage missing delivery boundary is CAP-062:

`accepted Candidate Case + accepted dependencies → explicit Editorial Projection command → existing Content Authoring DRAFT`

ADR-0029 and `editorial-projection.v1.yaml` already lock the boundary. The active delivery line contains the existing Content Authoring aggregate and lifecycle, but it does not contain the PR #68 ingestion-orchestration runtime because PR #68 remains outside the active stack.

PR #68 therefore remains **historical implementation evidence**, not active runtime evidence. It may be adopted only after compatibility review. Wholesale merge/copy is forbidden.

## Compatibility assessment

### Reusable semantics from PR #68

- immutable `Proposal` with stable payload hash;
- terminal `ProposalReviewDecision`;
- replay-safe `IngestionRun` identity;
- append-only stage attempts;
- accepted-only materialization ledger;
- provider-neutral ports;
- isolated PostgreSQL `ingestion` schema;
- no provider/AI authority over acceptance or publication.

### Active-line authority that must win

- current Content Authoring models, repository and lifecycle;
- current typed Questions and generic Flow runtime;
- current configuration/Flow pinning rules;
- current Admin identity/capability boundary;
- current migrations and error registry;
- active-stack exact-SHA CI requirements;
- current Preview/production isolation.

### Adoption rule

The first runtime implementation must introduce or adapt only the minimum source/review port required by ADR-0029. It must not silently import old persistence builders, migration ordering, error versions or stale aggregate assumptions.

## Next runtime slice

**CAP-062 — Editorial Projection runtime, first executable ADR-0029 slice**

Required behavior:

- versioned `EditorialProjectionProfile`;
- explicit authenticated command and idempotency key;
- accepted Candidate Case and dependency validation;
- deterministic mapping to existing Authoring Case/CaseVersion/Issue/Question models;
- explicit Flow selection, never title/domain/provider inference;
- immutable projection record;
- atomic DRAFT + projection record persistence;
- memory and PostgreSQL adapters;
- retry/idempotency/concurrency tests;
- architecture test proving no automatic submit/review/approve/publish;
- no provider SDK, AI call, consumer table write or new Case subtype.

## Evidence discipline

This checkpoint does **not** mark CAP-055 or CAP-062 complete. It makes their adoption order and completion criteria executable. Runtime PASS still requires contract-appropriate exact-SHA evidence.

No new APK is warranted because this checkpoint changes no phone runtime.

## Accidental no-op cleanup note

During branch setup, a temporary placeholder was repeatedly added and removed on PR #173's branch. The final branch has no net file difference from those placeholders. PR #173's verified runtime remains `e41cea5fc7bccb4bbe085b48cd15ea5a2fead082`; later branch heads are documentation/no-op history only and must not be treated as new runtime evidence.
