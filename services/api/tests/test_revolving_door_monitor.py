from __future__ import annotations

from kefe_api.modules.decision.revolving_door_monitor import (
    RevolvingDoorMonitorService,
    RevolvingDoorResult,
    TransitionStatus,
)


def test_revolving_door_audits_compliant_transition() -> None:
    r = RevolvingDoorMonitorService.audit_transition(
        transition_id="rvl_001",
        official_name_anonymized="Eski BDDK Kurul Üyesi #A8",
        cooling_off_months_observed=36,
        capture_risk_score=0.10,
        regulatory_agency_source="Bankacılık Düzenleme ve Denetleme Kurumu",
    )

    assert isinstance(r, RevolvingDoorResult)
    assert r.status == TransitionStatus.COOLING_OFF_COMPLIANT
    assert r.cooling_off_months_observed == 36
    assert r.capture_risk_score == 0.10


def test_revolving_door_invalid_inputs() -> None:
    failed = False
    try:
        RevolvingDoorMonitorService.audit_transition(
            transition_id="rvl_002",
            official_name_anonymized="Test",
            cooling_off_months_observed=-1,  # < 0
            capture_risk_score=1.50,  # > 1.0
            regulatory_agency_source="AB",  # < 3
        )
    except ValueError:
        failed = True

    assert failed is True
