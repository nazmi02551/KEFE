from __future__ import annotations

from alembic import op

revision = "20260727_0005"
down_revision = "20260727_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE content.question_version
        ADD COLUMN is_required boolean NOT NULL DEFAULT true
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE content.question_version
        DROP COLUMN IF EXISTS is_required
        """
    )
