# ADR-0256: Contribution Classes Separation (CAP-043)

## Status
ACCEPTED

## Context
A cornerstone of KEFE's constitutional integrity (`KEFE-TIM-001`, `KEFE-RM-001`) is the strict segregation of participant contribution classes. In traditional web polls or social platforms, pre-result organic votes, post-poll bandwagon reactions, and directed activist campaigns are lumped into a single headline number. This creates cognitive herd behavior, feedback loops, and vulnerability to organized mobilization campaigns.

To preserve the invariant `CONTRIBUTION_CLASSES_NEVER_SILENTLY_MIXED`, the deliberation and signal pipelines must enforce three mutually exclusive contribution classes:
1. `CORE_PRE_RESULT`: Blind-first commitments executed before any aggregate results or other perspectives are displayed. This is the **only** class eligible for primary civic signal generation.
2. `EXPOSED`: Post-reveal or post-perspective interactions, measuring shift-of-mind, reflective deliberation, and mind-change. Valuable for epistemic analysis, but barred from mutating the pristine core baseline.
3. `ADVOCACY_SUPPORT`: Community action co-signing, petition endorsements, and stakeholder follow-through (`CAP-052/053/054`). Measures civic mobilization and action intent, segregated from organic deliberation.

## Decision
1. Formalize the **Contribution Classes Separation Engine** (`KEFE-CONTRIBUTION-CLASSES-001`):
   - Categorize all weigh sessions and deliberation interactions strictly into `CORE_PRE_RESULT`, `EXPOSED`, or `ADVOCACY_SUPPORT`.
   - Calculate participant counts, percentage distributions, and signal eligibility flags for each cohort.
   - Enforce a zero-tolerance `contamination_risk_index` (0.0 to 1.0; 0.0 indicates perfect isolation) and an `isolation_audit_status` (`ENFORCED` vs `BREACH_DETECTED`).
   - Generate a deterministic SHA-256 `isolation_proof_hash` guaranteeing that no post-reveal or advocacy interactions contaminated the core signal.

2. Expose the breakdown through `GET /v1/signals/{signal_id}/contribution-classes` (and `GET /v1/cases/{case_version_id}/contribution-classes`).
3. Build the Flutter presentation widget (`ContributionClassesCard`) visualizing the 3 segmented cohorts, their proportional share, and the isolation audit guarantee.

## Consequences
- Protects democratic signal integrity from bandwagon effects and organized campaign brigading.
- Retains rich epistemic value by analyzing `EXPOSED` (shift-of-mind) and `ADVOCACY_SUPPORT` (action) without corrupting the pristine core baseline.
