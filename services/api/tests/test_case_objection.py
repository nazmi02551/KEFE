from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.case_objection import (
    CaseObjectionItem,
    CaseObjectionService,
    ObjectionCategory,
    ObjectionStatus,
)


def test_case_objection_service_submits_and_resolves_challenge() -> None:
    service = CaseObjectionService()
    case_id = uuid4()

    item = service.submit_objection(
        case_version_id=case_id,
        reason_category=ObjectionCategory.EXCLUDED_STAKEHOLDER,
        statement="Gece vardiyasında çalışan sağlık personeli paydaş analizi ve seçeneklerde dışlanmıştır.",
        supporting_evidence_url="https://tabipodasi.org.tr/rapor/2026",
    )

    assert isinstance(item, CaseObjectionItem)
    assert item.status == ObjectionStatus.SUBMITTED
    assert item.reason_category == ObjectionCategory.EXCLUDED_STAKEHOLDER

    # Resolution
    resolved = service.resolve_objection(
        objection_id=item.objection_id,
        new_status=ObjectionStatus.ACCEPTED_CORRECTION_FILED,
        resolution_note="Haklı itiraz. Vaka sürümü v1.2'ye sağlık çalışanları paydaş grubu eklendi.",
    )

    assert resolved.status == ObjectionStatus.ACCEPTED_CORRECTION_FILED
    assert resolved.resolution_note is not None


def test_case_objection_short_statement_rejected() -> None:
    service = CaseObjectionService()
    case_id = uuid4()

    failed = False
    try:
        service.submit_objection(
            case_version_id=case_id,
            reason_category=ObjectionCategory.EDITORIAL_BIAS_FRAMING,
            statement="Bu vaka taraflı.",  # < 20 characters
        )
    except ValueError:
        failed = True

    assert failed is True
