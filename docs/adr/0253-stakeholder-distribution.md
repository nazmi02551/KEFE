# ADR-0253: Stakeholder Distribution Engine (CAP-037)

## Status

ACCEPTED

## Context

In complex socio-technical and institutional dilemmas (`KEFE-TIM-001`, `KEFE-RM-001`, and `signal-impact-model.v1.yaml`), raw majority vote tallies frequently conceal deep asymmetric fractures among different stakeholder ecosystems. 

While `CAP-038` (Stakeholder Gap Disclosure) alerts citizens when a directly impacted minority's preference diverges sharply from the general public, `CAP-037` (Stakeholder Distribution) establishes the comprehensive, multi-party stakeholder topology across the five canonical democratic roles:
1. **Directly Impacted Citizens (`DIRECTLY_IMPACTED`)**: Individuals whose personal liberty, physical environment, livelihood, or safety are immediately subject to the outcome.
2. **Frontline Practitioners (`FRONTLINE_PRACTITIONERS`)**: Professionals on the ground implementing or executing the policies (e.g., healthcare workers, teachers, technical operators).
3. **Commercial & Economic Operators (`COMMERCIAL_ENTERPRISES`)**: Business enterprises, market participants, and employers bearing capital costs, regulatory burdens, or competitive disruption.
4. **Regulatory & Institutional Oversight (`REGULATORY_OVERSIGHT`)**: Administrative agencies, legal authorities, and independent ombudsmen charged with compliance and systemic stability.
5. **Civic & Public Community (`CIVIC_COMMUNITY`)**: Broader civil society, adjacent citizens, and long-term public interest advocates.

Without this multi-stakeholder distribution:
- Deliberations suffer from false consensus assumptions.
- Technical, regulatory, and frontline feasibility concerns are overshadowed by generic popular sentiment.
- Policymakers lack visibility into which specific institutional or community groups need bridge-building or transitional accommodations.

## Decision

1. **Contract & Schema**:
   - Author `docs/contracts/stakeholder-distribution.v1.json` (`KEFE-STAKEHOLDER-DISTRIBUTION-001`).
   - Define `StakeholderDistribution` capturing total representation, per-category sample counts and shares, option preference distributions, internal cohesion indices, and percentage-point divergence from overall collective choices.

2. **Backend Engine & API**:
   - Implement `StakeholderDistributionService` in `services/api/src/kefe_api/modules/decision/stakeholder_distribution.py`.
   - Expose `GET /v1/cases/{case_version_id}/stakeholder-distributions` returning the full multi-stakeholder breakdown.

3. **Mobile Client Presentation**:
   - Create `StakeholderDistributionCard` and domain models in `apps/mobile/lib/features/decision/`.
   - Render stakeholder category badges, representation progress bars, internal cohesion scores, and option breakdown bars.

## Consequences

- Elevates civic discourse from superficial majority polarization to nuanced multi-party institutional analysis.
- Complies strictly with KEFE core invariants: Commit First, descriptive non-normative summaries, and cryptographic non-profiling privacy.
- Satisfies the `STAKEHOLDER_DISTRIBUTION` minimum dimension required for methodology-qualified Signal (`signal-impact-model.v1.yaml`).
