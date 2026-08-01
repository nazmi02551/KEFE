# KEFE Platform Foundation Completion Program

**Status:** Active execution roadmap  
**Authority:** Delivery sequencing only; does not replace Product Bible, ADRs, executable contracts or the capability portfolio.  
**Started:** 2026-08-01

## Goal

Finish the reusable platform foundations required by the accepted and statused KEFE capability portfolio before implementing later product families one by one.

"Foundation complete" does not mean every product capability is implemented. It means new product capabilities can be added through versioned configuration, bounded modules and declared ports without case-specific runtime forks, silent data-semantic changes or preview/production leakage.

## Binding rules

- Commit First, immutable published CaseVersion and generic Flow runtime remain binding.
- Every foundation slice references the CAP IDs it advances.
- Material boundaries require ADR + executable contract before runtime.
- Each slice is exact-SHA verified; CI is not human/editorial/production-provider evidence.
- A foundation lane is complete only when its exit criteria are recorded in a durable status checkpoint.
- New product features wait for the dependency lanes they require; unrelated lanes may proceed in parallel only when the stacked PR order permits.

## Execution lanes

### F0 — Delivery-line consolidation

Purpose: keep the active stacked runtime recoverable and mergeable.

Exit criteria:
- live parent/child chain remains valid;
- latest exact runtime and later docs-only heads remain separated;
- capability portfolio and CURRENT are updated at milestones;
- no child is merged before its parent.

### F1 — Server-authoritative analytics event spine

Capabilities: CAP-114, CAP-115, CAP-116, CAP-117, CAP-124.

Exit criteria:
- versioned privacy-safe analytics event registry;
- deterministic projection from authoritative domain/outbox events;
- idempotent memory and PostgreSQL stores;
- raw private reason text, response bodies and forbidden inference fields excluded;
- stable event provenance and contribution-class handling;
- architecture fitness + PostgreSQL integration evidence.

### F2 — Content ingestion and editorial projection on the active line

Capabilities: CAP-055 through CAP-065.

Exit criteria:
- PR #68 compatibility review against the active generic Flow/CaseVersion line;
- provider-neutral ingestion adopted or superseded without parallel domain models;
- accepted Candidate Case / Decision Problem / Question Draft projection creates only Content Authoring DRAFT;
- atomic idempotent projection with provenance;
- no AI/provider auto-publication.

### F3 — Admin and operational control plane

Capabilities: CAP-061, CAP-063, CAP-064, CAP-065, CAP-066, CAP-123.

Exit criteria:
- authenticated role/capability-gated Admin workflows;
- proposal/review, authoring, configuration and moderation operations;
- audit history and operational reporting;
- no second CMS or direct published CaseVersion mutation.

### F4 — Production identity, environment and operational maturity

Capabilities: CAP-073, CAP-084, CAP-085, CAP-095 and production readiness dependencies.

Exit criteria:
- real provider-neutral OTP/delivery boundary and environment configuration;
- privacy export/delete workflows;
- observability/SLO/load/runbook and operator rollback evidence paths;
- Preview remains isolated and never becomes production fallback.

### F5 — WE, Signal and Impact core runtime

Capabilities: CAP-031 through CAP-054.

Exit criteria:
- contribution classes remain separated;
- methodology-versioned Signal qualification and scope alignment;
- stakeholder gaps cannot be hidden;
- verified institutional response and Impact evidence lifecycle;
- no percentage-to-truth or unproven causality shortcut.

### F6 — Media, discovery and notification platform

Capabilities: CAP-069 through CAP-079, CAP-092 through CAP-095.

Exit criteria:
- provider-neutral production media pipeline;
- search/filter and lifecycle notifications;
- public/deep-link release decision;
- accessible and low-end Android-safe delivery.

### F7 — Commercial entitlement and catalog foundation

Capabilities: CAP-103 through CAP-107.

Exit criteria:
- provider-independent entitlement state;
- regional product/catalog semantics;
- native store verification boundary;
- no monetization launch before accepted PMF gates.

### F8 — Reporting, research and FinOps projections

Capabilities: CAP-108 through CAP-125.

Exit criteria:
- aggregate and personal report projections over governed event/decision data;
- statistical and reproducibility metadata;
- privacy thresholds and suppression;
- provider/unit-economics cost attribution without leaking sensitive user history.

## Selection rule

At the start of every new slice:
1. reread CURRENT and the capability portfolio;
2. audit incomplete P0/P1 entries;
3. select the smallest meaningful vertical slice that closes an exit criterion;
4. reference this program lane and CAP IDs in the issue/PR;
5. update this roadmap only when sequencing or exit criteria materially change.
