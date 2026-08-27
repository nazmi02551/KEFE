from __future__ import annotations

from alembic import op

revision = "20260827_0037"
down_revision = "20260812_0036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE content.case_version
            ADD COLUMN is_real_event boolean NOT NULL DEFAULT false
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE content.case_version
            DROP COLUMN IF EXISTS is_real_event
        """
    )
