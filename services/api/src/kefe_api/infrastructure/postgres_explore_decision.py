from __future__ import annotations

from uuid import UUID

from sqlalchemy import text

from kefe_api.infrastructure.postgres_decision import PostgresDecisionRepository
from kefe_api.modules.decision.models import (
    CaseLocalization,
    CaseVersion,
    FlowStep,
    Question,
    ResolvedFlow,
)


class PostgresExploreDecisionRepository(PostgresDecisionRepository):
    """Decision adapter with the read model required by Explore and typed questions."""

    def list_current_cases(self, *, limit: int) -> tuple[CaseVersion, ...]:
        with self._engine.connect() as connection:
            version_ids = connection.execute(
                text(
                    """
                    SELECT cv.id
                    FROM content.case_version cv
                    JOIN content.case_item ci ON ci.id = cv.case_id
                    WHERE cv.status = 'PUBLISHED'
                      AND ci.lifecycle_state = 'PUBLISHED'
                    ORDER BY cv.published_at DESC NULLS LAST, cv.created_at DESC, cv.id
                    LIMIT :limit
                    """
                ),
                {"limit": limit},
            ).scalars().all()

        cases = [self.get_case_version(version_id) for version_id in version_ids]
        return tuple(case for case in cases if case is not None)

    def get_case_version(self, version_id: UUID) -> CaseVersion | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT
                        cv.id,
                        cv.case_id,
                        cv.version_no,
                        cv.title,
                        cv.summary,
                        cv.accepts_weighs,
                        cv.is_real_event,
                        cv.base_format_code,
                        cv.primary_domain_code,
                        cv.content_risk,
                        cv.content_configuration_id,
                        cv.content_configuration_version_no,
                        cv.resolved_flow,
                        cv.content_locale,
                        cv.market_scope,
                        cv.country_codes,
                        cv.cultural_context_note,
                        cv.legal_context_note,
                        cv.localizations
                    FROM content.case_version cv
                    WHERE cv.id = :version_id
                    """
                ),
                {"version_id": version_id},
            ).mappings().one_or_none()
            if row is None:
                return None

            question_rows = connection.execute(
                text(
                    """
                    SELECT
                        q.stable_code,
                        qv.id,
                        qv.prompt,
                        qv.response_type,
                        qv.response_schema,
                        qv.is_required
                    FROM content.issue i
                    JOIN content.question q ON q.issue_id = i.id
                    JOIN LATERAL (
                        SELECT
                            version.id,
                            version.prompt,
                            version.response_type,
                            version.response_schema,
                            version.is_required
                        FROM content.question_version version
                        WHERE version.question_id = q.id
                          AND version.is_active = true
                        ORDER BY version.version_no DESC
                        LIMIT 1
                    ) qv ON true
                    WHERE i.case_version_id = :version_id
                    ORDER BY i.sort_order, q.sort_order, q.id
                    """
                ),
                {"version_id": version_id},
            ).mappings().all()

        questions = tuple(
            Question(
                id=question_row["id"],
                prompt=question_row["prompt"],
                response_type=question_row["response_type"],
                required=question_row["is_required"],
                response_schema=question_row["response_schema"] or {},
                stable_code=question_row["stable_code"],
            )
            for question_row in question_rows
        )
        resolved_flow_document = row["resolved_flow"]
        resolved_flow = (
            ResolvedFlow(
                template_code=resolved_flow_document["template_code"],
                template_version_no=int(resolved_flow_document["template_version_no"]),
                entry_step_code=resolved_flow_document["entry_step_code"],
                steps=tuple(
                    FlowStep(
                        code=item["code"],
                        primitive_code=item["primitive_code"],
                        capability_codes=tuple(item.get("capability_codes", [])),
                        next_step_codes=tuple(item.get("next_step_codes", [])),
                        payload_schema_ref=item.get("payload_schema_ref"),
                    )
                    for item in resolved_flow_document.get("steps", [])
                ),
            )
            if resolved_flow_document is not None
            else None
        )
        localization_document = row["localizations"] or {}
        localizations = {
            locale: CaseLocalization(
                locale=locale,
                title=document["title"],
                summary=document["summary"],
                question_prompts=document.get("question_prompts", {}),
                option_labels=document.get("option_labels", {}),
                cultural_context_note=document.get("cultural_context_note"),
                legal_context_note=document.get("legal_context_note"),
            )
            for locale, document in localization_document.items()
        }
        return CaseVersion(
            id=row["id"],
            case_id=row["case_id"],
            title=row["title"],
            summary=row["summary"],
            base_format=row["base_format_code"],
            primary_domain=row["primary_domain_code"],
            content_risk=row["content_risk"],
            version_no=row["version_no"],
            questions=questions,
            accepts_weighs=row["accepts_weighs"],
            is_real_event=row["is_real_event"],
            content_configuration_id=row["content_configuration_id"],
            content_configuration_version_no=row["content_configuration_version_no"],
            resolved_flow=resolved_flow,
            content_locale=row["content_locale"],
            market_scope=row["market_scope"],
            country_codes=tuple(row["country_codes"] or ()),
            cultural_context_note=row["cultural_context_note"],
            legal_context_note=row["legal_context_note"],
            localizations=localizations,
        )
