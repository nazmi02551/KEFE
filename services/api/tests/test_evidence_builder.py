from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.evidence_builder import (
    EvidenceBuilderService,
    EvidenceCategory,
    EvidenceVerificationStatus,
    StructuredEvidenceItem,
)


def test_evidence_builder_service_attaches_and_filters_evidence() -> None:
    service = EvidenceBuilderService()
    case_id = uuid4()
    reason_id = uuid4()

    item = service.attach_evidence(
        case_version_id=case_id,
        reason_id=reason_id,
        category=EvidenceCategory.ACADEMIC_PEER_REVIEWED,
        title="Kentsel Toplu Taşıma Sübvansiyonlarının Sosyo-Ekonomik Etkileri",
        publisher="İktisat ve Toplum Dergisi",
        source_url="https://dergipark.org.tr/tr/pub/iktisat/issue/44",
        doi_or_doc_ref="doi:10.1111/j.1467-6419.2024.0044.x",
        verification_status=EvidenceVerificationStatus.EXPERT_AUDITED,
    )

    assert isinstance(item, StructuredEvidenceItem)
    assert item.verification_status == EvidenceVerificationStatus.EXPERT_AUDITED
    assert item.doi_or_doc_ref == "doi:10.1111/j.1467-6419.2024.0044.x"

    all_ev = service.get_evidence_for_case(case_id)
    assert len(all_ev) == 1
    assert all_ev[0].publisher == "İktisat ve Toplum Dergisi"


def test_evidence_short_title_rejected() -> None:
    service = EvidenceBuilderService()
    case_id = uuid4()

    failed = False
    try:
        service.attach_evidence(
            case_version_id=case_id,
            category=EvidenceCategory.OFFICIAL_GOVERNMENT_STAT,
            title="A",  # < 5 characters
            publisher="TÜİK",
        )
    except ValueError:
        failed = True

    assert failed is True
