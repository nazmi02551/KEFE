from __future__ import annotations

import json
from types import MappingProxyType
from uuid import UUID

from sqlalchemy import Connection, Engine, text

from kefe_api.modules.content_config.models import (
    ContentConfigLifecycle,
    ContentConfigurationAuditEntry,
    ContentConfigurationSnapshot,
)


class PostgresContentConfigurationRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def current_published(self) -> ContentConfigurationSnapshot | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT id, version_no, state, payload, created_at, published_at
                    FROM content_config.snapshot
                    WHERE state = 'PUBLISHED'
                    LIMIT 1
                    """
                )
            ).mappings().one_or_none()
        return self._snapshot(row) if row else None

    def get_snapshot(self, snapshot_id: UUID) -> ContentConfigurationSnapshot | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT id, version_no, state, payload, created_at, published_at
                    FROM content_config.snapshot
                    WHERE id = :snapshot_id
                    """
                ),
                {"snapshot_id": snapshot_id},
            ).mappings().one_or_none()
        return self._snapshot(row) if row else None

    def next_version_no(self) -> int:
        with self._engine.connect() as connection:
            value = connection.execute(
                text("SELECT COALESCE(MAX(version_no), 0) + 1 FROM content_config.snapshot")
            ).scalar_one()
        return int(value)

    def save_draft(self, snapshot: ContentConfigurationSnapshot) -> None:
        payload = json.dumps(self._payload(snapshot))
        with self._engine.begin() as connection:
            existing = connection.execute(
                text("SELECT state FROM content_config.snapshot WHERE id = :id FOR UPDATE"),
                {"id": snapshot.id},
            ).scalar_one_or_none()
            if existing is not None and existing != ContentConfigLifecycle.DRAFT.value:
                raise ValueError("published content configuration is immutable")
            if snapshot.state is not ContentConfigLifecycle.DRAFT:
                raise ValueError("save_draft accepts only DRAFT snapshots")
            connection.execute(
                text(
                    """
                    INSERT INTO content_config.snapshot (
                        id, version_no, state, payload, created_at, published_at
                    ) VALUES (
                        :id, :version_no, 'DRAFT', CAST(:payload AS jsonb), :created_at, NULL
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        payload = EXCLUDED.payload
                    """
                ),
                {
                    "id": snapshot.id,
                    "version_no": snapshot.version_no,
                    "payload": payload,
                    "created_at": snapshot.created_at,
                },
            )

    def publish_atomically(
        self,
        *,
        snapshot: ContentConfigurationSnapshot,
        audit: ContentConfigurationAuditEntry,
    ) -> tuple[ContentConfigurationSnapshot, ContentConfigurationSnapshot | None]:
        with self._engine.begin() as connection:
            draft_row = connection.execute(
                text(
                    """
                    SELECT id, version_no, state, payload, created_at, published_at
                    FROM content_config.snapshot
                    WHERE id = :id
                    FOR UPDATE
                    """
                ),
                {"id": snapshot.id},
            ).mappings().one_or_none()
            if draft_row is None or draft_row["state"] != ContentConfigLifecycle.DRAFT.value:
                raise ValueError("configuration lifecycle changed concurrently")

            previous_row = connection.execute(
                text(
                    """
                    SELECT id, version_no, state, payload, created_at, published_at
                    FROM content_config.snapshot
                    WHERE state = 'PUBLISHED'
                    FOR UPDATE
                    """
                )
            ).mappings().one_or_none()
            previous = self._snapshot(previous_row) if previous_row else None
            if previous is not None:
                connection.execute(
                    text(
                        """
                        UPDATE content_config.snapshot
                        SET state = 'SUPERSEDED'
                        WHERE id = :id AND state = 'PUBLISHED'
                        """
                    ),
                    {"id": previous.id},
                )

            connection.execute(
                text(
                    """
                    UPDATE content_config.snapshot
                    SET state = 'PUBLISHED', published_at = :published_at
                    WHERE id = :id AND state = 'DRAFT'
                    """
                ),
                {"id": snapshot.id, "published_at": snapshot.published_at},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO content_config.audit (
                        id, snapshot_id, actor_ref, command, previous_state,
                        new_state, superseded_snapshot_id, occurred_at
                    ) VALUES (
                        :id, :snapshot_id, :actor_ref, :command, :previous_state,
                        :new_state, :superseded_snapshot_id, :occurred_at
                    )
                    """
                ),
                {
                    "id": audit.id,
                    "snapshot_id": audit.snapshot_id,
                    "actor_ref": audit.actor_ref,
                    "command": audit.command,
                    "previous_state": audit.previous_state.value if audit.previous_state else None,
                    "new_state": audit.new_state.value,
                    "superseded_snapshot_id": audit.superseded_snapshot_id,
                    "occurred_at": audit.occurred_at,
                },
            )
        return snapshot, previous

    def list_audit(self) -> tuple[ContentConfigurationAuditEntry, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT id, snapshot_id, actor_ref, command, previous_state,
                           new_state, superseded_snapshot_id, occurred_at
                    FROM content_config.audit
                    ORDER BY occurred_at, id
                    """
                )
            ).mappings().all()
        return tuple(
            ContentConfigurationAuditEntry(
                id=row["id"],
                snapshot_id=row["snapshot_id"],
                actor_ref=row["actor_ref"],
                command=row["command"],
                previous_state=(
                    ContentConfigLifecycle(row["previous_state"])
                    if row["previous_state"]
                    else None
                ),
                new_state=ContentConfigLifecycle(row["new_state"]),
                superseded_snapshot_id=row["superseded_snapshot_id"],
                occurred_at=row["occurred_at"],
            )
            for row in rows
        )

    @staticmethod
    def seed_baseline_if_empty(
        engine: Engine,
        snapshot: ContentConfigurationSnapshot,
    ) -> None:
        with engine.begin() as connection:
            count = connection.execute(text("SELECT count(*) FROM content_config.snapshot")).scalar_one()
            if count:
                return
            connection.execute(
                text(
                    """
                    INSERT INTO content_config.snapshot (
                        id, version_no, state, payload, created_at, published_at
                    ) VALUES (
                        :id, :version_no, 'PUBLISHED', CAST(:payload AS jsonb),
                        :created_at, :published_at
                    )
                    """
                ),
                {
                    "id": snapshot.id,
                    "version_no": snapshot.version_no,
                    "payload": json.dumps(PostgresContentConfigurationRepository._payload(snapshot)),
                    "created_at": snapshot.created_at,
                    "published_at": snapshot.published_at,
                },
            )

    @staticmethod
    def _payload(snapshot: ContentConfigurationSnapshot) -> dict[str, object]:
        return {
            "domains": sorted(snapshot.domains),
            "base_formats": sorted(snapshot.base_formats),
            "modifiers": sorted(snapshot.modifiers),
            "risks": sorted(snapshot.risks),
            "claim_states": sorted(snapshot.claim_states),
            "review_modes": sorted(snapshot.review_modes),
            "allowed_modifiers": {
                key: sorted(value) for key, value in snapshot.allowed_modifiers.items()
            },
            "review_modes_by_risk": {
                key: sorted(value) for key, value in snapshot.review_modes_by_risk.items()
            },
        }

    @staticmethod
    def _snapshot(row) -> ContentConfigurationSnapshot:
        payload = row["payload"]
        return ContentConfigurationSnapshot(
            id=row["id"],
            version_no=row["version_no"],
            state=ContentConfigLifecycle(row["state"]),
            domains=frozenset(payload["domains"]),
            base_formats=frozenset(payload["base_formats"]),
            modifiers=frozenset(payload["modifiers"]),
            risks=frozenset(payload["risks"]),
            claim_states=frozenset(payload["claim_states"]),
            review_modes=frozenset(payload["review_modes"]),
            allowed_modifiers=MappingProxyType(
                {key: frozenset(value) for key, value in payload["allowed_modifiers"].items()}
            ),
            review_modes_by_risk=MappingProxyType(
                {key: frozenset(value) for key, value in payload["review_modes_by_risk"].items()}
            ),
            created_at=row["created_at"],
            published_at=row["published_at"],
        )
