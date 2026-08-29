from __future__ import annotations

from alembic import op

revision = "20260829_0038"
down_revision = "20260827_0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS analytics")
    op.execute(
        """
        CREATE TABLE analytics.analytics_event (
            id uuid PRIMARY KEY,
            source_event_id uuid NOT NULL,
            source_event_name text NOT NULL CHECK (btrim(source_event_name) <> ''),
            source_event_version integer NOT NULL CHECK (source_event_version > 0),
            analytics_name text NOT NULL CHECK (btrim(analytics_name) <> ''),
            analytics_version integer NOT NULL CHECK (analytics_version > 0),
            occurred_at timestamptz NOT NULL,
            producer_version text NOT NULL CHECK (btrim(producer_version) <> ''),
            actor_id uuid,
            session_id uuid NOT NULL,
            case_version_id uuid,
            contribution_class text CHECK (
                contribution_class IS NULL OR contribution_class IN (
                    'CORE_PRE_RESULT', 'EXPOSED', 'ADVOCACY_SUPPORT'
                )
            ),
            privacy_class text NOT NULL CHECK (
                privacy_class IN (
                    'PRODUCT_ANALYTICS', 'TRUST_AND_SAFETY', 'OPERATIONS_FINOPS'
                )
            ),
            retention_class text NOT NULL CHECK (
                retention_class IN ('STANDARD_13_MONTHS', 'EXTENDED_24_MONTHS')
            ),
            metric_families jsonb NOT NULL CHECK (
                jsonb_typeof(metric_families) = 'array'
            ),
            payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE(source_event_id, analytics_name, analytics_version)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX analytics_event_name_time_idx
        ON analytics.analytics_event(analytics_name, occurred_at, id)
        """
    )
    op.execute(
        """
        CREATE INDEX analytics_event_actor_time_idx
        ON analytics.analytics_event(actor_id, occurred_at, id)
        WHERE actor_id IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE INDEX analytics_event_case_time_idx
        ON analytics.analytics_event(case_version_id, occurred_at, id)
        WHERE case_version_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS analytics.analytics_event")
