from __future__ import annotations

from alembic import op

revision = "20260803_0027"
down_revision = "20260803_0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE knowledge.public_feed_manual_capture_audit (
            audit_seq bigserial PRIMARY KEY,
            event_id uuid NOT NULL UNIQUE,
            execution_id uuid NOT NULL,
            catalog_entry_id uuid NOT NULL
                REFERENCES knowledge.public_feed_catalog(id),
            feed_code text NOT NULL,
            configuration_hash text NOT NULL,
            actor_ref text NOT NULL,
            trace_id text NOT NULL,
            outcome text NOT NULL,
            source_artifact_id uuid,
            ingestion_run_id uuid,
            duration_ms integer NOT NULL,
            error_code text,
            occurred_at timestamptz NOT NULL,
            CONSTRAINT public_feed_manual_capture_hash_ck CHECK (
                configuration_hash ~ '^sha256:[0-9a-f]{64}$'
            ),
            CONSTRAINT public_feed_manual_capture_trace_ck CHECK (
                trace_id ~ '^[A-Za-z0-9._:-]{1,128}$'
            ),
            CONSTRAINT public_feed_manual_capture_outcome_ck CHECK (
                outcome IN (
                    'ATTEMPT_STARTED',
                    'ADMITTED',
                    'BLOCKED',
                    'RETRYABLE_FAILURE',
                    'FINAL_FAILURE'
                )
            ),
            CONSTRAINT public_feed_manual_capture_duration_ck CHECK (
                duration_ms >= 0
            ),
            CONSTRAINT public_feed_manual_capture_started_ck CHECK (
                outcome <> 'ATTEMPT_STARTED'
                OR (
                    source_artifact_id IS NULL
                    AND ingestion_run_id IS NULL
                    AND error_code IS NULL
                    AND duration_ms = 0
                )
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX public_feed_manual_capture_audit_entry_seq_idx
        ON knowledge.public_feed_manual_capture_audit(
            catalog_entry_id,
            audit_seq
        )
        """
    )
    op.execute(
        """
        CREATE INDEX public_feed_manual_capture_audit_execution_seq_idx
        ON knowledge.public_feed_manual_capture_audit(
            execution_id,
            audit_seq
        )
        """
    )
    op.execute(
        """
        CREATE FUNCTION knowledge.reject_public_feed_manual_capture_audit_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'public feed manual capture audit is append-only';
        END
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER public_feed_manual_capture_audit_append_only_trg
        BEFORE UPDATE OR DELETE ON knowledge.public_feed_manual_capture_audit
        FOR EACH ROW
        EXECUTE FUNCTION knowledge.reject_public_feed_manual_capture_audit_mutation()
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER public_feed_manual_capture_audit_append_only_trg "
        "ON knowledge.public_feed_manual_capture_audit"
    )
    op.execute(
        "DROP FUNCTION knowledge.reject_public_feed_manual_capture_audit_mutation()"
    )
    op.execute("DROP TABLE knowledge.public_feed_manual_capture_audit")
