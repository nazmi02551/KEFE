from __future__ import annotations

from alembic import op

revision = "20260812_0035"
down_revision = "20260806_0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE identity.actor_session
            ADD COLUMN previous_token_hash char(64),
            ADD COLUMN previous_token_valid_until timestamptz,
            ADD COLUMN renewal_token_hash char(64),
            ADD COLUMN previous_renewal_token_hash char(64),
            ADD COLUMN previous_renewal_valid_until timestamptz,
            ADD COLUMN rotation_counter bigint NOT NULL DEFAULT 0,
            ADD COLUMN token_derivation_key_id text,
            ADD COLUMN renewed_at timestamptz,
            ADD COLUMN continuity_absolute_expires_at timestamptz,
            ADD COLUMN continuity_inactive_expires_at timestamptz
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX actor_session_renewal_token_hash_uidx
        ON identity.actor_session(renewal_token_hash)
        WHERE renewal_token_hash IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE INDEX actor_session_previous_renewal_lookup_idx
        ON identity.actor_session(previous_renewal_token_hash, previous_renewal_valid_until)
        WHERE previous_renewal_token_hash IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE INDEX actor_session_previous_access_lookup_idx
        ON identity.actor_session(previous_token_hash, previous_token_valid_until)
        WHERE previous_token_hash IS NOT NULL
        """
    )
    op.execute(
        """
        ALTER TABLE identity.actor_session
        ADD CONSTRAINT actor_session_rotation_counter_nonnegative
        CHECK (rotation_counter >= 0)
        """
    )
    op.execute(
        """
        ALTER TABLE identity.actor_session
        ADD CONSTRAINT actor_session_continuity_deadline_order
        CHECK (
            continuity_absolute_expires_at IS NULL
            OR continuity_inactive_expires_at IS NULL
            OR continuity_inactive_expires_at <= continuity_absolute_expires_at
        )
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE identity.actor_session "
        "DROP CONSTRAINT IF EXISTS actor_session_continuity_deadline_order"
    )
    op.execute(
        "ALTER TABLE identity.actor_session "
        "DROP CONSTRAINT IF EXISTS actor_session_rotation_counter_nonnegative"
    )
    op.execute("DROP INDEX IF EXISTS identity.actor_session_previous_access_lookup_idx")
    op.execute("DROP INDEX IF EXISTS identity.actor_session_previous_renewal_lookup_idx")
    op.execute("DROP INDEX IF EXISTS identity.actor_session_renewal_token_hash_uidx")
    op.execute(
        """
        ALTER TABLE identity.actor_session
            DROP COLUMN IF EXISTS continuity_inactive_expires_at,
            DROP COLUMN IF EXISTS continuity_absolute_expires_at,
            DROP COLUMN IF EXISTS renewed_at,
            DROP COLUMN IF EXISTS token_derivation_key_id,
            DROP COLUMN IF EXISTS rotation_counter,
            DROP COLUMN IF EXISTS previous_renewal_valid_until,
            DROP COLUMN IF EXISTS previous_renewal_token_hash,
            DROP COLUMN IF EXISTS renewal_token_hash,
            DROP COLUMN IF EXISTS previous_token_valid_until,
            DROP COLUMN IF EXISTS previous_token_hash
        """
    )
