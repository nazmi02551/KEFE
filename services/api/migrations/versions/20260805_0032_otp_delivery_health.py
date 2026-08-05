from __future__ import annotations

from alembic import op

revision = "20260805_0032"
down_revision = "20260805_0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE identity.otp_delivery_event (
            id uuid PRIMARY KEY,
            observed_at timestamptz NOT NULL,
            channel text NOT NULL
                CHECK (channel IN ('EMAIL', 'SMS')),
            outcome text NOT NULL
                CHECK (outcome IN ('ACCEPTED', 'UNAVAILABLE', 'REJECTED')),
            attempts smallint NOT NULL
                CHECK (attempts BETWEEN 1 AND 3),
            status_code smallint
                CHECK (status_code IS NULL OR status_code BETWEEN 100 AND 599),
            error_code varchar(128),
            created_at timestamptz NOT NULL DEFAULT now(),
            CHECK (
                error_code IS NULL
                OR (
                    length(error_code) BETWEEN 1 AND 128
                    AND error_code = btrim(error_code)
                    AND error_code !~ '[[:cntrl:]]'
                )
            ),
            CHECK (
                (outcome = 'ACCEPTED' AND error_code IS NULL)
                OR (outcome <> 'ACCEPTED' AND error_code IS NOT NULL)
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX otp_delivery_event_observed_idx
        ON identity.otp_delivery_event(observed_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX otp_delivery_event_outcome_idx
        ON identity.otp_delivery_event(outcome, observed_at DESC)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS identity.otp_delivery_event_outcome_idx")
    op.execute("DROP INDEX IF EXISTS identity.otp_delivery_event_observed_idx")
    op.execute("DROP TABLE IF EXISTS identity.otp_delivery_event")
