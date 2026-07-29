from __future__ import annotations

from uuid import UUID

from sqlalchemy import Engine, text

from kefe_api.modules.progress.models import (
    DecisionJourneySnapshot,
    DomainActivity,
    ProgressSnapshot,
    RecentCompletedCase,
    RecentDecisionJourney,
)


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

    def get_journey(
        self,
        actor_id: UUID,
        *,
        recent_limit: int,
        domain_limit: int,
    ) -> DecisionJourneySnapshot:
        with self._engine.connect() as connection:
            aggregate = connection.execute(
                text(
                    """
                    WITH committed AS (
                        SELECT ws.id
                        FROM decision.weigh_session ws
                        WHERE ws.actor_id = :actor_id
                          AND ws.state = 'COMMITTED'
                    ),
                    revisions AS (
                        SELECT
                            dr.session_id,
                            count(*) FILTER (WHERE dr.revision_no > 1) AS update_count
                        FROM decision.decision_revision dr
                        JOIN committed c ON c.id = dr.session_id
                        WHERE dr.actor_id = :actor_id
                        GROUP BY dr.session_id
                    ),
                    reflections AS (
                        SELECT
                            rc.session_id,
                            count(*) AS completion_count
                        FROM decision.reflection_completion rc
                        JOIN committed c ON c.id = rc.session_id
                        WHERE rc.actor_id = :actor_id
                        GROUP BY rc.session_id
                    )
                    SELECT
                        COALESCE(sum(r.update_count), 0) AS decision_update_count,
                        count(*) FILTER (WHERE COALESCE(r.update_count, 0) > 0)
                            AS revisited_case_count,
                        COALESCE(sum(f.completion_count), 0) AS reflection_completion_count
                    FROM committed c
                    LEFT JOIN revisions r ON r.session_id = c.id
                    LEFT JOIN reflections f ON f.session_id = c.id
                    """
                ),
                {"actor_id": actor_id},
            ).mappings().one()

            domain_rows = connection.execute(
                text(
                    """
                    SELECT
                        ci.primary_domain_code,
                        count(*) AS committed_weigh_count,
                        max(ws.committed_at) AS last_committed_at
                    FROM decision.weigh_session ws
                    JOIN content.case_item ci ON ci.id = ws.case_id
                    WHERE ws.actor_id = :actor_id
                      AND ws.state = 'COMMITTED'
                    GROUP BY ci.primary_domain_code
                    ORDER BY committed_weigh_count DESC,
                             last_committed_at DESC,
                             ci.primary_domain_code ASC
                    LIMIT :domain_limit
                    """
                ),
                {"actor_id": actor_id, "domain_limit": domain_limit},
            ).mappings().all()

            journey_rows = connection.execute(
                text(
                    """
                    SELECT
                        ws.case_id,
                        ws.case_version_id,
                        cv.title,
                        ci.primary_domain_code,
                        ws.committed_at AS initial_committed_at,
                        GREATEST(
                            ws.committed_at,
                            COALESCE(r.latest_revision_at, ws.committed_at)
                        ) AS latest_decision_at,
                        COALESCE(r.update_count, 0) AS decision_update_count,
                        COALESCE(f.completion_count, 0) > 0 AS reflection_completed
                    FROM decision.weigh_session ws
                    JOIN content.case_item ci ON ci.id = ws.case_id
                    JOIN content.case_version cv ON cv.id = ws.case_version_id
                    LEFT JOIN LATERAL (
                        SELECT
                            count(*) FILTER (WHERE dr.revision_no > 1) AS update_count,
                            max(dr.committed_at) FILTER (WHERE dr.revision_no > 1)
                                AS latest_revision_at
                        FROM decision.decision_revision dr
                        WHERE dr.session_id = ws.id
                          AND dr.actor_id = :actor_id
                    ) r ON TRUE
                    LEFT JOIN LATERAL (
                        SELECT count(*) AS completion_count
                        FROM decision.reflection_completion rc
                        WHERE rc.session_id = ws.id
                          AND rc.actor_id = :actor_id
                    ) f ON TRUE
                    WHERE ws.actor_id = :actor_id
                      AND ws.state = 'COMMITTED'
                    ORDER BY ws.committed_at DESC, ws.id DESC
                    LIMIT :recent_limit
                    """
                ),
                {"actor_id": actor_id, "recent_limit": recent_limit},
            ).mappings().all()

        return DecisionJourneySnapshot(
            actor_id=actor_id,
            decision_update_count=aggregate["decision_update_count"],
            revisited_case_count=aggregate["revisited_case_count"],
            reflection_completion_count=aggregate["reflection_completion_count"],
            domain_activity=tuple(
                DomainActivity(
                    primary_domain=row["primary_domain_code"],
                    committed_weigh_count=row["committed_weigh_count"],
                    last_committed_at=row["last_committed_at"],
                )
                for row in domain_rows
            ),
            recent_journeys=tuple(
                RecentDecisionJourney(
                    case_id=row["case_id"],
                    case_version_id=row["case_version_id"],
                    title=row["title"],
                    primary_domain=row["primary_domain_code"],
                    initial_committed_at=row["initial_committed_at"],
                    latest_decision_at=row["latest_decision_at"],
                    decision_update_count=row["decision_update_count"],
                    reflection_completed=row["reflection_completed"],
                )
                for row in journey_rows
            ),
        )
