from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from kefe_api.modules.knowledge.source_scheduler import (
    SourceAcquisitionDispatch,
    SourceAcquisitionDispatchClaim,
    SourceAcquisitionDispatchState,
    SourceAcquisitionSchedule,
    SourceAcquisitionScheduleState,
)


class PostgresSourceAcquisitionSchedulerRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_or_get_schedule(
        self,
        schedule: SourceAcquisitionSchedule,
    ) -> SourceAcquisitionSchedule:
        try:
            with self._engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO knowledge.source_acquisition_schedule (
                            id, schedule_key, adapter_code, external_locator,
                            pipeline_code, pipeline_version, configuration_hash,
                            taxonomy_version, methodology_version, locale,
                            jurisdiction_code, interval_seconds,
                            max_dispatch_attempts, state, next_due_at,
                            created_at, updated_at
                        ) VALUES (
                            :id, :schedule_key, :adapter_code, :external_locator,
                            :pipeline_code, :pipeline_version, :configuration_hash,
                            :taxonomy_version, :methodology_version, :locale,
                            :jurisdiction_code, :interval_seconds,
                            :max_dispatch_attempts, :state, :next_due_at,
                            :created_at, :updated_at
                        )
                        ON CONFLICT (schedule_key) DO NOTHING
                        """
                    ),
                    self._schedule_params(schedule),
                )
                row = connection.execute(
                    text(
                        """
                        SELECT * FROM knowledge.source_acquisition_schedule
                        WHERE schedule_key = :schedule_key
                        """
                    ),
                    {"schedule_key": schedule.schedule_key},
                ).mappings().one()
            return self._schedule_from_row(row)
        except IntegrityError as exc:
            raise ValueError("source acquisition schedule invariant violated") from exc

    def get_schedule(
        self,
        schedule_id: UUID,
    ) -> SourceAcquisitionSchedule | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT * FROM knowledge.source_acquisition_schedule
                    WHERE id = :schedule_id
                    """
                ),
                {"schedule_id": schedule_id},
            ).mappings().one_or_none()
        return self._schedule_from_row(row) if row else None

    def update_schedule_lifecycle(
        self,
        schedule: SourceAcquisitionSchedule,
    ) -> None:
        with self._engine.begin() as connection:
            current_row = connection.execute(
                text(
                    """
                    SELECT * FROM knowledge.source_acquisition_schedule
                    WHERE id = :schedule_id
                    FOR UPDATE
                    """
                ),
                {"schedule_id": schedule.id},
            ).mappings().one_or_none()
            if current_row is None:
                raise KeyError(schedule.id)
            current = self._schedule_from_row(current_row)
            if self._immutable_signature(current) != self._immutable_signature(schedule):
                raise ValueError("source acquisition schedule configuration is immutable")
            if current.next_due_at != schedule.next_due_at:
                raise ValueError("lifecycle update cannot change next_due_at")
            connection.execute(
                text(
                    """
                    UPDATE knowledge.source_acquisition_schedule
                    SET state = :state, updated_at = :updated_at
                    WHERE id = :schedule_id
                    """
                ),
                {
                    "schedule_id": schedule.id,
                    "state": schedule.state.value,
                    "updated_at": schedule.updated_at,
                },
            )

    def plan_due_once(
        self,
        *,
        at: datetime,
    ) -> SourceAcquisitionDispatch | None:
        try:
            with self._engine.begin() as connection:
                schedule_row = connection.execute(
                    text(
                        """
                        SELECT *
                        FROM knowledge.source_acquisition_schedule
                        WHERE state = 'ACTIVE' AND next_due_at <= :at
                        ORDER BY next_due_at ASC, id ASC
                        FOR UPDATE SKIP LOCKED
                        LIMIT 1
                        """
                    ),
                    {"at": at},
                ).mappings().one_or_none()
                if schedule_row is None:
                    return None
                schedule = self._schedule_from_row(schedule_row)
                dispatch_id = uuid4()
                dispatch_row = connection.execute(
                    text(
                        """
                        INSERT INTO knowledge.source_acquisition_dispatch (
                            id, schedule_id, due_at, state, attempt_count,
                            created_at, updated_at
                        ) VALUES (
                            :id, :schedule_id, :due_at, 'PENDING', 0,
                            :at, :at
                        )
                        RETURNING *
                        """
                    ),
                    {
                        "id": dispatch_id,
                        "schedule_id": schedule.id,
                        "due_at": schedule.next_due_at,
                        "at": at,
                    },
                ).mappings().one()
                connection.execute(
                    text(
                        """
                        UPDATE knowledge.source_acquisition_schedule
                        SET next_due_at = :next_due_at, updated_at = :at
                        WHERE id = :schedule_id
                        """
                    ),
                    {
                        "schedule_id": schedule.id,
                        "next_due_at": schedule.next_due_at
                        + timedelta(seconds=schedule.interval_seconds),
                        "at": at,
                    },
                )
                return self._dispatch_from_row(dispatch_row)
        except IntegrityError as exc:
            raise ValueError("source acquisition occurrence already planned") from exc

    def claim_pending_once(
        self,
        *,
        worker_ref: str,
        claimed_at: datetime,
        expires_at: datetime,
    ) -> SourceAcquisitionDispatchClaim | None:
        with self._engine.begin() as connection:
            self._recover_stale(connection, at=claimed_at, limit=1000)
            dispatch_row = connection.execute(
                text(
                    """
                    SELECT *
                    FROM knowledge.source_acquisition_dispatch
                    WHERE state = 'PENDING'
                    ORDER BY due_at ASC, id ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                    """
                )
            ).mappings().one_or_none()
            if dispatch_row is None:
                return None
            schedule_row = connection.execute(
                text(
                    """
                    SELECT * FROM knowledge.source_acquisition_schedule
                    WHERE id = :schedule_id
                    """
                ),
                {"schedule_id": dispatch_row["schedule_id"]},
            ).mappings().one()
            schedule = self._schedule_from_row(schedule_row)
            if dispatch_row["attempt_count"] >= schedule.max_dispatch_attempts:
                raise ValueError("pending dispatch exhausted its claim attempts")
            running_row = connection.execute(
                text(
                    """
                    UPDATE knowledge.source_acquisition_dispatch
                    SET state = 'RUNNING',
                        attempt_count = attempt_count + 1,
                        worker_ref = :worker_ref,
                        claimed_at = :claimed_at,
                        heartbeat_at = :claimed_at,
                        expires_at = :expires_at,
                        updated_at = :claimed_at
                    WHERE id = :dispatch_id AND state = 'PENDING'
                    RETURNING *
                    """
                ),
                {
                    "dispatch_id": dispatch_row["id"],
                    "worker_ref": worker_ref,
                    "claimed_at": claimed_at,
                    "expires_at": expires_at,
                },
            ).mappings().one()
            return SourceAcquisitionDispatchClaim(
                schedule=schedule,
                dispatch=self._dispatch_from_row(running_row),
            )

    def heartbeat(
        self,
        *,
        dispatch_id: UUID,
        worker_ref: str,
        heartbeat_at: datetime,
        expires_at: datetime,
    ) -> SourceAcquisitionDispatch:
        with self._engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE knowledge.source_acquisition_dispatch
                    SET heartbeat_at = :heartbeat_at,
                        expires_at = :expires_at,
                        updated_at = :heartbeat_at
                    WHERE id = :dispatch_id
                      AND worker_ref = :worker_ref
                      AND state = 'RUNNING'
                      AND expires_at > :heartbeat_at
                    RETURNING *
                    """
                ),
                {
                    "dispatch_id": dispatch_id,
                    "worker_ref": worker_ref,
                    "heartbeat_at": heartbeat_at,
                    "expires_at": expires_at,
                },
            ).mappings().one_or_none()
            if row is not None:
                return self._dispatch_from_row(row)
            self._raise_missing_or_inactive(connection, dispatch_id)
        raise AssertionError("unreachable")

    def complete(
        self,
        *,
        dispatch_id: UUID,
        worker_ref: str,
        completed_at: datetime,
        target_state: SourceAcquisitionDispatchState,
        source_artifact_id: UUID | None = None,
        ingestion_run_id: UUID | None = None,
        error_code: str | None = None,
    ) -> SourceAcquisitionDispatch:
        with self._engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT * FROM knowledge.source_acquisition_dispatch
                    WHERE id = :dispatch_id
                    FOR UPDATE
                    """
                ),
                {"dispatch_id": dispatch_id},
            ).mappings().one_or_none()
            if row is None:
                raise KeyError(dispatch_id)
            current = self._dispatch_from_row(row)
            completed = current.complete(
                worker_ref=worker_ref,
                at=completed_at,
                target_state=target_state,
                source_artifact_id=source_artifact_id,
                ingestion_run_id=ingestion_run_id,
                error_code=error_code,
            )
            completed_row = connection.execute(
                text(
                    """
                    UPDATE knowledge.source_acquisition_dispatch
                    SET state = :state,
                        worker_ref = NULL,
                        claimed_at = NULL,
                        heartbeat_at = NULL,
                        expires_at = NULL,
                        completed_at = :completed_at,
                        source_artifact_id = :source_artifact_id,
                        ingestion_run_id = :ingestion_run_id,
                        error_code = :error_code,
                        updated_at = :completed_at
                    WHERE id = :dispatch_id AND state = 'RUNNING'
                    RETURNING *
                    """
                ),
                {
                    "dispatch_id": dispatch_id,
                    "state": completed.state.value,
                    "completed_at": completed_at,
                    "source_artifact_id": source_artifact_id,
                    "ingestion_run_id": ingestion_run_id,
                    "error_code": error_code,
                },
            ).mappings().one()
            return self._dispatch_from_row(completed_row)

    def recover_stale(
        self,
        *,
        at: datetime,
        limit: int,
    ) -> tuple[SourceAcquisitionDispatch, ...]:
        with self._engine.begin() as connection:
            return self._recover_stale(connection, at=at, limit=limit)

    def get_dispatch(
        self,
        dispatch_id: UUID,
    ) -> SourceAcquisitionDispatch | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT * FROM knowledge.source_acquisition_dispatch
                    WHERE id = :dispatch_id
                    """
                ),
                {"dispatch_id": dispatch_id},
            ).mappings().one_or_none()
        return self._dispatch_from_row(row) if row else None

    def list_dispatches(
        self,
        schedule_id: UUID,
    ) -> tuple[SourceAcquisitionDispatch, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT * FROM knowledge.source_acquisition_dispatch
                    WHERE schedule_id = :schedule_id
                    ORDER BY due_at ASC, id ASC
                    """
                ),
                {"schedule_id": schedule_id},
            ).mappings().all()
        return tuple(self._dispatch_from_row(row) for row in rows)

    def _recover_stale(
        self,
        connection,
        *,
        at: datetime,
        limit: int,
    ) -> tuple[SourceAcquisitionDispatch, ...]:
        rows = connection.execute(
            text(
                """
                SELECT d.*, s.max_dispatch_attempts
                FROM knowledge.source_acquisition_dispatch d
                JOIN knowledge.source_acquisition_schedule s
                  ON s.id = d.schedule_id
                WHERE d.state = 'RUNNING' AND d.expires_at <= :at
                ORDER BY d.expires_at ASC, d.id ASC
                FOR UPDATE OF d SKIP LOCKED
                LIMIT :limit
                """
            ),
            {"at": at, "limit": limit},
        ).mappings().all()
        recovered: list[SourceAcquisitionDispatch] = []
        for row in rows:
            current = self._dispatch_from_row(row)
            updated = current.recover_stale(
                at=at,
                max_attempts=row["max_dispatch_attempts"],
            )
            updated_row = connection.execute(
                text(
                    """
                    UPDATE knowledge.source_acquisition_dispatch
                    SET state = :state,
                        worker_ref = NULL,
                        claimed_at = NULL,
                        heartbeat_at = NULL,
                        expires_at = NULL,
                        completed_at = :completed_at,
                        source_artifact_id = NULL,
                        ingestion_run_id = NULL,
                        error_code = :error_code,
                        updated_at = :at
                    WHERE id = :dispatch_id
                    RETURNING *
                    """
                ),
                {
                    "dispatch_id": updated.id,
                    "state": updated.state.value,
                    "completed_at": updated.completed_at,
                    "error_code": updated.error_code,
                    "at": at,
                },
            ).mappings().one()
            recovered.append(self._dispatch_from_row(updated_row))
        return tuple(recovered)

    @staticmethod
    def _raise_missing_or_inactive(connection, dispatch_id: UUID) -> None:
        exists = connection.execute(
            text(
                """
                SELECT 1 FROM knowledge.source_acquisition_dispatch
                WHERE id = :dispatch_id
                """
            ),
            {"dispatch_id": dispatch_id},
        ).scalar_one_or_none()
        if exists is None:
            raise KeyError(dispatch_id)
        raise ValueError("source acquisition dispatch lease is not active")

    @staticmethod
    def _schedule_params(schedule: SourceAcquisitionSchedule) -> dict[str, object]:
        return {
            "id": schedule.id,
            "schedule_key": schedule.schedule_key,
            "adapter_code": schedule.adapter_code,
            "external_locator": schedule.external_locator,
            "pipeline_code": schedule.pipeline_code,
            "pipeline_version": schedule.pipeline_version,
            "configuration_hash": schedule.configuration_hash,
            "taxonomy_version": schedule.taxonomy_version,
            "methodology_version": schedule.methodology_version,
            "locale": schedule.locale,
            "jurisdiction_code": schedule.jurisdiction_code,
            "interval_seconds": schedule.interval_seconds,
            "max_dispatch_attempts": schedule.max_dispatch_attempts,
            "state": schedule.state.value,
            "next_due_at": schedule.next_due_at,
            "created_at": schedule.created_at,
            "updated_at": schedule.updated_at,
        }

    @staticmethod
    def _schedule_from_row(row) -> SourceAcquisitionSchedule:
        return SourceAcquisitionSchedule(
            id=row["id"],
            schedule_key=row["schedule_key"],
            adapter_code=row["adapter_code"],
            external_locator=row["external_locator"],
            pipeline_code=row["pipeline_code"],
            pipeline_version=row["pipeline_version"],
            configuration_hash=row["configuration_hash"],
            taxonomy_version=row["taxonomy_version"],
            methodology_version=row["methodology_version"],
            locale=row["locale"],
            jurisdiction_code=row["jurisdiction_code"],
            interval_seconds=row["interval_seconds"],
            max_dispatch_attempts=row["max_dispatch_attempts"],
            state=SourceAcquisitionScheduleState(row["state"]),
            next_due_at=row["next_due_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _dispatch_from_row(row) -> SourceAcquisitionDispatch:
        return SourceAcquisitionDispatch(
            id=row["id"],
            schedule_id=row["schedule_id"],
            due_at=row["due_at"],
            state=SourceAcquisitionDispatchState(row["state"]),
            attempt_count=row["attempt_count"],
            worker_ref=row["worker_ref"],
            claimed_at=row["claimed_at"],
            heartbeat_at=row["heartbeat_at"],
            expires_at=row["expires_at"],
            completed_at=row["completed_at"],
            source_artifact_id=row["source_artifact_id"],
            ingestion_run_id=row["ingestion_run_id"],
            error_code=row["error_code"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _immutable_signature(schedule: SourceAcquisitionSchedule) -> tuple[object, ...]:
        return (
            schedule.schedule_key,
            schedule.adapter_code,
            schedule.external_locator,
            schedule.pipeline_code,
            schedule.pipeline_version,
            schedule.configuration_hash,
            schedule.taxonomy_version,
            schedule.methodology_version,
            schedule.locale,
            schedule.jurisdiction_code,
            schedule.interval_seconds,
            schedule.max_dispatch_attempts,
            schedule.created_at,
        )
