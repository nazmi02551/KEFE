# Fairness and normative models comparison engine — 2026-09-01

Status: IMPLEMENTATION CANDIDATE / EXACT-HEAD CI PENDING / NO CAPABILITY PROMOTION

Issue: #432  
Capability: CAP-019 (`ROADMAP_ACCEPTED`)  
Stack base: `feature/insufficient-info-response` (`e665ec9b`)

ADR: ADR-0175  
Contract: `docs/contracts/fairness-normative-models.v1.json`

## User-visible outcome

Users can visualize the normative philosophical foundations of their decisions via `NormativeModelsCard`:
- Multi-dimensional scoring across the four cornerstone philosophical paradigms:
  - `UTILITARIAN_MAX_WELFARE` (Utilitarianism / Bentham & Mill)
  - `DEONTOLOGICAL_CATEGORICAL_RIGHTS` (Deontology & Human Rights / Kant)
  - `RAWLSIAN_MAXIMIN_EQUITY` (Distributive Equity / Rawls)
  - `VIRTUE_ETHICS_CHARACTER` (Virtue Ethics / Aristotle)
- Non-dogmatic, pluralistic comparative analysis deepening civic philosophical awareness.

## Verification & Boundary

- Contract: `docs/contracts/fairness-normative-models.v1.json` (PASS);
- ADR: `docs/adr/0175-fairness-and-normative-models-comparison-engine.md` (PASS);
- Backend normative evaluator & four-framework scoring tests: `services/api/tests/test_normative_models.py` (PASS);
- Mobile presentation card & domain model tests: `apps/mobile/test/normative_models_test.dart` (PASS);
- Four philosophical traditions invariant: PASS.

## Lifecycle

CAP-019 remains `ROADMAP_ACCEPTED` pending case authoring pipeline calibration of ethical baseline scores.
