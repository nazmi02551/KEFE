from __future__ import annotations

from alembic import op

revision = "20260812_0036"
down_revision = "20260812_0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE identity.guest_merge_replay
            ADD COLUMN account_session_id uuid,
            ADD COLUMN account_session_rotation_counter bigint,
            ADD COLUMN account_session_derivation_key_id varchar(64),
            ADD COLUMN continuity_absolute_expires_at timestamptz,
            ADD COLUMN continuity_inactive_expires_at timestamptz
        """
    )
    op.execute(
        """
        ALTER TABLE identity.guest_merge_replay
            ADD CONSTRAINT guest_merge_replay_session_metadata_ck CHECK (
                (
                    account_session_id IS NULL
                    AND account_session_rotation_counter IS NULL
                    AND account_session_derivation_key_id IS NULL
                    AND continuity_absolute_expires_at IS NULL
                    AND continuity_inactive_expires_at IS NULL
                )
                OR
                (
                    account_session_id IS NOT NULL
                    AND account_session_rotation_counter IS NOT NULL
                    AND account_session_rotation_counter >= 0
                    AND account_session_derivation_key_id IS NOT NULL
                    AND continuity_absolute_expires_at IS NOT NULL
                    AND continuity_inactive_expires_at IS NOT NULL
                    AND continuity_inactive_expires_at <= continuity_absolute_expires_at
                )
            )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX guest_merge_replay_account_session_idx
        ON identity.guest_merge_replay(account_session_id)
        WHERE account_session_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS identity.guest_merge_replay_account_session_idx")
    op.execute(
        "ALTER TABLE identity.guest_merge_replay "
        "DROP CONSTRAINT IF EXISTS guest_merge_replay_session_metadata_ck"
    )
    op.execute(
        """
        ALTER TABLE identity.guest_merge_replay
            DROP COLUMN IF EXISTS continuity_inactive_expires_at,
            DROP COLUMN IF EXISTS continuity_absolute_expires_at,
            DROP COLUMN IF EXISTS account_session_derivation_key_id,
            DROP COLUMN IF EXISTS account_session_rotation_counter,
            DROP COLUMN IF EXISTS account_session_id
        """
    )
