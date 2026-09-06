from __future__ import annotations

from kefe_api.modules.decision.impact_evidence import (
    EvidenceVerificationStatus,
    ImpactEvidenceResult,
    ImpactEvidenceService,
    ImpactEvidenceType,
)


def test_impact_evidence_service_registers_digest() -> None:
    r = ImpactEvidenceService.register_evidence(
        evidence_id="evi_001",
        action_id="act_001",
        evidence_type=ImpactEvidenceType.OFFICIAL_GAZETTE_DECREE,
        evidence_title="Resmi Gazete Sayı 32900 Karar Metni",
        source_url="https://resmigazete.gov.tr/ilanlar/2026/09/01/karar.pdf",
        raw_document_content="Bu karar ile Marmara Denizi su arıtma tesisleri standartları yürürlüğe girmiştir.",
    )

    assert isinstance(r, ImpactEvidenceResult)
    assert r.evidence_type == ImpactEvidenceType.OFFICIAL_GAZETTE_DECREE
    assert len(r.sha256_digest) == 64
    assert r.verification_status == EvidenceVerificationStatus.VERIFIED_AUTHENTIC


def test_impact_evidence_invalid_url() -> None:
    failed = False
    try:
        ImpactEvidenceService.register_evidence(
            evidence_id="evi_002",
            action_id="act_001",
            evidence_type=ImpactEvidenceType.SENSOR_TELEMETRY_DATA,
            evidence_title="Sensör Verileri",
            source_url="invalid-url",
            raw_document_content="Veri paketi metni.",
        )
    except ValueError:
        failed = True

    assert failed is True
