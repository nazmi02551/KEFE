# ADR-0254: Expert-Public Gap Analysis Engine (CAP-041)

## Status

ACCEPTED

## Context

A central challenge in contemporary democratic governance (`KEFE-PB-001`, `KEFE-RM-001`, `KEFE-CGD-001`) is the epistemic tension between specialized domain expertise and general civic deliberation:
- **Technocratic Distortion**: When scientific or economic experts dismiss public concern as irrational or uneducated, democracy degenerates into technocracy.
- **Populist Anti-Intellectualism**: When the public rejects empirical evidence and peer-reviewed consensus due to institutional cynicism or misinformation, policies risk catastrophe.

In accordance with KEFE constitutional invariants, the platform does not treat experts as unquestionable moral authorities nor does it treat public intuition as infallible truth. Instead, KEFE makes the **Expert-Public Gap** visible, structured, and auditable:

1. **Certified Expert Cohort**: Domain specialists with verified academic, clinical, technical, or legal credentials ($n \ge 30$).
2. **Civic Public Sample**: Broad population participating in post-commit deliberation ($n \ge 100$).
3. **Epistemic Gap Classification**:
   - `CONVERGENT` ($\Delta \le 10$ pts): Shared technical and normative alignment between specialists and the public.
   - `TECHNICAL_TRANSLATION_GAP` ($11 \le \Delta \le 25$ pts): Public skepticism caused primarily by complex jargon, risk perception asymmetry, or opaque communication, while underlying values align.
   - `NORMATIVE_VALUE_DIVERGENCE` ($\Delta > 25$ pts): Agreement on the physical or economic facts, but fundamental disagreement on ethical tradeoffs (e.g. collective safety vs individual privacy, economic efficiency vs cultural preservation).
   - `TRUST_DEFICIT_SKEPTICISM`: Institutional skepticism toward certifying bodies overriding empirical findings.
4. **Epistemic Reconciliation Bridges**: Specific framing, trade-off questions, and open-methodology disclosures that bridge the gap without coercive persuasion.

## Decision

1. **Contract & Schema**:
   - Author `docs/contracts/expert-public-gap.v1.json` (`KEFE-EXPERT-PUBLIC-GAP-001`).
   - Define `ExpertPublicGapAnalysis` capturing sample sizes, distributions, gap points, classification, divergence drivers, and epistemic bridges.

2. **Backend Engine & API**:
   - Implement `ExpertPublicGapService` in `services/api/src/kefe_api/modules/decision/expert_public_gap.py`.
   - Expose `GET /v1/cases/{case_version_id}/expert-public-gap` returning the epistemic gap assessment.

3. **Mobile Client Presentation**:
   - Create `ExpertPublicGapCard` and domain models in `apps/mobile/lib/features/decision/`.
   - Render comparative distribution bars (Expert vs Public), gap magnitude badge, classification pill, divergence drivers, and deliberative bridge recommendations.

## Consequences

- Replaces mutual contempt between technocrats and the public with transparent epistemic deliberation.
- Upholds KEFE invariants: Commit First, descriptive reporting, and zero psychometric profiling.
- Fulfills the Phase 8 roadmap milestone `CAP-041`.
