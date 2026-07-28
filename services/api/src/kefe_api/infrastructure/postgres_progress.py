from __future__ import annotations

from uuid import UUID

from sqlalchemy import Engine, text

from kefe_api.modules.progress.models import ProgressSnapshot, RecentCompletedCase


class PostgresProgressRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_progress(self, actor_id: UUID, *, recent_limit: int) -> ProgressSnapshot:
        with self._engine.connect() as connection:
            aggregate = connection.execute(
                text(
                    """
                    SELECT
                        count(*) AS meaningful_weigh_count,
                        count(DISTINCT ws.case_id) AS distinct_case_count,
                        count(DISTINCT ci.primary_domain_code) AS distinct_domain_count,
                        min(ws.committed_at) AS first_committed_at,
                        max(ws.committed_at) AS last_committed_at
                    FROM decision.weigh_session ws
                    JOIN content.case_item ci ON ci.id = ws.case_id
                    WHERE ws.actor_id = :actor_id
                      AND ws.state = 'COMMITTED'
                    """
                ),
                {"actor_id": actor_id},
            ).mappings().one()
            rows = connection.execute(
                text(
                    """
                    SELECT
                        ws.case_id,
                        ws.case_version_id,
                        cv.title,
                        ci.primary_domain_code,
                        ws.committed_at
                    FROM decision.weigh_session ws
                    JOIN content.case_item ci ON ci.id = ws.case_id
                    JOIN content.case_version cv ON cv.id = ws.case_version_id
                    WHERE ws.actor_id = :actor_id
                      AND ws.state = 'COMMITTED'
                    ORDER BY ws.committed_at DESC, ws.id DESC
                    LIMIT :recent_limit
                    """
                ),
                {"actor_id": actor_id, "recent_limit": recent_limit},
            ).mappings().all()

        return ProgressSnapshot(
            actor_id=actor_id,
            meaningful_weigh_count=aggregate["meaningful_weigh_count"],
            distinct_case_count=aggregate["distinct_case_count"],
            distinct_domain_count=aggregate["distinct_domain_count"],
            first_committed_at=aggregate["first_committed_at"],
            last_committed_at=aggregate["last_committed_at"],
            recent_cases=tuple(
                RecentCompletedCase(
                    case_id=row["case_id"],
                    case_version_id=row["case_version_id"],
                    title=row["title"],
                    primary_domain=row["primary_domain_code"],
                    committed_at=row["committed_at"],
                )
                for row in rows
            ),
        )
