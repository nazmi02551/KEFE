from __future__ import annotations

from alembic import op

revision = "20260727_0007"
down_revision = "20260727_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE content.perspective_item (
            id uuid PRIMARY KEY,
            case_version_id uuid NOT NULL
                REFERENCES content.case_version(id) ON DELETE RESTRICT,
            question_version_id uuid NOT NULL
                REFERENCES content.question_version(id) ON DELETE RESTRICT,
            target_value jsonb NOT NULL,
            text_body text NOT NULL,
            source_kind text NOT NULL CHECK (source_kind = 'EDITORIAL_HUMAN'),
            moderation_state text NOT NULL CHECK (
                moderation_state IN ('PENDING','ALLOWED','BLOCKED')
            ),
            publication_state text NOT NULL CHECK (
                publication_state IN ('DRAFT','PUBLISHED','WITHDRAWN')
            ),
            editorial_priority integer NOT NULL DEFAULT 100,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            CHECK (char_length(text_body) BETWEEN 1 AND 2000),
            CHECK (jsonb_typeof(target_value) IN ('string','number','boolean'))
        )
        """
    )
    op.execute(
        """
        CREATE INDEX perspective_published_lookup_idx
        ON content.perspective_item(
            case_version_id,
            question_version_id,
            editorial_priority,
            created_at
        )
        WHERE publication_state = 'PUBLISHED'
          AND moderation_state = 'ALLOWED'
          AND source_kind = 'EDITORIAL_HUMAN'
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS content.perspective_item")
