from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Connection, text

from kefe_api.core.settings import get_settings
from kefe_api.infrastructure.db import build_engine
from kefe_api.modules.context.bootstrap import (
    DEMO_CONTEXT_BLOCK_ID,
    DEMO_CONTEXT_DETAIL_ID,
    DEMO_CONTEXT_SOURCE_ID,
)
from kefe_api.modules.decision.bootstrap import DEMO_CASE_VERSION_ID


def seed_context_demo(connection: Connection) -> None:
    now = datetime.now(UTC)
    connection.execute(
        text(
            """
            INSERT INTO content.context_source (
                id,
                case_version_id,
                title,
                publisher,
                source_kind,
                url,
                published_at
            )
            VALUES (
                :id,
                :case_version_id,
                'KEFE Demo Senaryo Notu',
                'KEFE Editorial',
                'EDITORIAL',
                NULL,
                :published_at
            )
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                publisher = EXCLUDED.publisher,
                source_kind = EXCLUDED.source_kind,
                published_at = EXCLUDED.published_at
            """
        ),
        {
            "id": DEMO_CONTEXT_SOURCE_ID,
            "case_version_id": DEMO_CASE_VERSION_ID,
            "published_at": now,
        },
    )

    blocks = (
        (
            DEMO_CONTEXT_BLOCK_ID,
            0,
            "ESSENTIAL",
            "Durum",
            (
                "Toplu taşımada yalnız bir boş koltuk vardır ve iki kişinin de makul "
                "bir öncelik gerekçesi bulunmaktadır."
            ),
            "VERIFIED",
        ),
        (
            DEMO_CONTEXT_DETAIL_ID,
            10,
            "DETAIL",
            "Tartılması gereken çatışma",
            (
                "Karar, görünür ihtiyaç ile sırayı ve eşit uygulamayı koruma arasında "
                "bir öncelik çatışması oluşturur."
            ),
            "UNKNOWN",
        ),
    )
    for block_id, order, disclosure, title, body, claim_status in blocks:
        connection.execute(
            text(
                """
                INSERT INTO content.context_block (
                    id,
                    case_version_id,
                    display_order,
                    disclosure_level,
                    title,
                    body,
                    claim_status
                )
                VALUES (
                    :id,
                    :case_version_id,
                    :display_order,
                    :disclosure_level,
                    :title,
                    :body,
                    :claim_status
                )
                ON CONFLICT (id) DO UPDATE SET
                    display_order = EXCLUDED.display_order,
                    disclosure_level = EXCLUDED.disclosure_level,
                    title = EXCLUDED.title,
                    body = EXCLUDED.body,
                    claim_status = EXCLUDED.claim_status
                """
            ),
            {
                "id": block_id,
                "case_version_id": DEMO_CASE_VERSION_ID,
                "display_order": order,
                "disclosure_level": disclosure,
                "title": title,
                "body": body,
                "claim_status": claim_status,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO content.context_block_source (context_block_id, source_id)
                VALUES (:context_block_id, :source_id)
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "context_block_id": block_id,
                "source_id": DEMO_CONTEXT_SOURCE_ID,
            },
        )


def main() -> None:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required to seed PostgreSQL")
    engine = build_engine(settings.database_url)
    with engine.begin() as connection:
        seed_context_demo(connection)


if __name__ == "__main__":
    main()
