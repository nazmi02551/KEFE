from __future__ import annotations

from alembic import op

revision = "20260727_0007"
down_revision = "20260727_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE content.perspective_card (
            id uuid PRIMARY KEY,
            case_version_id uuid NOT NULL
                REFERENCES content.case_version(id) ON DELETE RESTRICT,
            slot text NOT NULL CHECK (
                slot IN ('NEAR','OPPOSING','BRIDGE','ALTERNATIVE_CONTEXT')
            ),
            body text NOT NULL CHECK (
                char_length(btrim(body)) > 0 AND char_length(body) <= 1200
            ),
            source_kind text NOT NULL DEFAULT 'CURATED' CHECK (source_kind = 'CURATED'),
            provenance_label text NOT NULL CHECK (char_length(btrim(provenance_label)) > 0),
            moderation_state text NOT NULL DEFAULT 'NOT_REQUIRED' CHECK (
                moderation_state = 'NOT_REQUIRED'
            ),
            status text NOT NULL CHECK (status IN ('DRAFT','PUBLISHED','WITHDRAWN')),
            published_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            CHECK (status <> 'PUBLISHED' OR published_at IS NOT NULL)
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX perspective_one_published_slot_idx
        ON content.perspective_card(case_version_id, slot)
        WHERE status = 'PUBLISHED'
        """
    )
    op.execute(
        """
        CREATE INDEX perspective_published_lookup_idx
        ON content.perspective_card(case_version_id, published_at, id)
        WHERE status = 'PUBLISHED'
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS content.perspective_card")
