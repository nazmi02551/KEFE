from __future__ import annotations

from kefe_api.modules.decision.democratic_emergency_safeguard import (
    DemocraticEmergencyResult,
    DemocraticEmergencySafeguardService,
    EmergencySafeguardStatus,
)


def test_emergency_safeguard_audits_decree() -> None:
    r = DemocraticEmergencySafeguardService.audit_emergency_decree(
        decree_id="emg_001",
        emergency_jurisdiction="Deprem Afet Bölgesi Geçici İskan Kararnamesi",
        proportionality_score=0.94,
        remaining_sunset_days=45,
    )

    assert isinstance(r, DemocraticEmergencyResult)
    assert r.safeguard_status == EmergencySafeguardStatus.PROPORTIONATE_SUNSET_BOUNDED
    assert r.proportionality_score == 0.94
    assert r.remaining_sunset_days == 45


def test_emergency_safeguard_invalid_inputs() -> None:
    failed = False
    try:
        DemocraticEmergencySafeguardService.audit_emergency_decree(
            decree_id="emg_002",
            emergency_jurisdiction="AB",  # < 3
            proportionality_score=1.5,  # > 1.0
            remaining_sunset_days=-5,  # < 0
        )
    except ValueError:
        failed = True

    assert failed is True
