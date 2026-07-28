from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import text

from kefe_api.core.settings import get_settings
from kefe_api.infrastructure.db import build_engine
from kefe_api.infrastructure.persistence import (
    build_content_authoring_repository,
    build_content_configuration_repository,
)
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    AuthoringIssue,
    AuthoringQuestion,
    CaseIdentity,
    ContentLifecycle,
)
from kefe_api.modules.content_authoring.registry import default_authoring_registry
from kefe_api.modules.content_authoring.service import ContentAuthoringService
from kefe_api.modules.content_configuration.publication_resolver import (
    ContentConfigurationPublicationResolver,
)
from kefe_api.modules.decision.bootstrap import (
    DEMO_ALTERNATIVE_PERSPECTIVE_ID,
    DEMO_BRIDGE_PERSPECTIVE_ID,
    DEMO_CASE_ID,
    DEMO_CASE_VERSION_ID,
    DEMO_CONFIDENCE_QUESTION_ID,
    DEMO_NEAR_PERSPECTIVE_ID,
    DEMO_OPPOSING_PERSPECTIVE_ID,
    DEMO_QUESTION_ID,
)

DEMO_ISSUE_ID = UUID("44444444-4444-4444-8444-444444444444")
DEMO_RESULT_ID = UUID("66666666-6666-4666-8666-666666666666")

DEMO_PERSPECTIVES = (
    (
        DEMO_NEAR_PERSPECTIVE_ID,
        "NEAR",
        "İhtiyacı daha acil görünen kişiye öncelik vermek zararı azaltabilir.",
    ),
    (
        DEMO_OPPOSING_PERSPECTIVE_ID,
        "OPPOSING",
        "Sırayı korumak, kişisel değerlendirmeden doğacak keyfiliği sınırlayabilir.",
    ),
    (
        DEMO_BRIDGE_PERSPECTIVE_ID,
        "BRIDGE",
        (
            "Acil ihtiyacı gözetirken sırada bekleyenin hakkını açık bir ölçütle "
            "korumak iki kaygıyı birlikte taşıyabilir."
        ),
    ),
    (
        DEMO_ALTERNATIVE_PERSPECTIVE_ID,
        "ALTERNATIVE_CONTEXT",
        (
            "Koltuk tek kaynak değilse kısa süreli destek veya yer değişimi "
            "ikilemi yumuşatabilir."
        ),
    ),
)


def _demo_authoring_version() -> AuthoringCaseVersion:
    return AuthoringCaseVersion(
        id=DEMO_CASE_VERSION_ID,
        case_id=DEMO_CASE_ID,
        version_no=1,
        state=ContentLifecycle.DRAFT,
        title="Son koltuk kime verilmeli?",
        summary="İki makul ihtiyaç arasında sınırlı bir kaynağı tart.",
        base_format_code="DILEMMA",
        primary_domain_code="DAILY_LIFE",
        content_risk="L0",
        issues=(
            AuthoringIssue(
                id=DEMO_ISSUE_ID,
                code="RESOURCE_FAIRNESS",
                title="Sınırlı kaynakta öncelik",
                questions=(
                    AuthoringQuestion(
                        id=DEMO_QUESTION_ID,
                        stable_code="PRIMARY_DECISION",
                        prompt="Son koltuğu kime verirdin?",
                        response_type="SINGLE_CHOICE",
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
                        is_required=True,
                        sort_order=0,
                    ),
                    AuthoringQuestion(
                        id=DEMO_CONFIDENCE_QUESTION_ID,
                        stable_code="DECISION_CONFIDENCE",
                        prompt="Bu kararından ne kadar eminsin?",
                        response_type="CONFIDENCE",
                        response_schema={"min": 1, "max": 10, "step": 1},
                        is_required=False,
                        sort_order=10,
                    ),
                ),
            ),
        ),
        modifiers=("CONFIDENCE_CAPTURE",),
        flow_template_code="STANDARD_COMMIT_REVEAL",
        flow_template_version_no=1,
    )


def _publish_demo_case() -> None:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required to seed PostgreSQL")
    postgres_settings = settings.model_copy(update={"persistence_backend": "postgres"})
    authoring_repository = build_content_authoring_repository(postgres_settings)
    configuration_repository = build_content_configuration_repository(postgres_settings)
    service = ContentAuthoringService(
        authoring_repository,
        default_authoring_registry(),
        ContentConfigurationPublicationResolver(configuration_repository),
    )
    if authoring_repository.get_case(DEMO_CASE_ID) is not None:
        return

    version = _demo_authoring_version()
    service.create_case(
        identity=CaseIdentity(
            id=DEMO_CASE_ID,
            slug="son-koltuk-kime-verilmeli",
        ),
        initial_version=version,
        actor_ref="seed:demo-editor",
    )
    service.submit_for_review(version.id, actor_ref="seed:demo-editor")
    service.approve(version.id, actor_ref="seed:demo-reviewer")
    service.publish(version.id, actor_ref="seed:demo-publisher")


def _seed_demo_result_and_perspectives() -> None:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required to seed PostgreSQL")

    engine = build_engine(settings.database_url)
    generated_at = datetime.now(UTC)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO analytics.result_snapshot (
                    id, case_version_id, layer, n, confidence_label, payload, generated_at
                )
                VALUES (
                    :id, :case_version_id, 'TRUSTED', 1284, 'HIGH',
                    CAST(:payload AS jsonb), :generated_at
                )
                ON CONFLICT (id) DO UPDATE SET
                    payload = EXCLUDED.payload,
                    n = EXCLUDED.n,
                    confidence_label = EXCLUDED.confidence_label,
                    generated_at = EXCLUDED.generated_at
                """
            ),
            {
                "id": DEMO_RESULT_ID,
                "case_version_id": DEMO_CASE_VERSION_ID,
                "payload": json.dumps({"A": 0.57, "B": 0.43}),
                "generated_at": generated_at,
            },
        )
        for perspective_id, slot, body in DEMO_PERSPECTIVES:
            connection.execute(
                text(
                    """
                    INSERT INTO content.perspective_card (
                        id, case_version_id, slot, body, source_kind,
                        provenance_label, moderation_state, status, published_at
                    )
                    VALUES (
                        :id, :case_version_id, :slot, :body, 'CURATED',
                        'KEFE editoryal', 'NOT_REQUIRED', 'PUBLISHED', :published_at
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        body = EXCLUDED.body,
                        provenance_label = EXCLUDED.provenance_label,
                        status = EXCLUDED.status,
                        published_at = EXCLUDED.published_at,
                        updated_at = now()
                    """
                ),
                {
                    "id": perspective_id,
                    "case_version_id": DEMO_CASE_VERSION_ID,
                    "slot": slot,
                    "body": body,
                    "published_at": generated_at,
                },
            )


def seed_demo() -> None:
    _publish_demo_case()
    _seed_demo_result_and_perspectives()


if __name__ == "__main__":
    seed_demo()
