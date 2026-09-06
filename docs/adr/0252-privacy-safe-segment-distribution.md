# ADR-0252: Privacy-Safe Segment Distribution (CAP-036)

## Status

ACCEPTED

## Context

A fundamental goal of the KEFE deliberative framework (`KEFE-TIM-001` and `KEFE-PB-001`) is to make visible how different societal cohorts experience and weigh complex dilemmas. Without segment breakdown, collective opinion risks appearing as an undifferentiated monolith, masking distinct generational, regional, or lived-experience perspectives.

However, granular demographic breakdowns pose severe privacy and ethical risks (`KEFE-SEC-001`):
1. **Re-identification & De-anonymization Risk**: In small communities or niche dilemmas, cross-referencing narrow demographic attributes can unmask individual citizens' votes, directly violating the secret ballot / private deliberation principle.
2. **Invasive Profiling & Micro-Targeting**: Commercial platforms build psychometric dossiers on citizens. KEFE explicitly prohibits individual psychometric, ideological, or behavioral profiling.
3. **Statistical Noise & Misleading Generalizations**: Subgroups with negligible sample sizes produce erratic percentages that distort public understanding.

To solve this, KEFE enforces strict mathematical and architectural privacy guardrails:
- **$k$-Anonymity Floor ($n \ge 30$)**: Any demographic cohort with fewer than 30 committed participants is automatically suppressed (`is_suppressed=true`), withholding option distributions to guarantee individual anonymity.
- **Differential Privacy & Noise Floor**: Aggregate shares include bounded differential privacy noise to prevent reconstruction attacks.
- **Coarse Demographic & Contextual Cohorts Only**: Attributes are strictly grouped into broad, non-invasive cohorts (`AGE_COHORT`, `URBAN_RURAL_COHORT`, `EXPERIENCE_LEVEL`, `REGIONAL_COHORT`, `STAKEHOLDER_ROLE`).
- **Post-Commit Only**: In accordance with the Commit First invariant, segment distributions are accessible exclusively after the user has committed their own decision.

## Decision

1. **Contract & Schema**:
   - Establish `docs/contracts/segment-distribution.v1.json` (`KEFE-SEGMENT-DISTRIBUTION-001`).
   - Define `PrivacySafeSegmentDistribution` with `minimum_sample_threshold = 30`, cohort-level suppression flags, option distributions, and entropy score.

2. **Backend Engine & API**:
   - Implement `PrivacySafeSegmentDistributionService` in `services/api/src/kefe_api/modules/decision/segment_distribution.py`.
   - Expose `GET /v1/cases/{case_version_id}/segment-distributions` returning the privacy-gated distribution.

3. **Mobile Client Presentation**:
   - Create `SegmentDistributionCard` and domain models in `apps/mobile/lib/features/decision/`.
   - Render cohort chips, privacy badges ("k >= 30 Korumalı"), distribution bars for non-suppressed cohorts, and respectful privacy-suppression placeholders for sub-threshold cohorts.

## Consequences

- Delivers rich societal insight into how different life experiences shape perspectives without compromising individual privacy.
- Preserves KEFE's constitutional guarantees: Commit First, zero psychometric profiling, and cryptographic privacy preservation.
- Meets Apple App Store and Google Play privacy criteria for anonymized civic research.
