from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, Engine, text

from kefe_api.modules.content_configuration.models import (
    ContentConfigLifecycle,
    ContentConfigurationAuditEntry,
    ContentConfigurationSnapshot,
    TaxonomyItem,
    TopicItem,
)


class PostgresContentConfigurationRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def current_published(self) -> ContentConfigurationSnapshot | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT id, version_no, lifecycle_state, aggregate, created_by,
                           created_at, published_at, cloned_from_version_id
                    FROM content_config.configuration_version
                    WHERE lifecycle_state = 'PUBLISHED'
                    LIMIT 1
                    """
                )
            ).mappings().one_or_none()
        return self._from_row(row) if row else None

    def get(self, version_id: UUID) -> ContentConfigurationSnapshot | None:
        with self._engine.connect() as connection:
            row = self._version_row(connection, version_id)
        return self._from_row(row) if row else None

    def list_versions(self) -> tuple[ContentConfigurationSnapshot, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT id, version_no, lifecycle_state, aggregate, created_by,
                           created_at, published_at, cloned_from_version_id
                    FROM content_config.configuration_version
                    ORDER BY version_no
                    """
                )
            ).mappings().all()
        return tuple(self._from_row(row) for row in rows)

    def next_version_no(self) -> int:
        with self._engine.begin() as connection:
            value = connection.execute(
                text("SELECT nextval('content_config.configuration_version_no_seq')")
            ).scalar_one()
        return int(value)

    def save_draft(
        self,
        snapshot: ContentConfigurationSnapshot,
        *,
        audit: ContentConfigurationAuditEntry,
    ) -> None:
        if snapshot.state is not ContentConfigLifecycle.DRAFT:
            raise ValueError("new configuration version must be DRAFT")
        with self._engine.begin() as connection:
            self._insert_version(connection, snapshot)
            self._insert_audit(connection, audit)

    def replace_draft(
        self,
        snapshot: ContentConfigurationSnapshot,
        *,
        audit: ContentConfigurationAuditEntry,
    ) -> None:
        with self._engine.begin() as connection:
            row = self._lock_version(connection, snapshot.id)
            if row is None:
                raise KeyError(snapshot.id)
            if row["lifecycle_state"] != ContentConfigLifecycle.DRAFT.value:
                raise ValueError("only DRAFT content configuration may be replaced")
            if int(row["version_no"]) != snapshot.version_no:
                raise ValueError("stable configuration version number cannot change")
            connection.execute(
                text(
                    """
                    UPDATE content_config.configuration_version
                    SET aggregate = CAST(:aggregate AS jsonb), updated_at = now()
                    WHERE id = :version_id
                    """
                ),
                {
                    "version_id": snapshot.id,
                    "aggregate": json.dumps(self._document(snapshot)),
                },
            )
            self._insert_audit(connection, audit)

    def publish_atomically(
        self,
        *,
        snapshot: ContentConfigurationSnapshot,
        audit: ContentConfigurationAuditEntry,
    ) -> tuple[ContentConfigurationSnapshot, ContentConfigurationSnapshot | None]:
        with self._engine.begin() as connection:
            target = self._lock_version(connection, snapshot.id)
            if target is None:
                raise KeyError(snapshot.id)
            if target["lifecycle_state"] != ContentConfigLifecycle.DRAFT.value:
                raise ValueError("only DRAFT content configuration may be published")

            previous_row = connection.execute(
                text(
                    """
                    SELECT id, version_no, lifecycle_state, aggregate, created_by,
                           created_at, published_at, cloned_from_version_id
                    FROM content_config.configuration_version
                    WHERE lifecycle_state = 'PUBLISHED'
                    FOR UPDATE
                    """
                )
            ).mappings().one_or_none()
            previous = self._from_row(previous_row) if previous_row else None

            if previous is not None:
                connection.execute(
                    text(
                        """
                        UPDATE content_config.configuration_version
                        SET lifecycle_state = 'SUPERSEDED', updated_at = now()
                        WHERE id = :previous_id
                        """
                    ),
                    {"previous_id": previous.id},
                )

            connection.execute(
                text(
                    """
                    UPDATE content_config.configuration_version
                    SET lifecycle_state = 'PUBLISHED',
                        aggregate = CAST(:aggregate AS jsonb),
                        published_at = :published_at,
                        updated_at = now()
                    WHERE id = :version_id
                    """
                ),
                {
                    "version_id": snapshot.id,
                    "aggregate": json.dumps(self._document(snapshot)),
                    "published_at": snapshot.published_at,
                },
            )
            self._insert_audit(connection, audit)
        return snapshot, previous

    def list_audit(self) -> tuple[ContentConfigurationAuditEntry, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT audit_id, config_version_id, actor_ref, command,
                           previous_state, new_state, rationale, occurred_at
                    FROM content_config.configuration_audit
                    ORDER BY audit_seq
                    """
                )
            ).mappings().all()
        return tuple(
            ContentConfigurationAuditEntry(
                audit_id=row["audit_id"],
                config_version_id=row["config_version_id"],
                actor_ref=row["actor_ref"],
                command=row["command"],
                previous_state=(
                    ContentConfigLifecycle(row["previous_state"])
                    if row["previous_state"] is not None
                    else None
                ),
                new_state=ContentConfigLifecycle(row["new_state"]),
                rationale=row["rationale"],
                occurred_at=row["occurred_at"],
            )
            for row in rows
        )

    def seed_if_empty(self, snapshot: ContentConfigurationSnapshot) -> None:
        with self._engine.begin() as connection:
            count = connection.execute(
                text("SELECT count(*) FROM content_config.configuration_version")
            ).scalar_one()
            if count:
                return
            self._insert_version(connection, snapshot)

    def _version_row(self, connection: Connection, version_id: UUID):
        return connection.execute(
            text(
                """
                SELECT id, version_no, lifecycle_state, aggregate, created_by,
                       created_at, published_at, cloned_from_version_id
                FROM content_config.configuration_version
                WHERE id = :version_id
                """
            ),
            {"version_id": version_id},
        ).mappings().one_or_none()

    def _lock_version(self, connection: Connection, version_id: UUID):
        return connection.execute(
            text(
                """
                SELECT id, version_no, lifecycle_state, aggregate, created_by,
                       created_at, published_at, cloned_from_version_id
                FROM content_config.configuration_version
                WHERE id = :version_id
                FOR UPDATE
                """
            ),
            {"version_id": version_id},
        ).mappings().one_or_none()

    def _insert_version(
        self,
        connection: Connection,
        snapshot: ContentConfigurationSnapshot,
    ) -> None:
        connection.execute(
            text(
                """
                INSERT INTO content_config.configuration_version (
                    id, version_no, lifecycle_state, aggregate, created_by,
                    created_at, published_at, cloned_from_version_id
                ) VALUES (
                    :id, :version_no, :lifecycle_state, CAST(:aggregate AS jsonb),
                    :created_by, :created_at, :published_at, :cloned_from_version_id
                )
                """
            ),
            {
                "id": snapshot.id,
                "version_no": snapshot.version_no,
                "lifecycle_state": snapshot.state.value,
                "aggregate": json.dumps(self._document(snapshot)),
                "created_by": snapshot.created_by,
                "created_at": snapshot.created_at,
                "published_at": snapshot.published_at,
                "cloned_from_version_id": snapshot.cloned_from_version_id,
            },
        )

    @staticmethod
    def _insert_audit(
        connection: Connection,
        audit: ContentConfigurationAuditEntry,
    ) -> None:
        connection.execute(
            text(
                """
                INSERT INTO content_config.configuration_audit (
                    audit_id, config_version_id, actor_ref, command,
                    previous_state, new_state, rationale, occurred_at
                ) VALUES (
                    :audit_id, :config_version_id, :actor_ref, :command,
                    :previous_state, :new_state, :rationale, :occurred_at
                )
                """
            ),
            {
                "audit_id": audit.audit_id,
                "config_version_id": audit.config_version_id,
                "actor_ref": audit.actor_ref,
                "command": audit.command,
                "previous_state": audit.previous_state.value if audit.previous_state else None,
                "new_state": audit.new_state.value,
                "rationale": audit.rationale,
                "occurred_at": audit.occurred_at,
            },
        )

    @staticmethod
    def _document(snapshot: ContentConfigurationSnapshot) -> dict[str, Any]:
        return {
            "domains": [
                {"code": item.code, "label_key": item.label_key, "enabled": item.enabled}
                for item in snapshot.domains
            ],
            "topics": [
                {
                    "code": item.code,
                    "domain_code": item.domain_code,
                    "label_key": item.label_key,
                    "enabled": item.enabled,
                }
                for item in snapshot.topics
            ],
            "base_formats": [
                {"code": item.code, "label_key": item.label_key, "enabled": item.enabled}
                for item in snapshot.base_formats
            ],
            "modifiers": [
                {"code": item.code, "label_key": item.label_key, "enabled": item.enabled}
                for item in snapshot.modifiers
            ],
            "modifier_compatibility": {
                key: sorted(value) for key, value in snapshot.modifier_compatibility.items()
            },
            "risks": sorted(snapshot.risks),
            "claim_states": sorted(snapshot.claim_states),
            "source_kinds": sorted(snapshot.source_kinds),
            "disclosure_levels": sorted(snapshot.disclosure_levels),
        }

    @staticmethod
    def _from_row(row) -> ContentConfigurationSnapshot:
        document = row["aggregate"]
        if isinstance(document, str):
            document = json.loads(document)
        return ContentConfigurationSnapshot(
            id=row["id"],
            version_no=int(row["version_no"]),
            state=ContentConfigLifecycle(row["lifecycle_state"]),
            domains=tuple(TaxonomyItem(**item) for item in document["domains"]),
            topics=tuple(TopicItem(**item) for item in document.get("topics", [])),
            base_formats=tuple(TaxonomyItem(**item) for item in document["base_formats"]),
            modifiers=tuple(TaxonomyItem(**item) for item in document["modifiers"]),
            modifier_compatibility={
                key: frozenset(value)
                for key, value in document["modifier_compatibility"].items()
            },
            risks=frozenset(document["risks"]),
            claim_states=frozenset(document["claim_states"]),
            source_kinds=frozenset(document["source_kinds"]),
            disclosure_levels=frozenset(document["disclosure_levels"]),
            created_by=row["created_by"],
            created_at=row["created_at"],
            published_at=row["published_at"],
            cloned_from_version_id=row["cloned_from_version_id"],
        )
