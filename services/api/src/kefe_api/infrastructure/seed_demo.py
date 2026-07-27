from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import text

from kefe_api.core.settings import get_settings
from kefe_api.infrastructure.db import build_engine
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
DEMO_STABLE_QUESTION_ID = UUID("55555555-5555-4555-8555-555555555555")
DEMO_RESULT_ID = UUID("66666666-6666-4666-8666-666666666666")
DEMO_STABLE_CONFIDENCE_QUESTION_ID = UUID("88888888-8888-4888-8888-888888888888")

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
        "Koltuk tek kaynak değilse kısa süreli destek veya yer değişimi ikilemi yumuşatabilir.",
    ),
)


def seed_demo() -> None:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required to seed PostgreSQL")

    engine = build_engine(settings.database_url)
    published_at = datetime.now(UTC)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO content.case_item (
                    id, slug, base_format_code, primary_domain_code, lifecycle_state, content_risk
                )
                VALUES (
                    :id, 'son-koltuk-kime-verilmeli', 'DILEMMA', 'DAILY_LIFE', 'PUBLISHED', 'L0'
                )
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {"id": DEMO_CASE_ID},
        )
        connection.execute(
            text(
                """
                INSERT INTO content.case_version (
                    id, case_id, version_no, status, title, summary, accepts_weighs, published_at
                )
                VALUES (
                    :id, :case_id, 1, 'PUBLISHED', :title, :summary, true, :published_at
                )
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "id": DEMO_CASE_VERSION_ID,
                "case_id": DEMO_CASE_ID,
                "title": "Son koltuk kime verilmeli?",
                "summary": "İki makul ihtiyaç arasında sınırlı bir kaynağı tart.",
                "published_at": published_at,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO content.issue (id, case_version_id, code, title, sort_order)
                VALUES (:id, :case_version_id, 'RESOURCE_FAIRNESS', 'Sınırlı kaynakta öncelik', 0)
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {"id": DEMO_ISSUE_ID, "case_version_id": DEMO_CASE_VERSION_ID},
        )
        connection.execute(
            text(
                """
                INSERT INTO content.question (id, issue_id, stable_code, sort_order)
                VALUES (:id, :issue_id, 'PRIMARY_DECISION', 0)
                ON CONFLICT (id) DO UPDATE SET sort_order = EXCLUDED.sort_order
                """
            ),
            {"id": DEMO_STABLE_QUESTION_ID, "issue_id": DEMO_ISSUE_ID},
        )
        connection.execute(
            text(
                """
                INSERT INTO content.question_version (
                    id,
                    question_id,
                    version_no,
                    prompt,
                    response_type,
                    response_schema,
                    is_required,
                    is_active
                )
                VALUES (
                    :id,
                    :question_id,
                    1,
                    'Son koltuğu kime verirdin?',
                    'SINGLE_CHOICE',
                    CAST(:response_schema AS jsonb),
                    true,
                    true
                )
                ON CONFLICT (id) DO UPDATE SET
                    response_schema = EXCLUDED.response_schema,
                    is_required = EXCLUDED.is_required
                """
            ),
            {
                "id": DEMO_QUESTION_ID,
                "question_id": DEMO_STABLE_QUESTION_ID,
                "response_schema": json.dumps(
                    {
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
                    }
                ),
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO content.question (id, issue_id, stable_code, sort_order)
                VALUES (:id, :issue_id, 'DECISION_CONFIDENCE', 10)
                ON CONFLICT (id) DO UPDATE SET sort_order = EXCLUDED.sort_order
                """
            ),
            {
                "id": DEMO_STABLE_CONFIDENCE_QUESTION_ID,
                "issue_id": DEMO_ISSUE_ID,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO content.question_version (
                    id,
                    question_id,
                    version_no,
                    prompt,
                    response_type,
                    response_schema,
                    is_required,
                    is_active
                )
                VALUES (
                    :id,
                    :question_id,
                    1,
                    'Bu kararından ne kadar eminsin?',
                    'CONFIDENCE',
                    CAST(:response_schema AS jsonb),
                    false,
                    true
                )
                ON CONFLICT (id) DO UPDATE SET
                    response_schema = EXCLUDED.response_schema,
                    is_required = EXCLUDED.is_required
                """
            ),
            {
                "id": DEMO_CONFIDENCE_QUESTION_ID,
                "question_id": DEMO_STABLE_CONFIDENCE_QUESTION_ID,
                "response_schema": json.dumps({"min": 1, "max": 5, "step": 1}),
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO analytics.result_snapshot (
                    id, case_version_id, layer, n, confidence_label, payload, generated_at
                )
                VALUES (
                    :id,
                    :case_version_id,
                    'TRUSTED',
                    1284,
                    'HIGH',
                    CAST(:payload AS jsonb),
                    :generated_at
                )
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {
                "id": DEMO_RESULT_ID,
                "case_version_id": DEMO_CASE_VERSION_ID,
                "payload": json.dumps({"A": 0.57, "B": 0.43}),
                "generated_at": published_at,
            },
        )
        for perspective_id, slot, body in DEMO_PERSPECTIVES:
            connection.execute(
                text(
                    """
                    INSERT INTO content.perspective_card (
                        id,
                        case_version_id,
                        slot,
                        body,
                        source_kind,
                        provenance_label,
                        moderation_state,
                        status,
                        published_at
                    )
                    VALUES (
                        :id,
                        :case_version_id,
                        :slot,
                        :body,
                        'CURATED',
                        'KEFE editoryal',
                        'NOT_REQUIRED',
                        'PUBLISHED',
                        :published_at
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
                    "published_at": published_at,
                },
            )


if __name__ == "__main__":
    seed_demo()
