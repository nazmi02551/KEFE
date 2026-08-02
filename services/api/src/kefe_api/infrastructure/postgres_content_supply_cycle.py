from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Engine, text

from kefe_api.modules.content_supply_cycle.models import (
    ContentSupplyCycle,
    ContentSupplyCycleCounters,
    ContentSupplyCycleState,
)


class PostgresContentSupplyCycleRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create(self, cycle: ContentSupplyCycle) -> ContentSupplyCycle:
        with self._engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    INSERT INTO ingestion.content_supply_cycle (
                        id, worker_ref, plan_hash, state,
                        planned_count,
                        dispatch_attempted_count,
                        dispatch_succeeded_count,
                        dispatch_non_success_count,
                        ingestion_attempted_count,
                        ingestion_succeeded_count,
                        ingestion_non_success_count,
                        started_at, heartbeat_at, expires_at,
                        completed_at, error_code
                    ) VALUES (
                        :id, :worker_ref, :plan_hash, :state,
                        :planned_count,
                        :dispatch_attempted_count,
                        :dispatch_succeeded_count,
                        :dispatch_non_success_count,
                        :ingestion_attempted_count,
                        :ingestion_succeeded_count,
                        :ingestion_non_success_count,
                        :started_at, :heartbeat_at, :expires_at,
                        :completed_at, :error_code
                    )
                    RETURNING *
                    """
                ),
                self._params(cycle),
            ).mappings().one()
        return self._from_row(row)

    def get(self, cycle_id: UUID) -> ContentSupplyCycle | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT *
                    FROM ingestion.content_supply_cycle
                    WHERE id = :cycle_id
                    """
                ),
                {"cycle_id": cycle_id},
            ).mappings().one_or_none()
        return self._from_row(row) if row is not None else None

    def heartbeat(
        self,
        *,
        cycle_id: UUID,
        worker_ref: str,
        heartbeat_at: datetime,
        expires_at: datetime,
        counters: ContentSupplyCycleCounters,
    ) -> ContentSupplyCycle:
        with self._engine.begin() as connection:
            cycle = self._lock_cycle(connection, cycle_id)
            updated = cycle.heartbeat(
                worker_ref=worker_ref,
                at=heartbeat_at,
                expires_at=expires_at,
                counters=counters,
            )
            return self._update(connection, updated)

    def complete(
        self,
        *,
        cycle_id: UUID,
        worker_ref: str,
        completed_at: datetime,
        state: ContentSupplyCycleState,
        counters: ContentSupplyCycleCounters,
        error_code: str | None = None,
    ) -> ContentSupplyCycle:
        with self._engine.begin() as connection:
            cycle = self._lock_cycle(connection, cycle_id)
            updated = cycle.complete(
                worker_ref=worker_ref,
                at=completed_at,
                state=state,
                counters=counters,
                error_code=error_code,
            )
            return self._update(connection, updated)

    def recover_stale(
        self,
        *,
        at: datetime,
        limit: int,
    ) -> tuple[ContentSupplyCycle, ...]:
        if limit < 1:
            raise ValueError("stale recovery limit must be positive")
        with self._engine.begin() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT *
                    FROM ingestion.content_supply_cycle
                    WHERE state = 'RUNNING'
                      AND expires_at <= :at
                    ORDER BY expires_at, id
                    FOR UPDATE SKIP LOCKED
                    LIMIT :limit
                    """
                ),
                {"at": at, "limit": limit},
            ).mappings().all()
            recovered = tuple(
                self._update(connection, self._from_row(row).abandon(at=at))
                for row in rows
            )
        return recovered

    @staticmethod
    def _lock_cycle(connection, cycle_id: UUID) -> ContentSupplyCycle:
        row = connection.execute(
            text(
                """
                SELECT *
                FROM ingestion.content_supply_cycle
                WHERE id = :cycle_id
                FOR UPDATE
                """
            ),
            {"cycle_id": cycle_id},
        ).mappings().one_or_none()
        if row is None:
            raise KeyError(cycle_id)
        return PostgresContentSupplyCycleRepository._from_row(row)

    @staticmethod
    def _update(connection, cycle: ContentSupplyCycle) -> ContentSupplyCycle:
        row = connection.execute(
            text(
                """
                UPDATE ingestion.content_supply_cycle
                SET state = :state,
                    planned_count = :planned_count,
                    dispatch_attempted_count = :dispatch_attempted_count,
                    dispatch_succeeded_count = :dispatch_succeeded_count,
                    dispatch_non_success_count = :dispatch_non_success_count,
                    ingestion_attempted_count = :ingestion_attempted_count,
                    ingestion_succeeded_count = :ingestion_succeeded_count,
                    ingestion_non_success_count = :ingestion_non_success_count,
                    heartbeat_at = :heartbeat_at,
                    expires_at = :expires_at,
                    completed_at = :completed_at,
                    error_code = :error_code
                WHERE id = :id
                RETURNING *
                """
            ),
            PostgresContentSupplyCycleRepository._params(cycle),
        ).mappings().one()
        return PostgresContentSupplyCycleRepository._from_row(row)

    @staticmethod
    def _params(cycle: ContentSupplyCycle) -> dict[str, object]:
        counters = cycle.counters
        return {
            "id": cycle.id,
            "worker_ref": cycle.worker_ref,
            "plan_hash": cycle.plan_hash,
            "state": cycle.state.value,
            "planned_count": counters.planned_count,
            "dispatch_attempted_count": counters.dispatch_attempted_count,
            "dispatch_succeeded_count": counters.dispatch_succeeded_count,
            "dispatch_non_success_count": counters.dispatch_non_success_count,
            "ingestion_attempted_count": counters.ingestion_attempted_count,
            "ingestion_succeeded_count": counters.ingestion_succeeded_count,
            "ingestion_non_success_count": counters.ingestion_non_success_count,
            "started_at": cycle.started_at,
            "heartbeat_at": cycle.heartbeat_at,
            "expires_at": cycle.expires_at,
            "completed_at": cycle.completed_at,
            "error_code": cycle.error_code,
        }

    @staticmethod
    def _from_row(row) -> ContentSupplyCycle:
        return ContentSupplyCycle(
            id=row["id"],
            worker_ref=row["worker_ref"],
            plan_hash=row["plan_hash"],
            state=ContentSupplyCycleState(row["state"]),
            counters=ContentSupplyCycleCounters(
                planned_count=row["planned_count"],
                dispatch_attempted_count=row["dispatch_attempted_count"],
                dispatch_succeeded_count=row["dispatch_succeeded_count"],
                dispatch_non_success_count=row["dispatch_non_success_count"],
                ingestion_attempted_count=row["ingestion_attempted_count"],
                ingestion_succeeded_count=row["ingestion_succeeded_count"],
                ingestion_non_success_count=row["ingestion_non_success_count"],
            ),
            started_at=row["started_at"],
            heartbeat_at=row["heartbeat_at"],
            expires_at=row["expires_at"],
            completed_at=row["completed_at"],
            error_code=row["error_code"],
        )
