# KEFE Platform Foundation Completion Program

**Status:** Active execution roadmap  
**Authority:** Delivery sequencing only; does not replace Product Bible, ADRs, executable contracts or the capability portfolio.  
**Parent issue:** #177  
**Started:** 2026-08-01

## Goal

Finish the reusable platform foundations required by the accepted and statused KEFE capability portfolio before implementing later product families one by one.

"Foundation complete" does not mean every product capability is implemented. It means new capabilities can be added through versioned configuration, bounded modules and declared ports without case-specific runtime forks, silent semantic changes or Preview/production leakage.

## Binding rules

- Commit First, immutable published CaseVersion and generic Flow runtime remain binding.
- Every foundation slice references the CAP IDs it advances.
- Material boundaries require ADR + executable contract before runtime.
- Each slice is exact-SHA verified; CI is not human/editorial/production-provider evidence.
- A lane closes only when its exit criteria are recorded in a durable status checkpoint.
- New product features wait for the foundation lanes they depend on.

## Execution lanes

### F0 — Delivery-line consolidation

Keep the active stacked runtime recoverable and mergeable. Never merge a child before its parent; keep exact runtime and later docs-only heads separate.

### F1 — Server-authoritative analytics event spine

Capabilities: CAP-114, CAP-115, CAP-116, CAP-117, CAP-124.

Exit criteria:
- versioned privacy-safe event registry;
- deterministic projection from authoritative domain/outbox events;
- idempotent memory and PostgreSQL stores;
- raw response/private-reason and forbidden inference fields excluded;
- contribution-class provenance preserved when available;
- architecture fitness, unit and PostgreSQL evidence.

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

Exit criteria: authenticated role/capability-gated review, authoring, configuration, moderation, audit and operational-report workflows without a second CMS.

### F4 — Production identity, privacy, environment and operations

Capabilities: CAP-073, CAP-084, CAP-085, CAP-095 plus production-readiness dependencies.

Exit criteria: provider-neutral production delivery boundaries, privacy export/delete, observability/SLO/load/runbook evidence paths and operator rollback controls. Preview remains isolated.

### F5 — WE, Signal and Impact core runtime

Capabilities: CAP-031 through CAP-054.

Exit criteria: contribution-class separation, methodology-versioned Signal qualification, scope alignment, visible stakeholder gaps, verified institution response and Impact evidence without percentage-to-truth or causality shortcuts.

### F6 — Media, discovery and notification platform

Capabilities: CAP-069 through CAP-079 and CAP-092 through CAP-095.

Exit criteria: provider-neutral media delivery, search/filter, lifecycle notifications, explicit public-web/deep-link release decision and accessible low-end Android behavior.

### F7 — Commercial entitlement and catalog foundation

Capabilities: CAP-103 through CAP-107.

Exit criteria: provider-independent entitlement state, regional product/catalog semantics and native-store verification boundary. No monetization launch before accepted PMF gates.

### F8 — Reporting, research and FinOps projections

Capabilities: CAP-108 through CAP-125.

Exit criteria: governed personal/aggregate/research/operational projections, statistical/reproducibility metadata, privacy thresholds/suppression and provider/unit-economics attribution.

## Selection rule

At the start of every new slice:
1. reread CURRENT and the capability portfolio;
2. audit incomplete P0/P1 entries;
3. select the smallest meaningful vertical slice that closes a lane exit criterion;
4. reference this program lane and CAP IDs in the issue/PR;
5. update this roadmap only when sequencing or exit criteria materially change.
