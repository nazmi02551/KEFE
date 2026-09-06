from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.context_lens import (
    ContextLensPillar,
    ContextLensResult,
    ContextLensService,
    LensPillarType,
)


def test_context_lens_service_adds_and_retrieves_pillars() -> None:
    service = ContextLensService()
    case_id = uuid4()

    p1 = service.add_pillar(
        case_version_id=case_id,
        pillar_type=LensPillarType.LEGAL_FRAMEWORK,
        title="Belediye Kanunu Madde 14 ve 15",
        content="Büyükşehir belediyelerinin toplu taşıma hizmetlerini düzenleme, sübvanse etme ve ücret tarifesi belirleme yetkisi kanunla tanımlanmıştır.",
        source_citation="5393 Sayılı Belediye Kanunu, Resmi Gazete",
        source_url="https://mevzuat.gov.tr/mevzuat?MevzuatNo=5393",
    )

    p2 = service.add_pillar(
        case_version_id=case_id,
        pillar_type=LensPillarType.COMPARATIVE_PRACTICE,
        title="Avrupa Metropollerinde Gece Ulaşımı",
        content="Londra Night Tube ve Berlin 24 saatlik metro uygulamaları kamu bütçesi ve güvenlik personeli sübvansiyonu ile işletilmektedir.",
        source_citation="TfL Night Services Report 2024",
    )

    assert isinstance(p1, ContextLensPillar)
    assert p1.pillar_type == LensPillarType.LEGAL_FRAMEWORK

    result = service.get_lens_for_case(case_id)
    assert isinstance(result, ContextLensResult)
    assert len(result.pillars) == 2
    assert result.pillars[0].source_citation.startswith("5393 Sayılı")


def test_context_lens_insufficient_content_rejected() -> None:
    service = ContextLensService()
    case_id = uuid4()

    failed = False
    try:
        service.add_pillar(
            case_version_id=case_id,
            pillar_type=LensPillarType.SCIENTIFIC_DATA,
            title="Kısa Başlık",
            content="Kısa içerik.",  # < 20 characters
            source_citation="Kaynak",
        )
    except ValueError:
        failed = True

    assert failed is True
