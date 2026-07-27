from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from kefe_api.modules.decision.in_memory import InMemoryDecisionRepository
from kefe_api.modules.decision.models import CaseVersion, Question, RevealSnapshot

DEMO_CASE_ID = UUID("11111111-1111-4111-8111-111111111111")
DEMO_CASE_VERSION_ID = UUID("22222222-2222-4222-8222-222222222222")
DEMO_QUESTION_ID = UUID("33333333-3333-4333-8333-333333333333")


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
                options=("A", "B"),
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
