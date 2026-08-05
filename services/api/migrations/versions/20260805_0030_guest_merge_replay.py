from __future__ import annotations

from alembic import op

revision = "20260805_0030"
down_revision = "20260805_0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE identity.guest_merge_replay (
            verification_token_hash char(64) PRIMARY KEY
                REFERENCES identity.otp_verification(token_hash) ON DELETE CASCADE,
            source_actor_id uuid NOT NULL
                REFERENCES identity.actor(id) ON DELETE RESTRICT,
            account_actor_id uuid NOT NULL
                REFERENCES identity.actor(id) ON DELETE RESTRICT,
            merged_from_actor_id uuid
                REFERENCES identity.actor(id) ON DELETE RESTRICT,
            account_session_expires_at timestamptz NOT NULL,
            completed_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            CHECK (
                merged_from_actor_id IS NULL
                OR merged_from_actor_id = source_actor_id
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX guest_merge_replay_account_idx
        ON identity.guest_merge_replay(account_actor_id, completed_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX guest_merge_replay_source_idx
        ON identity.guest_merge_replay(source_actor_id, completed_at DESC)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS identity.guest_merge_replay_source_idx")
    op.execute("DROP INDEX IF EXISTS identity.guest_merge_replay_account_idx")
    op.execute("DROP TABLE IF EXISTS identity.guest_merge_replay")
