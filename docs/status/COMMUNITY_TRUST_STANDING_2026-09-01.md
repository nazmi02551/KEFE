# Status Record: Community Trust Score & Contribution Standing (CAP-070)

**Date:** 2026-09-01  
**Capability ID:** `CAP-070`  
**Status:** `IMPLEMENTED_VERIFIED`  
**Phase:** Phase 4  
**Priority:** P1  

## Delivered Artifacts
- **ADR:** `docs/adr/0203-community-trust-standing.md`
- **Contract:** `docs/contracts/community-trust-standing.v1.json`
- **Backend Service:** `services/api/src/kefe_api/modules/decision/community_trust_standing.py` (`CommunityTrustCalculator`)
- **Backend Tests:** `services/api/tests/test_community_trust_standing.py`
- **Mobile Domain:** `apps/mobile/lib/features/decision/domain/community_trust_standing_models.dart`
- **Mobile Presentation:** `apps/mobile/lib/features/decision/presentation/community_trust_standing_card.dart`
- **Localization:** TR and EN keys in `internal_alpha_string_catalog.dart` & `internal_alpha_strings.dart`
- **Mobile Tests:** `apps/mobile/test/community_trust_standing_test.dart`
