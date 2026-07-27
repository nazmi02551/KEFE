from __future__ import annotations

from sqlalchemy import text

from kefe_api.infrastructure.postgres_decision import PostgresDecisionRepository
from kefe_api.modules.decision.models import CaseVersion


class PostgresExploreDecisionRepository(PostgresDecisionRepository):
    """Decision adapter with the read model required by Explore."""

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
