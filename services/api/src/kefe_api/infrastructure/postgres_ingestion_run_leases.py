from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from kefe_api.modules.ingestion_orchestration.leases import (
    IngestionRunLease,
    IngestionRunLeaseClaim,
    IngestionRunLeaseReleaseDisposition,
    IngestionRunLeaseState,
)
from kefe_api.modules.ingestion_orchestration.models import (
    IngestionRun,
    IngestionRunState,
    InputArtifactKind,
)

_TERMINAL_RELEASE_STATES = frozenset(
    {
        IngestionRunState.SUCCEEDED,
        IngestionRunState.FAILED_RETRYABLE,
        IngestionRunState.FAILED_FINAL,
        IngestionRunState.CANCELED,
    }
)


class PostgresIngestionRunLeaseRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def claim_next(
        self,
        *,
        worker_ref: str,
        claimed_at: datetime,
        expires_at: datetime,
        pipeline_code: str | None = None,
    ) -> IngestionRunLeaseClaim | None:
        try:
            with self._engine.begin() as connection:
                self._recover_expired(connection, at=claimed_at, limit=1000)
                clauses = [
                    "r.state = 'QUEUED'",
                    "NOT EXISTS ("
                    "SELECT 1 FROM ingestion.run_lease active "
                    "WHERE active.run_id = r.id AND active.state = 'ACTIVE'"
                    ")",
                ]
                params: dict[str, object] = {
                    "claimed_at": claimed_at,
                    "expires_at": expires_at,
                }
                if pipeline_code is not None:
                    clauses.append("r.pipeline_code = :pipeline_code")
                    params["pipeline_code"] = pipeline_code
                row = connection.execute(
                    text(
                        "SELECT r.* FROM ingestion.ingestion_run r WHERE "
                        + " AND ".join(clauses)
                        + " ORDER BY r.updated_at ASC, r.id ASC "
                        "FOR UPDATE SKIP LOCKED LIMIT 1"
                    ),
                    params,
                ).mappings().one_or_none()
                if row is None:
                    return None

                connection.execute(
                    text(
                        """
                        UPDATE ingestion.ingestion_run
                        SET state = 'RUNNING', updated_at = :claimed_at
                        WHERE id = :run_id AND state = 'QUEUED'
                        """
                    ),
                    {"run_id": row["id"], "claimed_at": claimed_at},
                )
                lease_id = uuid4()
                lease_row = connection.execute(
                    text(
                        """
                        INSERT INTO ingestion.run_lease (
                            id, run_id, worker_ref, state,
                            claimed_at, heartbeat_at, expires_at
                        ) VALUES (
                            :id, :run_id, :worker_ref, 'ACTIVE',
                            :claimed_at, :claimed_at, :expires_at
                        )
                        RETURNING *
                        """
                    ),
                    {
                        "id": lease_id,
                        "run_id": row["id"],
                        "worker_ref": worker_ref,
                        "claimed_at": claimed_at,
                        "expires_at": expires_at,
                    },
                ).mappings().one()
                running_row = dict(row)
                running_row["state"] = IngestionRunState.RUNNING.value
                running_row["updated_at"] = claimed_at
                return IngestionRunLeaseClaim(
                    run=self._run_from_row(running_row),
                    lease=self._lease_from_row(lease_row),
                )
        except IntegrityError as exc:
            raise ValueError("ingestion run lease persistence invariant violated") from exc

    def heartbeat(
        self,
        *,
        lease_id: UUID,
        worker_ref: str,
        heartbeat_at: datetime,
        expires_at: datetime,
    ) -> IngestionRunLease:
        with self._engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE ingestion.run_lease
                    SET heartbeat_at = :heartbeat_at, expires_at = :expires_at
                    WHERE id = :lease_id
                      AND worker_ref = :worker_ref
                      AND state = 'ACTIVE'
                      AND expires_at > :heartbeat_at
                    RETURNING *
                    """
                ),
                {
                    "lease_id": lease_id,
                    "worker_ref": worker_ref,
                    "heartbeat_at": heartbeat_at,
                    "expires_at": expires_at,
                },
            ).mappings().one_or_none()
            if row is not None:
                return self._lease_from_row(row)
            self._raise_missing_or_inactive(connection, lease_id)
        raise AssertionError("unreachable")

    def assert_active(
        self,
        *,
        lease_id: UUID,
        worker_ref: str,
        at: datetime,
    ) -> IngestionRunLease:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT * FROM ingestion.run_lease
                    WHERE id = :lease_id
                      AND worker_ref = :worker_ref
                      AND state = 'ACTIVE'
                      AND expires_at > :at
                    """
                ),
                {"lease_id": lease_id, "worker_ref": worker_ref, "at": at},
            ).mappings().one_or_none()
            if row is not None:
                return self._lease_from_row(row)
            self._raise_missing_or_inactive(connection, lease_id)
        raise AssertionError("unreachable")

    def release(
        self,
        *,
        lease_id: UUID,
        worker_ref: str,
        released_at: datetime,
        disposition: IngestionRunLeaseReleaseDisposition,
    ) -> IngestionRunLease:
        with self._engine.begin() as connection:
            lease_row = connection.execute(
                text(
                    """
                    SELECT * FROM ingestion.run_lease
                    WHERE id = :lease_id
                    FOR UPDATE
                    """
                ),
                {"lease_id": lease_id},
            ).mappings().one_or_none()
            if lease_row is None:
                raise KeyError(lease_id)
            lease = self._lease_from_row(lease_row)
            if lease.worker_ref != worker_ref or not lease.is_active_at(released_at):
                raise ValueError("ingestion run lease is not active for this worker")

            run_state_value = connection.execute(
                text(
                    """
                    SELECT state FROM ingestion.ingestion_run
                    WHERE id = :run_id
                    FOR UPDATE
                    """
                ),
                {"run_id": lease.run_id},
            ).scalar_one_or_none()
            if run_state_value is None:
                raise KeyError(lease.run_id)
            run_state = IngestionRunState(run_state_value)
            if disposition is IngestionRunLeaseReleaseDisposition.REQUEUE:
                if run_state is not IngestionRunState.RUNNING:
                    raise ValueError("REQUEUE release requires RUNNING run")
                connection.execute(
                    text(
                        """
                        UPDATE ingestion.ingestion_run
                        SET state = 'QUEUED', updated_at = :released_at
                        WHERE id = :run_id
                        """
                    ),
                    {"run_id": lease.run_id, "released_at": released_at},
                )
            elif run_state not in _TERMINAL_RELEASE_STATES:
                raise ValueError("TERMINAL release requires terminal run")

            released_row = connection.execute(
                text(
                    """
                    UPDATE ingestion.run_lease
                    SET state = 'RELEASED',
                        released_at = :released_at,
                        release_disposition = :disposition
                    WHERE id = :lease_id AND state = 'ACTIVE'
                    RETURNING *
                    """
                ),
                {
                    "lease_id": lease_id,
                    "released_at": released_at,
                    "disposition": disposition.value,
                },
            ).mappings().one()
            return self._lease_from_row(released_row)

    def recover_expired(
        self,
        *,
        at: datetime,
        limit: int,
    ) -> tuple[IngestionRunLease, ...]:
        with self._engine.begin() as connection:
            return self._recover_expired(connection, at=at, limit=limit)

    def get_lease(self, lease_id: UUID) -> IngestionRunLease | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text("SELECT * FROM ingestion.run_lease WHERE id = :lease_id"),
                {"lease_id": lease_id},
            ).mappings().one_or_none()
        return self._lease_from_row(row) if row else None

    def _recover_expired(
        self,
        connection,
        *,
        at: datetime,
        limit: int,
    ) -> tuple[IngestionRunLease, ...]:
        rows = connection.execute(
            text(
                """
                WITH due AS (
                    SELECT id, run_id
                    FROM ingestion.run_lease
                    WHERE state = 'ACTIVE' AND expires_at <= :at
                    ORDER BY expires_at ASC, id ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT :limit
                )
                UPDATE ingestion.run_lease lease
                SET state = 'EXPIRED', released_at = :at
                FROM due
                WHERE lease.id = due.id
                RETURNING lease.*
                """
            ),
            {"at": at, "limit": limit},
        ).mappings().all()
        if rows:
            connection.execute(
                text(
                    """
                    UPDATE ingestion.ingestion_run run
                    SET state = 'QUEUED', updated_at = :at
                    WHERE run.state = 'RUNNING'
                      AND run.id = ANY(:run_ids)
                    """
                ),
                {"at": at, "run_ids": [row["run_id"] for row in rows]},
            )
        return tuple(self._lease_from_row(row) for row in rows)

    @staticmethod
    def _raise_missing_or_inactive(connection, lease_id: UUID) -> None:
        exists = connection.execute(
            text("SELECT 1 FROM ingestion.run_lease WHERE id = :lease_id"),
            {"lease_id": lease_id},
        ).scalar_one_or_none()
        if exists is None:
            raise KeyError(lease_id)
        raise ValueError("ingestion run lease is not active for this worker")

    @staticmethod
    def _lease_from_row(row) -> IngestionRunLease:
        return IngestionRunLease(
            id=row["id"],
            run_id=row["run_id"],
            worker_ref=row["worker_ref"],
            state=IngestionRunLeaseState(row["state"]),
            claimed_at=row["claimed_at"],
            heartbeat_at=row["heartbeat_at"],
            expires_at=row["expires_at"],
            released_at=row["released_at"],
            release_disposition=(
                IngestionRunLeaseReleaseDisposition(row["release_disposition"])
                if row["release_disposition"] is not None
                else None
            ),
        )

    @staticmethod
    def _run_from_row(row) -> IngestionRun:
        source_id = row["source_artifact_id"]
        normalized_id = row["normalized_artifact_id"]
        return IngestionRun(
            id=row["id"],
            run_key=row["run_key"],
            input_artifact_kind=(
                InputArtifactKind.SOURCE_ARTIFACT
                if source_id is not None
                else InputArtifactKind.NORMALIZED_ARTIFACT
            ),
            input_artifact_id=source_id if source_id is not None else normalized_id,
            input_content_hash=row["input_content_hash"],
            pipeline_code=row["pipeline_code"],
            pipeline_version=row["pipeline_version"],
            configuration_hash=row["configuration_hash"],
            taxonomy_version=row["taxonomy_version"],
            methodology_version=row["methodology_version"],
            locale=row["locale"],
            jurisdiction_code=row["jurisdiction_code"],
            state=IngestionRunState(row["state"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
