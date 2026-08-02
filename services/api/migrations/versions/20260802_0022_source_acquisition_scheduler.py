from __future__ import annotations

from alembic import op

revision = "20260802_0022"
down_revision = "20260802_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE knowledge.source_acquisition_schedule (
            id uuid PRIMARY KEY,
            schedule_key text NOT NULL UNIQUE CHECK (btrim(schedule_key) <> ''),
            adapter_code text NOT NULL CHECK (btrim(adapter_code) <> ''),
            external_locator text NOT NULL CHECK (btrim(external_locator) <> ''),
            pipeline_code text NOT NULL CHECK (btrim(pipeline_code) <> ''),
            pipeline_version text NOT NULL CHECK (btrim(pipeline_version) <> ''),
            configuration_hash text NOT NULL CHECK (btrim(configuration_hash) <> ''),
            taxonomy_version text,
            methodology_version text,
            locale text,
            jurisdiction_code text,
            interval_seconds integer NOT NULL CHECK (
                interval_seconds BETWEEN 60 AND 2592000
            ),
            max_dispatch_attempts integer NOT NULL CHECK (
                max_dispatch_attempts BETWEEN 1 AND 10
            ),
            state text NOT NULL CHECK (state IN ('ACTIVE','PAUSED','RETIRED')),
            next_due_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL,
            updated_at timestamptz NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE INDEX source_acquisition_schedule_due_idx
        ON knowledge.source_acquisition_schedule(state, next_due_at, id)
        """
    )
    op.execute(
        """
        CREATE TABLE knowledge.source_acquisition_dispatch (
            id uuid PRIMARY KEY,
            schedule_id uuid NOT NULL
                REFERENCES knowledge.source_acquisition_schedule(id)
                ON DELETE RESTRICT,
            due_at timestamptz NOT NULL,
            state text NOT NULL CHECK (
                state IN (
                    'PENDING','RUNNING','SUCCEEDED',
                    'RETRYABLE_FAILURE','FINAL_FAILURE','BLOCKED'
                )
            ),
            attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
            worker_ref text,
            claimed_at timestamptz,
            heartbeat_at timestamptz,
            expires_at timestamptz,
            completed_at timestamptz,
            source_artifact_id uuid
                REFERENCES knowledge.source_artifact(id) ON DELETE RESTRICT,
            ingestion_run_id uuid
                REFERENCES ingestion.ingestion_run(id) ON DELETE RESTRICT,
            error_code text,
            created_at timestamptz NOT NULL,
            updated_at timestamptz NOT NULL,
            UNIQUE(schedule_id, due_at),
            CHECK (
                (state = 'PENDING'
                    AND worker_ref IS NULL
                    AND claimed_at IS NULL
                    AND heartbeat_at IS NULL
                    AND expires_at IS NULL
                    AND completed_at IS NULL
                    AND source_artifact_id IS NULL
                    AND ingestion_run_id IS NULL
                    AND error_code IS NULL)
                OR
                (state = 'RUNNING'
                    AND worker_ref IS NOT NULL
                    AND claimed_at IS NOT NULL
                    AND heartbeat_at IS NOT NULL
                    AND expires_at IS NOT NULL
                    AND completed_at IS NULL
                    AND source_artifact_id IS NULL
                    AND ingestion_run_id IS NULL
                    AND error_code IS NULL)
                OR
                (state = 'SUCCEEDED'
                    AND completed_at IS NOT NULL
                    AND source_artifact_id IS NOT NULL
                    AND ingestion_run_id IS NOT NULL
                    AND error_code IS NULL)
                OR
                (state IN ('RETRYABLE_FAILURE','FINAL_FAILURE','BLOCKED')
                    AND completed_at IS NOT NULL
                    AND source_artifact_id IS NULL
                    AND ingestion_run_id IS NULL
                    AND error_code IS NOT NULL)
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX source_acquisition_dispatch_pending_idx
        ON knowledge.source_acquisition_dispatch(state, due_at, id)
        """
    )
    op.execute(
        """
        CREATE INDEX source_acquisition_dispatch_running_expiry_idx
        ON knowledge.source_acquisition_dispatch(expires_at, id)
        WHERE state = 'RUNNING'
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS knowledge.source_acquisition_dispatch")
    op.execute("DROP TABLE IF EXISTS knowledge.source_acquisition_schedule")
