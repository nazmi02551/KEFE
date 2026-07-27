from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from kefe_api.modules.decision.in_memory import InMemoryDecisionRepository
from kefe_api.modules.decision.models import (
    CaseVersion,
    Claim,
    ClaimPresentation,
    ClaimStatus,
    ContextBlock,
    ContextKind,
    Question,
    RevealSnapshot,
    Source,
)

DEMO_CASE_ID = UUID("11111111-1111-4111-8111-111111111111")
DEMO_CASE_VERSION_ID = UUID("22222222-2222-4222-8222-222222222222")
DEMO_QUESTION_ID = UUID("33333333-3333-4333-8333-333333333333")
DEMO_CONFIDENCE_QUESTION_ID = UUID("77777777-7777-4777-8777-777777777777")

DEMO_CRITICAL_CLAIM_IDS = (
    UUID("91000000-0000-4000-8000-000000000001"),
    UUID("91000000-0000-4000-8000-000000000002"),
    UUID("91000000-0000-4000-8000-000000000003"),
)
DEMO_DETAIL_CLAIM_ID = UUID("92000000-0000-4000-8000-000000000001")
DEMO_CONTEXT_BLOCK_ID = UUID("93000000-0000-4000-8000-000000000001")
DEMO_METHODOLOGY_BLOCK_ID = UUID("93000000-0000-4000-8000-000000000002")
DEMO_SOURCE_ID = UUID("94000000-0000-4000-8000-000000000001")


def build_demo_repository() -> InMemoryDecisionRepository:
    methodology_source = Source(
        id=DEMO_SOURCE_ID,
        title="Development fixture methodology note",
        publisher="KEFE Development Fixture",
        url="https://kefe.invalid/methodology/demo-case",
    )
    case = CaseVersion(
        id=DEMO_CASE_VERSION_ID,
        case_id=DEMO_CASE_ID,
        title="Son koltuk kime verilmeli?",
        summary="İki makul ihtiyaç arasında sınırlı bir kaynağı tart.",
        base_format="DILEMMA",
        primary_domain="DAILY_LIFE",
        content_risk="L0",
        version_no=1,
        critical_claims=(
            Claim(
                id=DEMO_CRITICAL_CLAIM_IDS[0],
                text="Senaryoda yalnızca bir boş koltuk vardır.",
                status=ClaimStatus.VERIFIED,
                presentation=ClaimPresentation.CRITICAL,
            ),
            Claim(
                id=DEMO_CRITICAL_CLAIM_IDS[1],
                text="İki kişinin de makul fakat birbirinden farklı bir ihtiyacı vardır.",
                status=ClaimStatus.VERIFIED,
                presentation=ClaimPresentation.CRITICAL,
            ),
            Claim(
                id=DEMO_CRITICAL_CLAIM_IDS[2],
                text="Karar, sınırlı bir kaynakta önceliğin nasıl kurulacağını tartar.",
                status=ClaimStatus.VERIFIED,
                presentation=ClaimPresentation.CRITICAL,
            ),
        ),
        detail_claims=(
            Claim(
                id=DEMO_DETAIL_CLAIM_ID,
                text="Bu DILEMMA gerçek bir kişi veya güncel olaya ilişkin iddia değildir.",
                status=ClaimStatus.VERIFIED,
                presentation=ClaimPresentation.DETAIL,
                source_ids=(DEMO_SOURCE_ID,),
            ),
        ),
        context_blocks=(
            ContextBlock(
                id=DEMO_CONTEXT_BLOCK_ID,
                kind=ContextKind.CONTEXT,
                title="Bağlam",
                body=(
                    "Bu senaryoda karar verici, iki makul ihtiyaç arasında tek bir koltuğu "
                    "tahsis etmek zorundadır. Amaç kişileri değer bakımından sıralamak değil, "
                    "hangi gerekçenin öncelik yaratacağını tartmaktır."
                ),
            ),
            ContextBlock(
                id=DEMO_METHODOLOGY_BLOCK_ID,
                kind=ContextKind.METHODOLOGY,
                title="Bu içerik nasıl kullanılmalı?",
                body=(
                    "Bu içerik düşük riskli sentetik bir geliştirme senaryosudur. "
                    "Topluluk sonucu ilk karar verilmeden gösterilmez."
                ),
            ),
        ),
        sources=(methodology_source,),
        questions=(
            Question(
                id=DEMO_QUESTION_ID,
                prompt="Son koltuğu kime verirdin?",
                response_type="SINGLE_CHOICE",
                required=True,
                response_schema={"options": ["A", "B"]},
            ),
            Question(
                id=DEMO_CONFIDENCE_QUESTION_ID,
                prompt="Bu kararından ne kadar eminsin?",
                response_type="CONFIDENCE",
                required=False,
                response_schema={"min": 1, "max": 5, "step": 1},
            ),
        ),
    )
    reveal = RevealSnapshot(
        case_version_id=case.id,
        layer="TRUSTED",
        n=1284,
        confidence="HIGH",
        generated_at=datetime.now(UTC),
        payload={"A": 0.57, "B": 0.43},
    )
    return InMemoryDecisionRepository(cases=[case], reveals=[reveal])
