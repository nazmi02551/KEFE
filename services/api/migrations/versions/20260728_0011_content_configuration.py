from __future__ import annotations

from alembic import op

revision = "20260728_0011"
down_revision = "20260728_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS content_config")
    op.execute(
        """
        CREATE TABLE content_config.snapshot (
            id uuid PRIMARY KEY,
            version_no integer NOT NULL UNIQUE CHECK (version_no > 0),
            state text NOT NULL CHECK (state IN ('DRAFT','PUBLISHED','SUPERSEDED')),
            payload jsonb NOT NULL,
            created_at timestamptz NOT NULL,
            published_at timestamptz
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX content_config_one_published_idx
        ON content_config.snapshot ((state))
        WHERE state = 'PUBLISHED'
        """
    )
    op.execute(
        """
        CREATE TABLE content_config.audit (
            id uuid PRIMARY KEY,
            snapshot_id uuid NOT NULL REFERENCES content_config.snapshot(id) ON DELETE RESTRICT,
            actor_ref text NOT NULL,
            command text NOT NULL,
            previous_state text,
            new_state text NOT NULL,
            superseded_snapshot_id uuid REFERENCES content_config.snapshot(id) ON DELETE RESTRICT,
            occurred_at timestamptz NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE INDEX content_config_audit_order_idx
        ON content_config.audit(occurred_at, id)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS content_config.audit")
    op.execute("DROP TABLE IF EXISTS content_config.snapshot")
    op.execute("DROP SCHEMA IF EXISTS content_config")
