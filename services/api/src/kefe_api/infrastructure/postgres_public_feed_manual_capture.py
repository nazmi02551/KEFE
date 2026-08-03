from __future__ import annotations

from uuid import UUID

from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError

from kefe_api.modules.knowledge.public_feed_manual_capture import (
    PublicFeedManualCaptureAuditEntry,
)


class PostgresPublicFeedManualCaptureAuditRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def append(self, entry: PublicFeedManualCaptureAuditEntry) -> None:
        try:
            with self._engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO knowledge.public_feed_manual_capture_audit (
                            event_id, execution_id, catalog_entry_id, feed_code,
                            configuration_hash, actor_ref, trace_id, outcome,
                            source_artifact_id, ingestion_run_id, duration_ms,
                            error_code, occurred_at
                        ) VALUES (
                            :event_id, :execution_id, :catalog_entry_id,
                            :feed_code, :configuration_hash, :actor_ref,
                            :trace_id, :outcome, :source_artifact_id,
                            :ingestion_run_id, :duration_ms, :error_code,
                            :occurred_at
                        )
                        """
                    ),
                    {
                        "event_id": entry.event_id,
                        "execution_id": entry.execution_id,
                        "catalog_entry_id": entry.catalog_entry_id,
                        "feed_code": entry.feed_code,
                        "configuration_hash": entry.configuration_hash,
                        "actor_ref": entry.actor_ref,
                        "trace_id": entry.trace_id,
                        "outcome": entry.outcome,
                        "source_artifact_id": entry.source_artifact_id,
                        "ingestion_run_id": entry.ingestion_run_id,
                        "duration_ms": entry.duration_ms,
                        "error_code": entry.error_code,
                        "occurred_at": entry.occurred_at,
                    },
                )
        except IntegrityError as exc:
            raise ValueError("manual capture audit append failed") from exc

    def list_entries(
        self,
        catalog_entry_id: UUID | None = None,
    ) -> tuple[PublicFeedManualCaptureAuditEntry, ...]:
        query = """
            SELECT event_id, execution_id, catalog_entry_id, feed_code,
                   configuration_hash, actor_ref, trace_id, outcome,
                   source_artifact_id, ingestion_run_id, duration_ms,
                   error_code, occurred_at
            FROM knowledge.public_feed_manual_capture_audit
        """
        parameters: dict[str, object] = {}
        if catalog_entry_id is not None:
            query += " WHERE catalog_entry_id = :catalog_entry_id"
            parameters["catalog_entry_id"] = catalog_entry_id
        query += " ORDER BY audit_seq"
        with self._engine.connect() as connection:
            rows = connection.execute(text(query), parameters).mappings().all()
        return tuple(
            PublicFeedManualCaptureAuditEntry(
                event_id=row["event_id"],
                execution_id=row["execution_id"],
                catalog_entry_id=row["catalog_entry_id"],
                feed_code=row["feed_code"],
                configuration_hash=row["configuration_hash"],
                actor_ref=row["actor_ref"],
                trace_id=row["trace_id"],
                outcome=row["outcome"],
                source_artifact_id=row["source_artifact_id"],
                ingestion_run_id=row["ingestion_run_id"],
                duration_ms=row["duration_ms"],
                error_code=row["error_code"],
                occurred_at=row["occurred_at"],
            )
            for row in rows
        )


__all__ = ["PostgresPublicFeedManualCaptureAuditRepository"]
