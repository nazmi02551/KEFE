from __future__ import annotations

from alembic import op

revision = "20260824_0035"
down_revision = "20260806_0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE content.case_version
        ADD COLUMN is_real_event boolean NOT NULL DEFAULT false
        """
    )
    op.execute(
        """
        UPDATE content.case_version AS consumer
        SET is_real_event = true
        FROM editorial.case_version AS editorial
        WHERE editorial.id = consumer.id
          AND editorial.aggregate->>'is_real_event' = 'true'
        """
    )
    op.execute(
        """
        CREATE INDEX case_version_real_event_published_idx
        ON content.case_version(published_at DESC, id)
        WHERE status = 'PUBLISHED' AND is_real_event = true
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS content.case_version_real_event_published_idx")
    op.execute("ALTER TABLE content.case_version DROP COLUMN IF EXISTS is_real_event")
