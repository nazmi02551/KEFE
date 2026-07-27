from __future__ import annotations

from alembic import op

revision = "20260727_0006"
down_revision = "20260727_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE content.source (
            id uuid PRIMARY KEY,
            title text NOT NULL,
            publisher text NOT NULL,
            url text NOT NULL,
            published_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE content.claim (
            id uuid PRIMARY KEY,
            case_version_id uuid NOT NULL REFERENCES content.case_version(id) ON DELETE RESTRICT,
            text text NOT NULL,
            status text NOT NULL CHECK (status IN ('VERIFIED','CLAIMED','DISPUTED','UNKNOWN')),
            presentation text NOT NULL CHECK (presentation IN ('CRITICAL','DETAIL')),
            sort_order integer NOT NULL DEFAULT 0,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE content.claim_source (
            claim_id uuid NOT NULL REFERENCES content.claim(id) ON DELETE CASCADE,
            source_id uuid NOT NULL REFERENCES content.source(id) ON DELETE RESTRICT,
            PRIMARY KEY (claim_id, source_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE content.context_block (
            id uuid PRIMARY KEY,
            case_version_id uuid NOT NULL REFERENCES content.case_version(id) ON DELETE RESTRICT,
            kind text NOT NULL CHECK (
                kind IN ('CONTEXT','LEGAL_FRAME','CULTURAL_CONTEXT','METHODOLOGY')
            ),
            title text NOT NULL,
            body text NOT NULL,
            sort_order integer NOT NULL DEFAULT 0,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE decision.exposure (
            id uuid PRIMARY KEY,
            session_id uuid NOT NULL REFERENCES decision.weigh_session(id) ON DELETE CASCADE,
            exposure_kind text NOT NULL CHECK (
                exposure_kind IN ('CLAIM','CONTEXT_BLOCK','SOURCE')
            ),
            ref_id uuid NOT NULL,
            occurred_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE(session_id, exposure_kind, ref_id)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX claim_case_version_order_idx
        ON content.claim(case_version_id, presentation, sort_order, id)
        """
    )
    op.execute(
        """
        CREATE INDEX context_block_case_version_order_idx
        ON content.context_block(case_version_id, sort_order, id)
        """
    )
    op.execute(
        """
        CREATE INDEX exposure_session_idx
        ON decision.exposure(session_id, occurred_at)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS decision.exposure")
    op.execute("DROP TABLE IF EXISTS content.context_block")
    op.execute("DROP TABLE IF EXISTS content.claim_source")
    op.execute("DROP TABLE IF EXISTS content.claim")
    op.execute("DROP TABLE IF EXISTS content.source")
