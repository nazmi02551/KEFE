from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from kefe_api.modules.decision.models import (
    CaseVersion,
    FlowStep,
    PerspectiveCard,
    PerspectiveMode,
    PerspectiveSlot,
    PerspectiveSnapshot,
    PerspectiveSourceKind,
    Question,
    ReasonModerationState,
    ResolvedFlow,
    RevealSnapshot,
)
from kefe_api.modules.decision.reflection_in_memory import (
    InMemoryReflectionDecisionRepository,
)

DEMO_CASE_ID = UUID("11111111-1111-4111-8111-111111111111")
DEMO_CASE_VERSION_ID = UUID("22222222-2222-4222-8222-222222222222")
DEMO_QUESTION_ID = UUID("33333333-3333-4333-8333-333333333333")
DEMO_CONFIDENCE_QUESTION_ID = UUID("77777777-7777-4777-8777-777777777777")
DEMO_NEAR_PERSPECTIVE_ID = UUID("90000000-0000-4000-8000-000000000001")
DEMO_OPPOSING_PERSPECTIVE_ID = UUID("90000000-0000-4000-8000-000000000002")
DEMO_BRIDGE_PERSPECTIVE_ID = UUID("90000000-0000-4000-8000-000000000003")
DEMO_ALTERNATIVE_PERSPECTIVE_ID = UUID("90000000-0000-4000-8000-000000000004")

TRIAGE_CASE_ID = UUID("44444444-4444-4444-8444-444444444444")
TRIAGE_CASE_VERSION_ID = UUID("55555555-5555-4555-8555-555555555555")
TRIAGE_QUESTION_ID = UUID("66666666-6666-4666-8666-666666666666")
TRIAGE_CONFIDENCE_ID = UUID("77777777-7777-4777-8777-777777777778")
TRIAGE_NEAR_PERSPECTIVE_ID = UUID("90000000-0000-4000-8000-000000000011")
TRIAGE_OPPOSING_PERSPECTIVE_ID = UUID("90000000-0000-4000-8000-000000000012")
TRIAGE_BRIDGE_PERSPECTIVE_ID = UUID("90000000-0000-4000-8000-000000000013")
TRIAGE_ALTERNATIVE_PERSPECTIVE_ID = UUID("90000000-0000-4000-8000-000000000014")


def build_demo_repository() -> InMemoryReflectionDecisionRepository:
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
                response_schema={"min": 1, "max": 10, "step": 1},
            ),
        ),
        resolved_flow=ResolvedFlow(
            template_code="STANDARD_COMMIT_REVEAL",
            template_version_no=1,
            entry_step_code="CONTEXT",
            steps=(
                FlowStep(
                    code="CONTEXT",
                    primitive_code="CONTEXT",
                    capability_codes=("SOURCE_REVEAL",),
                    next_step_codes=("DECISION",),
                ),
                FlowStep(
                    code="DECISION",
                    primitive_code="DECISION",
                    capability_codes=(
                        "COMMIT_FIRST",
                        "CONFIDENCE_CAPTURE",
                        "REASON_CAPTURE",
                    ),
                    next_step_codes=("RESULT",),
                ),
                FlowStep(
                    code="RESULT",
                    primitive_code="COLLECTIVE_RESULT",
                ),
            ),
        ),
    )
    generated_at = datetime.now(UTC)
    reveal = RevealSnapshot(
        case_version_id=case.id,
        layer="TRUSTED",
        n=1284,
        confidence="HIGH",
        generated_at=generated_at,
        payload={"A": 0.57, "B": 0.43},
    )
    perspective = PerspectiveSnapshot(
        case_version_id=case.id,
        mode=PerspectiveMode.DEGRADED_CURATED,
        sample_kind="CURATED_FALLBACK",
        sample_size=4,
        generated_at=generated_at,
        provenance_note="KEFE demo editoryal kartları; topluluk gerekçesi içermez.",
        cards=(
            PerspectiveCard(
                perspective_id=DEMO_NEAR_PERSPECTIVE_ID,
                slot=PerspectiveSlot.NEAR,
                body="İhtiyacı daha acil görünen kişiye öncelik vermek zararı azaltabilir.",
                source_kind=PerspectiveSourceKind.CURATED,
                provenance_label="KEFE editoryal",
                moderation_state=ReasonModerationState.NOT_REQUIRED,
            ),
            PerspectiveCard(
                perspective_id=DEMO_OPPOSING_PERSPECTIVE_ID,
                slot=PerspectiveSlot.OPPOSING,
                body="Sırayı korumak, kişisel değerlendirmeden doğacak keyfiliği sınırlayabilir.",
                source_kind=PerspectiveSourceKind.CURATED,
                provenance_label="KEFE editoryal",
                moderation_state=ReasonModerationState.NOT_REQUIRED,
            ),
            PerspectiveCard(
                perspective_id=DEMO_BRIDGE_PERSPECTIVE_ID,
                slot=PerspectiveSlot.BRIDGE,
                body=(
                    "Acil ihtiyacı gözetirken sırada bekleyenin hakkını açık bir ölçütle "
                    "korumak iki kaygıyı birlikte taşıyabilir."
                ),
                source_kind=PerspectiveSourceKind.CURATED,
                provenance_label="KEFE editoryal",
                moderation_state=ReasonModerationState.NOT_REQUIRED,
            ),
            PerspectiveCard(
                perspective_id=DEMO_ALTERNATIVE_PERSPECTIVE_ID,
                slot=PerspectiveSlot.ALTERNATIVE_CONTEXT,
                body=(
                    "Koltuk tek kaynak değilse kısa süreli destek veya yer değişimi ikilemi "
                    "yumuşatabilir."
                ),
                source_kind=PerspectiveSourceKind.CURATED,
                provenance_label="KEFE editoryal",
                moderation_state=ReasonModerationState.NOT_REQUIRED,
            ),
        ),
    )

    triage_case = CaseVersion(
        id=TRIAGE_CASE_VERSION_ID,
        case_id=TRIAGE_CASE_ID,
        title="Acil Serviste Tek Solunum Cihazı",
        summary="Afet ve yoğun bakım krizinde tek kalan solunum cihazının tahsis ikilemi.",
        base_format="DILEMMA",
        primary_domain="HEALTH",
        content_risk="L1",
        version_no=1,
        questions=(
            Question(
                id=TRIAGE_QUESTION_ID,
                prompt="Son solunum cihazını kime tahsis ederdin?",
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
                id=TRIAGE_CONFIDENCE_ID,
                prompt="Bu kararından ne kadar eminsin?",
                response_type="CONFIDENCE",
                required=False,
                response_schema={"min": 1, "max": 10, "step": 1},
            ),
        ),
        resolved_flow=case.resolved_flow,
    )
    triage_reveal = RevealSnapshot(
        case_version_id=triage_case.id,
        layer="TRUSTED",
        n=842,
        confidence="HIGH",
        generated_at=generated_at,
        payload={"A": 0.52, "B": 0.48},
    )
    triage_perspective = PerspectiveSnapshot(
        case_version_id=triage_case.id,
        mode=PerspectiveMode.DEGRADED_CURATED,
        sample_kind="CURATED_FALLBACK",
        sample_size=4,
        generated_at=generated_at,
        provenance_note="KEFE editoryal triyaj kartları.",
        cards=(
            PerspectiveCard(
                perspective_id=TRIAGE_NEAR_PERSPECTIVE_ID,
                slot=PerspectiveSlot.NEAR,
                body="Genç hastanın yaşam beklentisi ve kurtulma şansı yüksek olduğu için kaynak maksimum fayda ile kullanılmalıdır.",
                source_kind=PerspectiveSourceKind.CURATED,
                provenance_label="KEFE editoryal",
                moderation_state=ReasonModerationState.NOT_REQUIRED,
            ),
            PerspectiveCard(
                perspective_id=TRIAGE_OPPOSING_PERSPECTIVE_ID,
                slot=PerspectiveSlot.OPPOSING,
                body="Topluma uzun yıllar hizmet etmiş ve kliniği ayakta tutan kıdemli hekime vefa ve süreklilik gereği öncelik verilmelidir.",
                source_kind=PerspectiveSourceKind.CURATED,
                provenance_label="KEFE editoryal",
                moderation_state=ReasonModerationState.NOT_REQUIRED,
            ),
            PerspectiveCard(
                perspective_id=TRIAGE_BRIDGE_PERSPECTIVE_ID,
                slot=PerspectiveSlot.BRIDGE,
                body="Yaş veya unvan yerine sadece nesnel tıbbi triyaj skorları (SOFA/APACHE) esas alınarak tarafsız protokol uygulanmalıdır.",
                source_kind=PerspectiveSourceKind.CURATED,
                provenance_label="KEFE editoryal",
                moderation_state=ReasonModerationState.NOT_REQUIRED,
            ),
            PerspectiveCard(
                perspective_id=TRIAGE_ALTERNATIVE_PERSPECTIVE_ID,
                slot=PerspectiveSlot.ALTERNATIVE_CONTEXT,
                body="Komşu hastanelerden acil transfer veya non-invaziv alternatif solunum desteği olanakları hızla devreye sokulmalıdır.",
                source_kind=PerspectiveSourceKind.CURATED,
                provenance_label="KEFE editoryal",
                moderation_state=ReasonModerationState.NOT_REQUIRED,
            ),
        ),
    )

    return InMemoryReflectionDecisionRepository(
        cases=[case, triage_case],
        reveals=[reveal, triage_reveal],
        perspectives=[perspective, triage_perspective],
    )
