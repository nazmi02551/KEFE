from __future__ import annotations

from alembic import op

revision = "20260802_0023"
down_revision = "20260802_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE ingestion.content_supply_cycle (
            id uuid PRIMARY KEY,
            worker_ref text NOT NULL CHECK (btrim(worker_ref) <> ''),
            plan_hash text NOT NULL CHECK (btrim(plan_hash) <> ''),
            state text NOT NULL CHECK (
                state IN (
                    'RUNNING','IDLE','SUCCEEDED',
                    'DEGRADED','FAILED','ABANDONED'
                )
            ),
            planned_count integer NOT NULL DEFAULT 0
                CHECK (planned_count >= 0),
            dispatch_attempted_count integer NOT NULL DEFAULT 0
                CHECK (dispatch_attempted_count >= 0),
            dispatch_succeeded_count integer NOT NULL DEFAULT 0
                CHECK (
                    dispatch_succeeded_count >= 0
                    AND dispatch_succeeded_count <= dispatch_attempted_count
                ),
            dispatch_non_success_count integer NOT NULL DEFAULT 0
                CHECK (
                    dispatch_non_success_count >= 0
                    AND dispatch_non_success_count <= dispatch_attempted_count
                ),
            ingestion_attempted_count integer NOT NULL DEFAULT 0
                CHECK (ingestion_attempted_count >= 0),
            ingestion_succeeded_count integer NOT NULL DEFAULT 0
                CHECK (
                    ingestion_succeeded_count >= 0
                    AND ingestion_succeeded_count <= ingestion_attempted_count
                ),
            ingestion_non_success_count integer NOT NULL DEFAULT 0
                CHECK (
                    ingestion_non_success_count >= 0
                    AND ingestion_non_success_count <= ingestion_attempted_count
                ),
            started_at timestamptz NOT NULL,
            heartbeat_at timestamptz NOT NULL,
            expires_at timestamptz NOT NULL,
            completed_at timestamptz,
            error_code text,
            CHECK (
                dispatch_succeeded_count + dispatch_non_success_count
                    <= dispatch_attempted_count
            ),
            CHECK (
                ingestion_succeeded_count + ingestion_non_success_count
                    <= ingestion_attempted_count
            ),
            CHECK (
                (state = 'RUNNING'
                    AND completed_at IS NULL
                    AND error_code IS NULL)
                OR
                (state IN ('IDLE','SUCCEEDED')
                    AND completed_at IS NOT NULL
                    AND error_code IS NULL)
                OR
                (state IN ('DEGRADED','FAILED','ABANDONED')
                    AND completed_at IS NOT NULL
                    AND error_code IS NOT NULL)
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX content_supply_cycle_running_expiry_idx
        ON ingestion.content_supply_cycle(expires_at, id)
        WHERE state = 'RUNNING'
        """
    )
    op.execute(
        """
        CREATE INDEX content_supply_cycle_completed_idx
        ON ingestion.content_supply_cycle(completed_at DESC, id DESC)
        WHERE state <> 'RUNNING'
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ingestion.content_supply_cycle")
