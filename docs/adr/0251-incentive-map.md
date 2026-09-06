# ADR-0251: Incentive Map Engine (CAP-022)

## Status

ACCEPTED

## Context

Decisions and public policies are fundamentally steered by the underlying institutional and economic incentives of the participating actors. Even well-intentioned regulatory interventions frequently unravel due to incentive misalignments, regulatory capture, or perverse incentives (where an intervention inadvertently rewards behavior that amplifies the dilemma).

In accordance with `KEFE-PB-001` (Product Bible) and `KEFE-CQB-001` (Content & Question Design Bible), deliberative democracy requires examining the invisible incentive structures behind a dilemma:
1. Stakeholder Categorization: Commercial providers, political officials, bureaucratic administrators, consumers, and civic communities.
2. Incentive Typology:
   - `FINANCIAL_PROFIT`: Margin expansion, cost minimization, shareholder returns.
   - `POLITICAL_ELECTORAL`: Short-term poll bumps, electoral coalition preservation.
   - `BUREAUCRATIC_RISK_AVERSION`: Status quo preservation, blame shifting, avoidance of procedural scrutiny.
   - `CIVIC_PUBLIC_WELFARE`: Public health, ecological preservation, affordability, long-term civic stability.
3. Alignment Status:
   - `ALIGNED`: When private self-interest naturally advances public benefit.
   - `MISALIGNED`: When private self-interest works at cross-purposes with public welfare.
   - `PERVERSE`: When the intervention creates unintended economic or political rewards for worsening the harm.
4. Structural Mitigations: Clear governance mechanisms (transparency mandates, clawbacks, independent verification) to realign incentives with public interest.

## Decision

1. **Incentive Topology & Alignment Index**:
   - Compute a comprehensive `IncentiveMap` per case version with an `alignment_index` $[0.0, 1.0]$.
   - Quantify `perverse_incentive_risk` (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`) with explicit identification of primary drivers.
   - Detail the specific mitigation mechanisms that can structurally alter incentives.

2. **API Specification**:
   - Expose `GET /v1/cases/{case_version_id}/incentive-map` returning the complete incentive topology, alignment ratings, and risk levels.

3. **Mobile Presentation**:
   - Render `IncentiveMapCard` within the post-commit analytical perspective suite and case explorer, providing visual node intensity bars, alignment status badges, and systemic mitigation guidance.

## Consequences

- Transforms simplistic moralistic finger-pointing into systemic, institutional understanding.
- Protects civic deliberations from superficial rhetoric by exposing economic and political incentives.
- Adheres strictly to KEFE constitutional invariants: Commit First, descriptive non-normative reporting, and zero psychometric bias.
