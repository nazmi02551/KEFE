from __future__ import annotations

from alembic import op

revision = "20260727_0003"
down_revision = "20260727_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE analytics.outbox_event
        ADD COLUMN next_attempt_at timestamptz NOT NULL DEFAULT now(),
        ADD COLUMN last_error text,
        ADD COLUMN lock_owner text,
        ADD COLUMN locked_until timestamptz,
        ADD COLUMN dead_lettered_at timestamptz
        """
    )
    op.execute(
        """
        CREATE INDEX outbox_delivery_ready_idx
        ON analytics.outbox_event(next_attempt_at, created_at)
        WHERE published_at IS NULL AND dead_lettered_at IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS analytics.outbox_delivery_ready_idx")
    op.execute(
        """
        ALTER TABLE analytics.outbox_event
        DROP COLUMN IF EXISTS dead_lettered_at,
        DROP COLUMN IF EXISTS locked_until,
        DROP COLUMN IF EXISTS lock_owner,
        DROP COLUMN IF EXISTS last_error,
        DROP COLUMN IF EXISTS next_attempt_at
        """
    )
