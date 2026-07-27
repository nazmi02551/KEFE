from __future__ import annotations

from alembic import op

revision = "20260727_0008"
down_revision = "20260727_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE content.context_source (
            id uuid PRIMARY KEY,
            case_version_id uuid NOT NULL
                REFERENCES content.case_version(id) ON DELETE RESTRICT,
            title text NOT NULL,
            publisher text NOT NULL,
            source_kind text NOT NULL CHECK (
                source_kind IN ('OFFICIAL','NEWS','RESEARCH','EDITORIAL','OTHER')
            ),
            url text,
            published_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX context_source_case_version_idx
        ON content.context_source(case_version_id, created_at, id)
        """
    )
    op.execute(
        """
        CREATE TABLE content.context_block (
            id uuid PRIMARY KEY,
            case_version_id uuid NOT NULL
                REFERENCES content.case_version(id) ON DELETE RESTRICT,
            display_order integer NOT NULL CHECK (display_order >= 0),
            disclosure_level text NOT NULL CHECK (
                disclosure_level IN ('ESSENTIAL','DETAIL')
            ),
            title text NOT NULL,
            body text NOT NULL,
            claim_status text NOT NULL CHECK (
                claim_status IN ('VERIFIED','CLAIMED','DISPUTED','UNKNOWN')
            ),
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE(case_version_id, display_order, id)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX context_block_case_version_idx
        ON content.context_block(case_version_id, display_order, id)
        """
    )
    op.execute(
        """
        CREATE TABLE content.context_block_source (
            context_block_id uuid NOT NULL
                REFERENCES content.context_block(id) ON DELETE CASCADE,
            source_id uuid NOT NULL
                REFERENCES content.context_source(id) ON DELETE RESTRICT,
            PRIMARY KEY(context_block_id, source_id)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS content.context_block_source")
    op.execute("DROP TABLE IF EXISTS content.context_block")
    op.execute("DROP TABLE IF EXISTS content.context_source")
