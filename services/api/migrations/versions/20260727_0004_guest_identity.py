from __future__ import annotations

from alembic import op

revision = "20260727_0004"
down_revision = "20260727_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE identity.actor_session (
            id uuid PRIMARY KEY,
            actor_id uuid NOT NULL REFERENCES identity.actor(id) ON DELETE CASCADE,
            token_hash char(64) NOT NULL UNIQUE,
            expires_at timestamptz NOT NULL,
            revoked_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX actor_session_active_lookup_idx
        ON identity.actor_session(token_hash, expires_at)
        WHERE revoked_at IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS identity.actor_session")
