# Status Record: Depolarization & Bridge Efficacy Index (CAP-117)

**Date:** 2026-09-01  
**Capability ID:** `CAP-117`  
**Status:** `IMPLEMENTED_VERIFIED`  
**Phase:** Phase 4  
**Priority:** P1  

## Delivered Artifacts
- **ADR:** `docs/adr/0204-depolarization-index.md`
- **Contract:** `docs/contracts/depolarization-index.v1.json`
- **Backend Service:** `services/api/src/kefe_api/modules/decision/depolarization_index.py` (`DepolarizationCalculator`)
- **Backend Tests:** `services/api/tests/test_depolarization_index.py`
- **Mobile Domain:** `apps/mobile/lib/features/decision/domain/depolarization_index_models.dart`
- **Mobile Presentation:** `apps/mobile/lib/features/decision/presentation/depolarization_index_card.dart`
- **Localization:** TR and EN keys in `internal_alpha_string_catalog.dart` & `internal_alpha_strings.dart`
- **Mobile Tests:** `apps/mobile/test/depolarization_index_test.dart`
