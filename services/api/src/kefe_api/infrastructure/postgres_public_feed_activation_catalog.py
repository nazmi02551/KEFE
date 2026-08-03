from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy import Engine, text

from kefe_api.modules.knowledge.public_feed_activation_catalog import (
    MAX_CATALOG_PAGE_SIZE,
    PublicFeedActivationCatalogEntry,
)
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code

_SELECT_COLUMNS = """
    id,
    activation_code,
    adapter_code,
    configuration_hash,
    manifest_schema_version,
    manifest_json,
    evidence_ref,
    recorded_by,
    recorded_at
"""


class PostgresPublicFeedActivationCatalogRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_or_get(
        self,
        entry: PublicFeedActivationCatalogEntry,
    ) -> PublicFeedActivationCatalogEntry:
        if type(entry) is not PublicFeedActivationCatalogEntry:
            raise ValueError("catalog entry must be exact PublicFeedActivationCatalogEntry")
        entry.manifest_payload()
        with self._engine.begin() as connection:
            inserted = connection.execute(
                text(
                    f"""
                    INSERT INTO knowledge.public_feed_activation_catalog (
                        id,
                        activation_code,
                        adapter_code,
                        configuration_hash,
                        manifest_schema_version,
                        manifest_json,
                        evidence_ref,
                        recorded_by,
                        recorded_at
                    ) VALUES (
                        :id,
                        :activation_code,
                        :adapter_code,
                        :configuration_hash,
                        :manifest_schema_version,
                        :manifest_json,
                        :evidence_ref,
                        :recorded_by,
                        :recorded_at
                    )
                    ON CONFLICT DO NOTHING
                    RETURNING {_SELECT_COLUMNS}
                    """
                ),
                self._parameters(entry),
            ).mappings().one_or_none()
            if inserted is not None:
                return self._from_row(inserted)

            existing = connection.execute(
                text(
                    f"""
                    SELECT {_SELECT_COLUMNS}
                    FROM knowledge.public_feed_activation_catalog
                    WHERE activation_code = :activation_code
                       OR adapter_code = :adapter_code
                       OR configuration_hash = :configuration_hash
                    ORDER BY activation_code
                    LIMIT 1
                    """
                ),
                {
                    "activation_code": entry.activation_code,
                    "adapter_code": entry.adapter_code,
                    "configuration_hash": entry.configuration_hash,
                },
            ).mappings().one_or_none()

        if existing is None:
            raise RuntimeError("catalog insert conflict could not be resolved")
        resolved = self._from_row(existing)
        if resolved.catalog_content_identity == entry.catalog_content_identity:
            return resolved
        raise ValueError("conflicting public feed activation catalog entry")

    def get_by_activation_code(
        self,
        activation_code: str,
    ) -> PublicFeedActivationCatalogEntry | None:
        require_versioned_adapter_code(activation_code)
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    f"""
                    SELECT {_SELECT_COLUMNS}
                    FROM knowledge.public_feed_activation_catalog
                    WHERE activation_code = :activation_code
                    """
                ),
                {"activation_code": activation_code},
            ).mappings().one_or_none()
        return self._from_row(row) if row is not None else None

    def get_by_adapter_code(
        self,
        adapter_code: str,
    ) -> PublicFeedActivationCatalogEntry | None:
        require_versioned_adapter_code(adapter_code)
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    f"""
                    SELECT {_SELECT_COLUMNS}
                    FROM knowledge.public_feed_activation_catalog
                    WHERE adapter_code = :adapter_code
                    """
                ),
                {"adapter_code": adapter_code},
            ).mappings().one_or_none()
        return self._from_row(row) if row is not None else None

    def list_entries(
        self,
        *,
        limit: int,
        after_activation_code: str | None = None,
    ) -> tuple[PublicFeedActivationCatalogEntry, ...]:
        if not 1 <= limit <= MAX_CATALOG_PAGE_SIZE:
            raise ValueError("catalog list limit is outside the supported range")
        if after_activation_code is not None:
            require_versioned_adapter_code(after_activation_code)
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    f"""
                    SELECT {_SELECT_COLUMNS}
                    FROM knowledge.public_feed_activation_catalog
                    WHERE :after_activation_code IS NULL
                       OR activation_code > :after_activation_code
                    ORDER BY activation_code
                    LIMIT :limit
                    """
                ),
                {
                    "after_activation_code": after_activation_code,
                    "limit": limit,
                },
            ).mappings().all()
        return tuple(self._from_row(row) for row in rows)

    @staticmethod
    def _parameters(entry: PublicFeedActivationCatalogEntry) -> dict[str, object]:
        return {
            "id": entry.id,
            "activation_code": entry.activation_code,
            "adapter_code": entry.adapter_code,
            "configuration_hash": entry.configuration_hash,
            "manifest_schema_version": entry.manifest_schema_version,
            "manifest_json": entry.manifest_json,
            "evidence_ref": entry.evidence_ref,
            "recorded_by": entry.recorded_by,
            "recorded_at": entry.recorded_at,
        }

    @staticmethod
    def _from_row(row: Mapping[str, object]) -> PublicFeedActivationCatalogEntry:
        return PublicFeedActivationCatalogEntry(
            id=row["id"],
            activation_code=str(row["activation_code"]),
            adapter_code=str(row["adapter_code"]),
            configuration_hash=str(row["configuration_hash"]),
            manifest_schema_version=str(row["manifest_schema_version"]),
            manifest_json=str(row["manifest_json"]),
            evidence_ref=str(row["evidence_ref"]),
            recorded_by=str(row["recorded_by"]),
            recorded_at=row["recorded_at"],
        )


__all__ = ["PostgresPublicFeedActivationCatalogRepository"]
