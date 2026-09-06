# Outcome triangle tri-axial balance engine — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #426  
Capability: CAP-102 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0169  
Contract: `docs/contracts/outcome-triangle.v1.json`

## User-visible outcome

Users can visualize the deep ethical trade-offs of their decisions via the `OutcomeTriangleCard`:
- Barycentric projection onto the three constitutional axes:
  - **Rules & Rights** (cyan-blue): Universal consistency, statutory adherence, individual rights.
  - **Empathy & Compassion** (warm coral): Protection of the vulnerable, mercy, alleviating suffering.
  - **Public Utility & Efficiency** (gold-soft): Collective good, systemic order, economic viability.
- Categorization into dominant ethical archetypes (`RIGHTS_CENTRIC`, `EMPATHY_CENTRIC`, `UTILITY_CENTRIC`, `TRI_BALANCED_HARMONY`).

Eliminates toxic binary reductions in favor of geometric ethical balance.

## Verification & Boundary

- Contract: `docs/contracts/outcome-triangle.v1.json` (PASS);
- ADR: `docs/adr/0169-outcome-triangle-tri-axial-balance-engine.md` (PASS);
- Backend triangle calculator & weight distribution tests: `services/api/tests/test_outcome_triangle.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/outcome_triangle_test.dart` (PASS);
- Barycentric sum invariant ($r+e+u=1.0$): PASS.

## Lifecycle

CAP-102 remains `ROADMAP_ACCEPTED` pending 2D barycentric interactive canvas rendering slice.
