from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from kefe_api.modules.decision.in_memory import InMemoryDecisionRepository
from kefe_api.modules.decision.models import (
    CaseVersion,
    PerspectiveItem,
    PerspectiveModerationState,
    PerspectivePublicationState,
    PerspectiveSourceKind,
    Question,
    RevealSnapshot,
)

DEMO_CASE_ID = UUID("11111111-1111-4111-8111-111111111111")
DEMO_CASE_VERSION_ID = UUID("22222222-2222-4222-8222-222222222222")
DEMO_QUESTION_ID = UUID("33333333-3333-4333-8333-333333333333")
DEMO_CONFIDENCE_QUESTION_ID = UUID("77777777-7777-4777-8777-777777777777")
DEMO_PERSPECTIVE_A_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1")
DEMO_PERSPECTIVE_B_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb2")


def build_demo_repository() -> InMemoryDecisionRepository:
    case = CaseVersion(
        id=DEMO_CASE_VERSION_ID,
        case_id=DEMO_CASE_ID,
        title="Son koltuk kime verilmeli?",
        summary="İki makul ihtiyaç arasında sınırlı bir kaynağı tart.",
        base_format="DILEMMA",
        primary_domain="DAILY_LIFE",
        content_risk="L0",
        version_no=1,
        questions=(
            Question(
                id=DEMO_QUESTION_ID,
                prompt="Son koltuğu kime verirdin?",
                response_type="SINGLE_CHOICE",
                required=True,
                response_schema={
                    "options": ["A", "B"],
                    "reason": {
                        "tags": [
                            "FAIRNESS",
                            "NEED",
                            "RESPONSIBILITY",
                            "PRACTICAL_IMPACT",
                        ],
                        "max_tags": 3,
                        "text_enabled": True,
                        "text_max_length": 500,
                    },
                },
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
    perspectives = [
        PerspectiveItem(
            id=DEMO_PERSPECTIVE_A_ID,
            case_version_id=case.id,
            question_version_id=DEMO_QUESTION_ID,
            target_value="A",
            text=(
                "A seçeneği, sınırlı kaynağı o anda daha acil ihtiyacı olan kişiye "
                "vermenin daha adil olduğunu savunur."
            ),
            source_kind=PerspectiveSourceKind.EDITORIAL_HUMAN,
            moderation_state=PerspectiveModerationState.ALLOWED,
            publication_state=PerspectivePublicationState.PUBLISHED,
            editorial_priority=10,
        ),
        PerspectiveItem(
            id=DEMO_PERSPECTIVE_B_ID,
            case_version_id=case.id,
            question_version_id=DEMO_QUESTION_ID,
            target_value="B",
            text=(
                "B seçeneği, önceliğin yalnız mevcut ihtiyete değil sorumluluk ve "
                "koşulların bütünüyle değerlendirilmesi gerektiğini savunur."
            ),
            source_kind=PerspectiveSourceKind.EDITORIAL_HUMAN,
            moderation_state=PerspectiveModerationState.ALLOWED,
            publication_state=PerspectivePublicationState.PUBLISHED,
            editorial_priority=10,
        ),
    ]
    return InMemoryDecisionRepository(
        cases=[case],
        reveals=[reveal],
        perspectives=perspectives,
    )
