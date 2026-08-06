from __future__ import annotations

from alembic import op

revision = "20260806_0034"
down_revision = "20260806_0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE identity.otp_provider_receipt (
            provider_event_ref varchar(64) PRIMARY KEY
                CHECK (provider_event_ref ~ '^[0-9a-f]{64}$'),
            delivery_ref varchar(64) NOT NULL
                CHECK (delivery_ref ~ '^[0-9a-f]{64}$'),
            outcome text NOT NULL
                CHECK (outcome IN ('DELIVERED', 'UNDELIVERABLE', 'EXPIRED')),
            occurred_at timestamptz NOT NULL,
            received_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            CHECK (created_at >= received_at)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX otp_provider_receipt_received_idx
        ON identity.otp_provider_receipt(received_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX otp_provider_receipt_outcome_idx
        ON identity.otp_provider_receipt(outcome, received_at DESC)
        """
    )
    op.execute(
        """
        CREATE FUNCTION identity.reject_otp_provider_receipt_update()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'OTP provider receipt records are immutable';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER otp_provider_receipt_no_update
        BEFORE UPDATE ON identity.otp_provider_receipt
        FOR EACH ROW
        EXECUTE FUNCTION identity.reject_otp_provider_receipt_update()
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS otp_provider_receipt_no_update "
        "ON identity.otp_provider_receipt"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS identity.reject_otp_provider_receipt_update()"
    )
    op.execute("DROP INDEX IF EXISTS identity.otp_provider_receipt_outcome_idx")
    op.execute("DROP INDEX IF EXISTS identity.otp_provider_receipt_received_idx")
    op.execute("DROP TABLE IF EXISTS identity.otp_provider_receipt")
