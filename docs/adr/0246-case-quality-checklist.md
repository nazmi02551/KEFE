# ADR-0246: Case Quality Checklist Instead of Magic Score (CAP-075)

## Status
ACCEPTED

## Context
In public discourse platforms and automated content systems, editorial quality is frequently collapsed into an opaque scalar metric (e.g., "Quality Score: 8.4/10"). Such scores obscure underlying biases, lack auditability, and create misleading impressions of mathematical objectivity.

KEFE's constitutional foundation (`KEFE-CQB-001`, `KEFE-ADM-001`, `KEFE-TIM-001`) rejects black-box scoring in favor of transparent, multidimensional checklists where every criterion is explicitly inspectable and auditable by consumers.

## Decision
1. Replace single composite scores with an 8-point **Case Quality Checklist**:
   - `BALANCED_OPTIONS`
   - `NEUTRAL_PROVENANCE`
   - `DISCLOSED_STAKEHOLDERS`
   - `VERIFIED_SOURCES`
   - `ACCESSIBLE_READABILITY`
   - `PRINCIPLE_INTEGRITY`
   - `REASON_PROMPT_EQUITY`
   - `METHODOLOGY_TRANSPARENCY`
2. Every item carries an audit state (`VERIFIED`, `PENDING`, `FLAGGED`) and editorial reviewer rationale.
3. Expose the checklist through a governed API endpoint: `GET /v1/cases/{case_version_id}/quality-checklist`.
4. Provide a mobile modal/sheet (`CaseQualityChecklistSheet`) allowing consumers to examine why and how a case meets constitutional quality standards.

## Consequences
- No opaque algorithmic ranking.
- Complete editorial transparency and auditability.
- Consumers can challenge items through `CAP-068` (Case Objection mechanism).
