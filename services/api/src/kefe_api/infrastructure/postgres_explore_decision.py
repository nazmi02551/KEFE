from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import text

from kefe_api.infrastructure.postgres_decision import PostgresDecisionRepository
from kefe_api.modules.decision.models import (
    CaseVersion,
    Claim,
    ClaimPresentation,
    ClaimStatus,
    ContextBlock,
    ContextKind,
    Exposure,
    Question,
    Source,
)


class PostgresExploreDecisionRepository(PostgresDecisionRepository):
    """PostgreSQL Decision adapter with Explore, typed questions and Case context."""

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

            claim_rows = connection.execute(
                text(
                    """
                    SELECT
                        c.id,
                        c.text,
                        c.status,
                        c.presentation,
                        c.sort_order,
                        COALESCE(
                            array_agg(cs.source_id ORDER BY cs.source_id)
                                FILTER (WHERE cs.source_id IS NOT NULL),
                            ARRAY[]::uuid[]
                        ) AS source_ids
                    FROM content.claim c
                    LEFT JOIN content.claim_source cs ON cs.claim_id = c.id
                    WHERE c.case_version_id = :version_id
                    GROUP BY c.id
                    ORDER BY c.presentation, c.sort_order, c.id
                    """
                ),
                {"version_id": version_id},
            ).mappings().all()

            context_rows = connection.execute(
                text(
                    """
                    SELECT id, kind, title, body
                    FROM content.context_block
                    WHERE case_version_id = :version_id
                    ORDER BY sort_order, id
                    """
                ),
                {"version_id": version_id},
            ).mappings().all()

            source_rows = connection.execute(
                text(
                    """
                    SELECT DISTINCT s.id, s.title, s.publisher, s.url, s.published_at
                    FROM content.source s
                    JOIN content.claim_source cs ON cs.source_id = s.id
                    JOIN content.claim c ON c.id = cs.claim_id
                    WHERE c.case_version_id = :version_id
                    ORDER BY s.publisher, s.title, s.id
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
        claims = tuple(
            Claim(
                id=claim_row["id"],
                text=claim_row["text"],
                status=ClaimStatus(claim_row["status"]),
                presentation=ClaimPresentation(claim_row["presentation"]),
                source_ids=tuple(claim_row["source_ids"]),
            )
            for claim_row in claim_rows
        )
        context_blocks = tuple(
            ContextBlock(
                id=context_row["id"],
                kind=ContextKind(context_row["kind"]),
                title=context_row["title"],
                body=context_row["body"],
            )
            for context_row in context_rows
        )
        sources = tuple(
            Source(
                id=source_row["id"],
                title=source_row["title"],
                publisher=source_row["publisher"],
                url=source_row["url"],
                published_at=source_row["published_at"],
            )
            for source_row in source_rows
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
            critical_claims=tuple(
                claim for claim in claims if claim.presentation is ClaimPresentation.CRITICAL
            ),
            detail_claims=tuple(
                claim for claim in claims if claim.presentation is ClaimPresentation.DETAIL
            ),
            context_blocks=context_blocks,
            sources=sources,
            accepts_weighs=row["accepts_weighs"],
        )

    def record_exposures(
        self,
        *,
        session_id: UUID,
        exposures: tuple[Exposure, ...],
    ) -> None:
        if not exposures:
            return
        with self._engine.begin() as connection:
            for exposure in exposures:
                connection.execute(
                    text(
                        """
                        INSERT INTO decision.exposure (
                            id,
                            session_id,
                            exposure_kind,
                            ref_id,
                            occurred_at
                        )
                        VALUES (
                            :id,
                            :session_id,
                            :exposure_kind,
                            :ref_id,
                            :occurred_at
                        )
                        ON CONFLICT (session_id, exposure_kind, ref_id) DO NOTHING
                        """
                    ),
                    {
                        "id": uuid4(),
                        "session_id": session_id,
                        "exposure_kind": exposure.kind.value,
                        "ref_id": exposure.ref_id,
                        "occurred_at": exposure.occurred_at,
                    },
                )
