from __future__ import annotations

from alembic import op

revision = "20260727_0006"
down_revision = "20260727_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE decision.private_reason (
            session_id uuid PRIMARY KEY
                REFERENCES decision.weigh_session(id) ON DELETE CASCADE,
            tags jsonb NOT NULL DEFAULT '[]'::jsonb,
            text_body text,
            moderation_state text NOT NULL CHECK (
                moderation_state IN ('NOT_REQUIRED','PENDING','ALLOWED','BLOCKED')
            ),
            visibility text NOT NULL DEFAULT 'PRIVATE' CHECK (visibility = 'PRIVATE'),
            updated_at timestamptz NOT NULL DEFAULT now(),
            CHECK (jsonb_typeof(tags) = 'array'),
            CHECK (text_body IS NULL OR char_length(text_body) <= 1000)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS decision.private_reason")
