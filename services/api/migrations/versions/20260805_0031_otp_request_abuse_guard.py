from __future__ import annotations

from alembic import op

revision = "20260805_0031"
down_revision = "20260805_0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE identity.otp_request_guard (
            channel text NOT NULL
                CHECK (channel IN ('EMAIL', 'SMS')),
            identifier_hash char(64) NOT NULL,
            latest_challenge_id uuid NOT NULL UNIQUE
                REFERENCES identity.otp_challenge(id) ON DELETE CASCADE,
            window_started_at timestamptz NOT NULL,
            last_requested_at timestamptz NOT NULL,
            request_count integer NOT NULL
                CHECK (request_count >= 1),
            retention_expires_at timestamptz NOT NULL,
            updated_at timestamptz NOT NULL,
            PRIMARY KEY (channel, identifier_hash),
            CHECK (retention_expires_at > last_requested_at),
            CHECK (updated_at >= last_requested_at)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX otp_request_guard_retention_idx
        ON identity.otp_request_guard(retention_expires_at)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS identity.otp_request_guard_retention_idx")
    op.execute("DROP TABLE IF EXISTS identity.otp_request_guard")
