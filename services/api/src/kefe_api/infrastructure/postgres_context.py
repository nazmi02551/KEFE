from __future__ import annotations

from uuid import UUID

from sqlalchemy import Engine, text

from kefe_api.modules.context.models import (
    ClaimStatus,
    ContextBlock,
    ContextSnapshot,
    ContextSource,
    DisclosureLevel,
    SourceKind,
)


class PostgresContextRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_context(self, case_version_id: UUID) -> ContextSnapshot | None:
        with self._engine.connect() as connection:
            exists = connection.execute(
                text(
                    """
                    SELECT 1
                    FROM content.case_version
                    WHERE id = :id
                      AND status IN ('PUBLISHED','SUPERSEDED')
                    """
                ),
                {"id": case_version_id},
            ).scalar_one_or_none()
            if not exists:
                return None

            source_rows = connection.execute(
                text(
                    """
                    SELECT id, title, publisher, source_kind, url, published_at
                    FROM content.context_source
                    WHERE case_version_id = :case_version_id
                    ORDER BY created_at, id
                    LIMIT 20
                    """
                ),
                {"case_version_id": case_version_id},
            ).mappings().all()
            block_rows = connection.execute(
                text(
                    """
                    SELECT id, display_order, disclosure_level, title, body, claim_status
                    FROM content.context_block
                    WHERE case_version_id = :case_version_id
                    ORDER BY display_order, id
                    LIMIT 20
                    """
                ),
                {"case_version_id": case_version_id},
            ).mappings().all()
            link_rows = (
                connection.execute(
                    text(
                        """
                        SELECT context_block_id, source_id
                        FROM content.context_block_source
                        WHERE context_block_id = ANY(:block_ids)
                        ORDER BY context_block_id, source_id
                        """
                    ),
                    {"block_ids": [row["id"] for row in block_rows]},
                ).mappings().all()
                if block_rows
                else []
            )

        source_ids_by_block: dict[UUID, list[UUID]] = {}
        for row in link_rows:
            source_ids_by_block.setdefault(row["context_block_id"], []).append(row["source_id"])

        return ContextSnapshot(
            case_version_id=case_version_id,
            blocks=tuple(
                ContextBlock(
                    id=row["id"],
                    case_version_id=case_version_id,
                    display_order=row["display_order"],
                    disclosure_level=DisclosureLevel(row["disclosure_level"]),
                    title=row["title"],
                    body=row["body"],
                    claim_status=ClaimStatus(row["claim_status"]),
                    source_ids=tuple(source_ids_by_block.get(row["id"], [])),
                )
                for row in block_rows
            ),
            sources=tuple(
                ContextSource(
                    id=row["id"],
                    case_version_id=case_version_id,
                    title=row["title"],
                    publisher=row["publisher"],
                    source_kind=SourceKind(row["source_kind"]),
                    url=row["url"],
                    published_at=row["published_at"],
                )
                for row in source_rows
            ),
        )
