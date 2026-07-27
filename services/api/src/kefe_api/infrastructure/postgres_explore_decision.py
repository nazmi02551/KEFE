from __future__ import annotations

from uuid import UUID

from sqlalchemy import text

from kefe_api.infrastructure.postgres_decision import PostgresDecisionRepository
from kefe_api.modules.decision.models import CaseVersion, Question


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
                        ci.base_format_code,
                        ci.primary_domain_code,
                        ci.content_risk
                    FROM content.case_version cv
                    JOIN content.case_item ci ON ci.id = cv.case_id
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
            )
            for question_row in question_rows
        )
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
        )
