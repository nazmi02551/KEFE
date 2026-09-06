from __future__ import annotations

from datetime import datetime, timezone

from kefe_api.modules.decision.verified_institution_response import (
    InstitutionType,
    VerifiedInstitutionResponseResult,
    VerifiedInstitutionResponseService,
)


def test_verified_institution_response_registers_correctly() -> None:
    ts = datetime(2026, 9, 1, 14, 30, 0, tzinfo=timezone.utc)

    r = VerifiedInstitutionResponseService.register_response(
        response_id="resp_001",
        signal_id="sig_94812",
        institution_name="Ulaştırma ve Altyapı Bakanlığı",
        institution_type=InstitutionType.OFFICIAL_GOVERNMENT,
        response_body="Söz konusu demiryolu hattı güvenlik standartları gereği modernize edilecek ve istasyon erişilebilirliği artırılacaktır.",
        signing_key_id="gov-tr-uab-key-2026",
        timestamp=ts,
    )

    assert isinstance(r, VerifiedInstitutionResponseResult)
    assert r.institution_name == "Ulaştırma ve Altyapı Bakanlığı"
    assert len(r.verification_fingerprint) == 64


def test_verified_institution_response_invalid_name() -> None:
    failed = False
    try:
        VerifiedInstitutionResponseService.register_response(
            response_id="resp_002",
            signal_id="sig_94812",
            institution_name="A",
            institution_type=InstitutionType.CIVIL_SOCIETY,
            response_body="Kısa açıklama",
            signing_key_id="k",
        )
    except ValueError:
        failed = True

    assert failed is True
