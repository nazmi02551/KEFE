from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.correction_history import (
    CaseCorrectionHistoryResult,
    CaseCorrectionHistoryService,
    CaseCorrectionItem,
    CorrectionSeverity,
    CorrectionType,
)


def test_correction_history_logs_and_orders_corrections() -> None:
    service = CaseCorrectionHistoryService()
    case_id = uuid4()

    c1 = service.log_correction(
        case_version_id=case_id,
        correction_type=CorrectionType.FACTUAL_UPDATE,
        severity=CorrectionSeverity.MATERIAL,
        summary="Sübvansiyon bütçesi rakamı güncellendi.",
        editorial_rationale="Belediye meclisinin 2026 yılı ek bütçe kararı doğrultusunda revize edildi.",
        previous_text="120 Milyon TL sübvansiyon",
        corrected_text="150 Milyon TL sübvansiyon",
    )

    assert isinstance(c1, CaseCorrectionItem)
    assert c1.severity == CorrectionSeverity.MATERIAL

    history = service.get_history(case_id)
    assert isinstance(history, CaseCorrectionHistoryResult)
    assert len(history.corrections) == 1
    assert history.corrections[0].previous_text == "120 Milyon TL sübvansiyon"


def test_correction_history_short_fields_rejected() -> None:
    service = CaseCorrectionHistoryService()
    case_id = uuid4()

    failed = False
    try:
        service.log_correction(
            case_version_id=case_id,
            correction_type=CorrectionType.TYPO_FIX,
            severity=CorrectionSeverity.MINOR,
            summary="A",  # < 5 chars
            editorial_rationale="Kısa",  # < 10 chars
        )
    except ValueError:
        failed = True

    assert failed is True
