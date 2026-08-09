from __future__ import annotations

from alembic import op

revision = "20260809_0035"
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
        ADD COLUMN rotation_counter integer NOT NULL DEFAULT 0,
        ADD COLUMN token_derivation_key_id varchar(64),
        ADD COLUMN renewed_at timestamptz,
        ADD CONSTRAINT actor_session_rotation_counter_nonnegative
            CHECK (rotation_counter >= 0),
        ADD CONSTRAINT actor_session_previous_access_pair
            CHECK (
                (previous_token_hash IS NULL AND previous_token_valid_until IS NULL)
                OR
                (previous_token_hash IS NOT NULL AND previous_token_valid_until IS NOT NULL)
            ),
        ADD CONSTRAINT actor_session_previous_renewal_pair
            CHECK (
                (
                    previous_renewal_token_hash IS NULL
                    AND previous_renewal_valid_until IS NULL
                )
                OR
                (
                    previous_renewal_token_hash IS NOT NULL
                    AND previous_renewal_valid_until IS NOT NULL
                )
            ),
        ADD CONSTRAINT actor_session_renewal_metadata_coherent
            CHECK (
                renewal_token_hash IS NULL
                OR token_derivation_key_id IS NOT NULL
            )
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
        CREATE UNIQUE INDEX actor_session_previous_renewal_token_hash_uidx
        ON identity.actor_session(previous_renewal_token_hash)
        WHERE previous_renewal_token_hash IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX actor_session_previous_token_hash_uidx
        ON identity.actor_session(previous_token_hash)
        WHERE previous_token_hash IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE INDEX actor_session_renewal_active_lookup_idx
        ON identity.actor_session(renewal_token_hash, revoked_at)
        WHERE renewal_token_hash IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE INDEX actor_session_previous_renewal_lookup_idx
        ON identity.actor_session(
            previous_renewal_token_hash,
            previous_renewal_valid_until
        )
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
        ALTER TABLE identity.guest_merge_replay
        ADD COLUMN account_session_id uuid
            REFERENCES identity.actor_session(id) ON DELETE SET NULL
        """
    )
    op.execute(
        """
        CREATE INDEX guest_merge_replay_account_session_idx
        ON identity.guest_merge_replay(account_session_id)
        WHERE account_session_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP INDEX IF EXISTS identity.guest_merge_replay_account_session_idx"
    )
    op.execute(
        "ALTER TABLE identity.guest_merge_replay DROP COLUMN IF EXISTS account_session_id"
    )
    op.execute(
        "DROP INDEX IF EXISTS identity.actor_session_previous_access_lookup_idx"
    )
    op.execute(
        "DROP INDEX IF EXISTS identity.actor_session_previous_renewal_lookup_idx"
    )
    op.execute(
        "DROP INDEX IF EXISTS identity.actor_session_renewal_active_lookup_idx"
    )
    op.execute(
        "DROP INDEX IF EXISTS identity.actor_session_previous_token_hash_uidx"
    )
    op.execute(
        "DROP INDEX IF EXISTS identity.actor_session_previous_renewal_token_hash_uidx"
    )
    op.execute(
        "DROP INDEX IF EXISTS identity.actor_session_renewal_token_hash_uidx"
    )
    op.execute(
        """
        ALTER TABLE identity.actor_session
        DROP CONSTRAINT IF EXISTS actor_session_renewal_metadata_coherent,
        DROP CONSTRAINT IF EXISTS actor_session_previous_renewal_pair,
        DROP CONSTRAINT IF EXISTS actor_session_previous_access_pair,
        DROP CONSTRAINT IF EXISTS actor_session_rotation_counter_nonnegative,
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
