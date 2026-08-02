from __future__ import annotations

from alembic import op

revision = "20260802_0024"
down_revision = "20260802_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE knowledge.source_provider_capability (
            adapter_code text PRIMARY KEY
                CHECK (btrim(adapter_code) <> ''),
            secret_ref text NOT NULL
                CHECK (
                    secret_ref ~
                    '^(secret|vault|kms|envref)://[A-Za-z0-9._/@:+-]+$'
                ),
            lifecycle_state text NOT NULL
                CHECK (lifecycle_state IN ('ENABLED','PAUSED','RETIRED')),
            quota_limit integer NOT NULL
                CHECK (quota_limit BETWEEN 1 AND 100000),
            quota_window_seconds integer NOT NULL
                CHECK (quota_window_seconds BETWEEN 1 AND 86400),
            failure_threshold integer NOT NULL
                CHECK (failure_threshold BETWEEN 1 AND 1000),
            circuit_open_seconds integer NOT NULL
                CHECK (circuit_open_seconds BETWEEN 1 AND 86400),
            permit_ttl_seconds integer NOT NULL
                CHECK (permit_ttl_seconds BETWEEN 5 AND 3600),
            window_started_at timestamptz NOT NULL,
            window_request_count integer NOT NULL DEFAULT 0
                CHECK (window_request_count >= 0),
            consecutive_failure_count integer NOT NULL DEFAULT 0
                CHECK (consecutive_failure_count >= 0),
            circuit_state text NOT NULL
                CHECK (circuit_state IN ('CLOSED','OPEN','HALF_OPEN')),
            circuit_opened_at timestamptz,
            created_at timestamptz NOT NULL,
            updated_at timestamptz NOT NULL,
            CHECK (
                (circuit_state = 'CLOSED' AND circuit_opened_at IS NULL)
                OR
                (circuit_state IN ('OPEN','HALF_OPEN')
                    AND circuit_opened_at IS NOT NULL)
            )
        )
        """
    )
    op.execute(
        """
        CREATE TABLE knowledge.source_provider_capture_permit (
            id uuid PRIMARY KEY,
            adapter_code text NOT NULL REFERENCES
                knowledge.source_provider_capability(adapter_code)
                ON DELETE RESTRICT,
            state text NOT NULL
                CHECK (state IN ('ACTIVE','SUCCEEDED','FAILED','ABANDONED')),
            was_half_open_probe boolean NOT NULL DEFAULT false,
            admitted_at timestamptz NOT NULL,
            expires_at timestamptz NOT NULL,
            completed_at timestamptz,
            failure_code text,
            CHECK (expires_at > admitted_at),
            CHECK (
                (state = 'ACTIVE'
                    AND completed_at IS NULL
                    AND failure_code IS NULL)
                OR
                (state = 'SUCCEEDED'
                    AND completed_at IS NOT NULL
                    AND failure_code IS NULL)
                OR
                (state IN ('FAILED','ABANDONED')
                    AND completed_at IS NOT NULL
                    AND btrim(failure_code) <> '')
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX source_provider_permit_active_expiry_idx
        ON knowledge.source_provider_capture_permit(adapter_code, expires_at, id)
        WHERE state = 'ACTIVE'
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX source_provider_single_half_open_probe_idx
        ON knowledge.source_provider_capture_permit(adapter_code)
        WHERE state = 'ACTIVE' AND was_half_open_probe
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TABLE IF EXISTS knowledge.source_provider_capture_permit"
    )
    op.execute(
        "DROP TABLE IF EXISTS knowledge.source_provider_capability"
    )
