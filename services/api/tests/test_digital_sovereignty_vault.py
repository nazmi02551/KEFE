from __future__ import annotations

from kefe_api.modules.decision.digital_sovereignty_vault import (
    DigitalSovereigntyResult,
    DigitalSovereigntyTier,
    DigitalSovereigntyVaultService,
)


def test_digital_sovereignty_audits_enforced_residency() -> None:
    r = DigitalSovereigntyVaultService.audit_sovereignty(
        vault_id="vlt_001",
        jurisdiction_region="TR-Marmara Sovereign Enclave",
        local_residency_pct=1.00,
        exfiltration_threat_score=0.01,
    )

    assert isinstance(r, DigitalSovereigntyResult)
    assert r.sovereignty_tier == DigitalSovereigntyTier.SOVEREIGN_RESIDENCY_ENFORCED
    assert r.local_residency_pct == 1.00
    assert r.exfiltration_threat_score == 0.01


def test_digital_sovereignty_invalid_inputs() -> None:
    failed = False
    try:
        DigitalSovereigntyVaultService.audit_sovereignty(
            vault_id="vlt_002",
            jurisdiction_region="T",  # < 2
            local_residency_pct=1.50,  # > 1.0
            exfiltration_threat_score=-0.2,  # < 0.0
        )
    except ValueError:
        failed = True

    assert failed is True
