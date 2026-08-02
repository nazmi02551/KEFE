from __future__ import annotations

from alembic import op

revision = "20260802_0021"
down_revision = "20260802_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE ingestion.run_lease (
            id uuid PRIMARY KEY,
            run_id uuid NOT NULL
                REFERENCES ingestion.ingestion_run(id) ON DELETE RESTRICT,
            worker_ref text NOT NULL CHECK (btrim(worker_ref) <> ''),
            state text NOT NULL CHECK (state IN ('ACTIVE','RELEASED','EXPIRED')),
            claimed_at timestamptz NOT NULL,
            heartbeat_at timestamptz NOT NULL,
            expires_at timestamptz NOT NULL,
            released_at timestamptz,
            release_disposition text CHECK (
                release_disposition IS NULL
                OR release_disposition IN ('REQUEUE','TERMINAL')
            ),
            CHECK (heartbeat_at >= claimed_at),
            CHECK (expires_at > heartbeat_at),
            CHECK (
                (state = 'ACTIVE' AND released_at IS NULL AND release_disposition IS NULL)
                OR
                (state = 'EXPIRED' AND released_at IS NOT NULL AND release_disposition IS NULL)
                OR
                (state = 'RELEASED' AND released_at IS NOT NULL AND release_disposition IS NOT NULL)
            )
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX run_lease_one_active_per_run_idx
        ON ingestion.run_lease(run_id)
        WHERE state = 'ACTIVE'
        """
    )
    op.execute(
        """
        CREATE INDEX run_lease_active_expiry_idx
        ON ingestion.run_lease(expires_at, run_id, id)
        WHERE state = 'ACTIVE'
        """
    )
    op.execute(
        """
        CREATE INDEX run_lease_worker_history_idx
        ON ingestion.run_lease(worker_ref, claimed_at, id)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ingestion.run_lease")
