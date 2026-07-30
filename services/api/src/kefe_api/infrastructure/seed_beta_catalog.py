from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import text

from kefe_api.core.settings import get_settings
from kefe_api.infrastructure.beta_catalog import BETA_CATALOG
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


def _version(item) -> AuthoringCaseVersion:
    return AuthoringCaseVersion(
        id=item.version_id,
        case_id=item.case_id,
        version_no=1,
        state=ContentLifecycle.DRAFT,
        title=item.title,
        summary=item.summary,
        base_format_code=item.base_format,
        primary_domain_code=item.domain,
        content_risk="L0",
        issues=(
            AuthoringIssue(
                id=item.issue_id,
                code="BETA_PRIMARY_ISSUE",
                title=item.title,
                questions=(
                    AuthoringQuestion(
                        id=item.question_id,
                        stable_code="PRIMARY_DECISION",
                        prompt=item.prompt,
                        response_type="SINGLE_CHOICE",
                        response_schema={
                            "options": [item.option_a, item.option_b],
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
                        id=item.confidence_id,
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
        modifiers=("CONFIDENCE_CAPTURE", "REASON_CAPTURE"),
        flow_template_code="STANDARD_COMMIT_REVEAL",
        flow_template_version_no=1,
    )


def seed_beta_catalog() -> None:
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

    for item in BETA_CATALOG:
        if authoring_repository.get_case(item.case_id) is None:
            version = _version(item)
            service.create_case(
                identity=CaseIdentity(id=item.case_id, slug=item.slug),
                initial_version=version,
                actor_ref="seed:beta-editor",
            )
            service.submit_for_review(version.id, actor_ref="seed:beta-editor")
            service.approve(version.id, actor_ref="seed:beta-reviewer")
            service.publish(version.id, actor_ref="seed:beta-publisher")

    engine = build_engine(settings.database_url)
    generated_at = datetime.now(UTC)
    with engine.begin() as connection:
        for index, item in enumerate(BETA_CATALOG):
            a_share = 0.48 + ((index % 5) * 0.02)
            b_share = 1.0 - a_share
            connection.execute(
                text(
                    """
                    INSERT INTO analytics.result_snapshot (
                        id, case_version_id, layer, n, confidence_label, payload, generated_at
                    ) VALUES (
                        :id, :case_version_id, 'TRUSTED', :n, 'MEDIUM',
                        CAST(:payload AS jsonb), :generated_at
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        n = EXCLUDED.n,
                        confidence_label = EXCLUDED.confidence_label,
                        payload = EXCLUDED.payload,
                        generated_at = EXCLUDED.generated_at
                    """
                ),
                {
                    "id": item.result_id,
                    "case_version_id": item.version_id,
                    "n": 300 + index * 7,
                    "payload": json.dumps(
                        {item.option_a: round(a_share, 2), item.option_b: round(b_share, 2)}
                    ),
                    "generated_at": generated_at,
                },
            )
            connection.execute(
                text(
                    """
                    INSERT INTO content.perspective_card (
                        id, case_version_id, slot, body, source_kind,
                        provenance_label, moderation_state, status, published_at
                    ) VALUES (
                        :id, :case_version_id, 'BRIDGE', :body, 'CURATED',
                        'KEFE beta editoryal fixture', 'NOT_REQUIRED', 'PUBLISHED', :published_at
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        body = EXCLUDED.body,
                        status = EXCLUDED.status,
                        published_at = EXCLUDED.published_at,
                        updated_at = now()
                    """
                ),
                {
                    "id": item.perspective_id,
                    "case_version_id": item.version_id,
                    "body": (
                        f"{item.option_a} yaklaşımı ile {item.option_b} yaklaşımı farklı değerleri "
                        "koruyabilir; kararın bağlama göre değişebileceğini birlikte düşün."
                    ),
                    "published_at": generated_at,
                },
            )


if __name__ == "__main__":
    seed_beta_catalog()
