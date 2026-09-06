from __future__ import annotations

from kefe_api.modules.decision.public_procurement_oversight import (
    ProcurementIntegrityLevel,
    ProcurementOversightResult,
    PublicProcurementOversightService,
)


def test_procurement_oversight_verifies_open_tender() -> None:
    r = PublicProcurementOversightService.audit_tender(
        tender_id="tnd_001",
        contracting_authority="Kadıköy Belediyesi Fen İşleri",
        awarded_amount_try=15400000.0,
        cost_overrun_pct=0.02,
        active_civic_auditors_count=128,
    )

    assert isinstance(r, ProcurementOversightResult)
    assert r.integrity_level == ProcurementIntegrityLevel.OPEN_COMPETITIVE_VERIFIED
    assert r.awarded_amount_try == 15400000.0
    assert r.active_civic_auditors_count == 128


def test_procurement_oversight_invalid_inputs() -> None:
    failed = False
    try:
        PublicProcurementOversightService.audit_tender(
            tender_id="tnd_002",
            contracting_authority="AB",  # < 3
            awarded_amount_try=-1000.0,  # < 0
            cost_overrun_pct=-0.1,  # < 0
            active_civic_auditors_count=-5,  # < 0
        )
    except ValueError:
        failed = True

    assert failed is True
