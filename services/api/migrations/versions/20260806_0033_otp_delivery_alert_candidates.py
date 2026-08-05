from __future__ import annotations

from alembic import op

revision = "20260806_0033"
down_revision = "20260805_0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE identity.otp_delivery_alert_candidate (
            id uuid PRIMARY KEY,
            signal text NOT NULL
                CHECK (signal IN ('ATTENTION', 'CRITICAL')),
            reason_codes jsonb NOT NULL
                CHECK (
                    jsonb_typeof(reason_codes) = 'array'
                    AND jsonb_array_length(reason_codes) > 0
                ),
            observed_at timestamptz NOT NULL,
            window_started_at timestamptz NOT NULL,
            total_count integer NOT NULL CHECK (total_count >= 0),
            accepted_count integer NOT NULL CHECK (accepted_count >= 0),
            unavailable_count integer NOT NULL CHECK (unavailable_count >= 0),
            rejected_count integer NOT NULL CHECK (rejected_count >= 0),
            failure_ratio_bps integer
                CHECK (
                    failure_ratio_bps IS NULL
                    OR failure_ratio_bps BETWEEN 0 AND 10000
                ),
            created_at timestamptz NOT NULL DEFAULT now(),
            CHECK (window_started_at <= observed_at),
            CHECK (created_at >= observed_at),
            CHECK (
                accepted_count + unavailable_count + rejected_count = total_count
            )
        )
        """
    )
    op.execute(
        """
        CREATE TABLE identity.otp_delivery_alert_acknowledgement (
            candidate_id uuid PRIMARY KEY
                REFERENCES identity.otp_delivery_alert_candidate(id)
                ON DELETE CASCADE,
            acknowledged_at timestamptz NOT NULL,
            actor_ref varchar(128) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            CHECK (created_at >= acknowledged_at),
            CHECK (
                actor_ref LIKE 'admin:%'
                AND actor_ref = btrim(actor_ref)
                AND actor_ref !~ '[[:cntrl:]]'
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX otp_delivery_alert_candidate_observed_idx
        ON identity.otp_delivery_alert_candidate(observed_at DESC, id DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX otp_delivery_alert_candidate_signal_idx
        ON identity.otp_delivery_alert_candidate(signal, observed_at DESC)
        """
    )
    op.execute(
        """
        CREATE FUNCTION identity.reject_otp_delivery_alert_update()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'OTP delivery alert records are immutable';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER otp_delivery_alert_candidate_no_update
        BEFORE UPDATE ON identity.otp_delivery_alert_candidate
        FOR EACH ROW EXECUTE FUNCTION identity.reject_otp_delivery_alert_update()
        """
    )
    op.execute(
        """
        CREATE TRIGGER otp_delivery_alert_acknowledgement_no_update
        BEFORE UPDATE ON identity.otp_delivery_alert_acknowledgement
        FOR EACH ROW EXECUTE FUNCTION identity.reject_otp_delivery_alert_update()
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS otp_delivery_alert_acknowledgement_no_update "
        "ON identity.otp_delivery_alert_acknowledgement"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS otp_delivery_alert_candidate_no_update "
        "ON identity.otp_delivery_alert_candidate"
    )
    op.execute("DROP FUNCTION IF EXISTS identity.reject_otp_delivery_alert_update()")
    op.execute("DROP INDEX IF EXISTS identity.otp_delivery_alert_candidate_signal_idx")
    op.execute("DROP INDEX IF EXISTS identity.otp_delivery_alert_candidate_observed_idx")
    op.execute("DROP TABLE IF EXISTS identity.otp_delivery_alert_acknowledgement")
    op.execute("DROP TABLE IF EXISTS identity.otp_delivery_alert_candidate")
