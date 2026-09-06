from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.impact.models import (
    AuthorityVerificationStatus,
    InstitutionResponse,
    InstitutionResponseType,
)
from kefe_api.modules.impact.service import InstitutionResponseService


def test_publish_and_list_verified_institution_responses() -> None:
    service = InstitutionResponseService()
    case_version_id = uuid4()

    resp = service.publish_response(
        case_version_id=case_version_id,
        institution_name="Ulaştırma Bakanlığı",
        authority_role="Basın ve Halkla İlişkiler Dairesi",
        response_type=InstitutionResponseType.POLICY_CHANGE,
        statement="Topluluk müzakeresi sonucunda ilgili tarife düzenlemesi yeniden değerlendirmeye alınmıştır.",
        verification_status=AuthorityVerificationStatus.VERIFIED,
    )

    assert isinstance(resp, InstitutionResponse)
    assert resp.institution_name == "Ulaştırma Bakanlığı"
    assert resp.response_type == InstitutionResponseType.POLICY_CHANGE
    assert resp.verification_status == AuthorityVerificationStatus.VERIFIED

    verified_list = service.list_verified_responses(case_version_id)
    assert len(verified_list) == 1
    assert verified_list[0].response_id == resp.response_id


def test_unverified_responses_are_filtered_from_verified_list() -> None:
    service = InstitutionResponseService()
    case_version_id = uuid4()

    service.publish_response(
        case_version_id=case_version_id,
        institution_name="Sahte Kurum",
        authority_role="Anonim",
        response_type=InstitutionResponseType.ACKNOWLEDGE,
        statement="Bu doğrulama aşamasında olan bir test yanıtıdır.",
        verification_status=AuthorityVerificationStatus.PENDING_VERIFICATION,
    )

    verified_list = service.list_verified_responses(case_version_id)
    assert len(verified_list) == 0


def test_short_statement_rejected() -> None:
    service = InstitutionResponseService()
    case_version_id = uuid4()

    failed = False
    try:
        service.publish_response(
            case_version_id=case_version_id,
            institution_name="Kurum",
            authority_role="Yetkili",
            response_type=InstitutionResponseType.ACKNOWLEDGE,
            statement="Kısa",  # < 10 chars
        )
    except ValueError:
        failed = True

    assert failed is True
