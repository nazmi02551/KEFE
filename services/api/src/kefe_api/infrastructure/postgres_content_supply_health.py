from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import Engine, text

from kefe_api.modules.content_supply_health.models import (
    ContentSupplyOperationalFacts,
)


class PostgresContentSupplyOperationalFactsRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def read_facts(
        self,
        *,
        as_of: datetime,
        failure_window_seconds: int,
    ) -> ContentSupplyOperationalFacts:
        window_start = as_of - timedelta(seconds=failure_window_seconds)
        with self._engine.connect().execution_options(
            isolation_level="REPEATABLE READ"
        ) as connection:
            with connection.begin():
                connection.execute(text("SET TRANSACTION READ ONLY"))
                row = connection.execute(
                    text(
                        """
                        SELECT
                            (
                                SELECT count(*)
                                FROM knowledge.source_acquisition_schedule
                                WHERE state = 'ACTIVE'
                            ) AS active_schedule_count,
                            (
                                SELECT count(*)
                                FROM knowledge.source_acquisition_schedule
                                WHERE state = 'PAUSED'
                            ) AS paused_schedule_count,
                            (
                                SELECT count(*)
                                FROM knowledge.source_acquisition_schedule
                                WHERE state = 'ACTIVE' AND next_due_at <= :as_of
                            ) AS due_schedule_count,
                            (
                                SELECT count(*)
                                FROM knowledge.source_acquisition_dispatch
                                WHERE state = 'PENDING'
                            ) AS pending_dispatch_count,
                            (
                                SELECT count(*)
                                FROM knowledge.source_acquisition_dispatch
                                WHERE state = 'RUNNING'
                            ) AS running_dispatch_count,
                            (
                                SELECT count(*)
                                FROM knowledge.source_acquisition_dispatch
                                WHERE state = 'RUNNING' AND expires_at <= :as_of
                            ) AS stale_dispatch_count,
                            (
                                SELECT count(*)
                                FROM knowledge.source_acquisition_dispatch
                                WHERE state IN (
                                    'RETRYABLE_FAILURE','FINAL_FAILURE','BLOCKED'
                                )
                                  AND completed_at >= :window_start
                            ) AS recent_dispatch_non_success_count,
                            (
                                SELECT count(*)
                                FROM ingestion.ingestion_run
                                WHERE state = 'QUEUED'
                            ) AS queued_ingestion_run_count,
                            (
                                SELECT count(*)
                                FROM ingestion.ingestion_run
                                WHERE state = 'RUNNING'
                            ) AS running_ingestion_run_count,
                            (
                                SELECT count(*)
                                FROM ingestion.run_lease
                                WHERE state = 'ACTIVE' AND expires_at <= :as_of
                            ) AS stale_ingestion_lease_count,
                            (
                                SELECT count(*)
                                FROM ingestion.ingestion_run
                                WHERE state IN ('FAILED_RETRYABLE','FAILED_FINAL')
                                  AND updated_at >= :window_start
                            ) AS recent_failed_ingestion_run_count,
                            (
                                SELECT count(*)
                                FROM ingestion.proposal proposal
                                WHERE NOT EXISTS (
                                    SELECT 1
                                    FROM ingestion.proposal_review_decision decision
                                    WHERE decision.proposal_id = proposal.id
                                )
                            ) AS unreviewed_proposal_count,
                            (
                                SELECT count(*)
                                FROM ingestion.content_supply_cycle
                                WHERE state = 'RUNNING'
                            ) AS running_cycle_count,
                            (
                                SELECT count(*)
                                FROM ingestion.content_supply_cycle
                                WHERE state = 'RUNNING' AND expires_at <= :as_of
                            ) AS stale_cycle_count,
                            (
                                SELECT count(*)
                                FROM ingestion.content_supply_cycle
                                WHERE state IN ('DEGRADED','FAILED','ABANDONED')
                                  AND completed_at >= :window_start
                            ) AS recent_non_success_cycle_count,
                            (
                                SELECT state
                                FROM ingestion.content_supply_cycle
                                WHERE state <> 'RUNNING'
                                ORDER BY completed_at DESC, id DESC
                                LIMIT 1
                            ) AS latest_terminal_cycle_state,
                            (
                                SELECT completed_at
                                FROM ingestion.content_supply_cycle
                                WHERE state <> 'RUNNING'
                                ORDER BY completed_at DESC, id DESC
                                LIMIT 1
                            ) AS latest_terminal_cycle_completed_at
                        """
                    ),
                    {"as_of": as_of, "window_start": window_start},
                ).mappings().one()

        return ContentSupplyOperationalFacts(
            as_of=as_of,
            active_schedule_count=row["active_schedule_count"],
            paused_schedule_count=row["paused_schedule_count"],
            due_schedule_count=row["due_schedule_count"],
            pending_dispatch_count=row["pending_dispatch_count"],
            running_dispatch_count=row["running_dispatch_count"],
            stale_dispatch_count=row["stale_dispatch_count"],
            recent_dispatch_non_success_count=(
                row["recent_dispatch_non_success_count"]
            ),
            queued_ingestion_run_count=row["queued_ingestion_run_count"],
            running_ingestion_run_count=row["running_ingestion_run_count"],
            stale_ingestion_lease_count=row["stale_ingestion_lease_count"],
            recent_failed_ingestion_run_count=(
                row["recent_failed_ingestion_run_count"]
            ),
            unreviewed_proposal_count=row["unreviewed_proposal_count"],
            running_cycle_count=row["running_cycle_count"],
            stale_cycle_count=row["stale_cycle_count"],
            recent_non_success_cycle_count=(
                row["recent_non_success_cycle_count"]
            ),
            latest_terminal_cycle_state=row["latest_terminal_cycle_state"],
            latest_terminal_cycle_completed_at=(
                row["latest_terminal_cycle_completed_at"]
            ),
        )
