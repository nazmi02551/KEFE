from __future__ import annotations

from alembic import op

revision = "20260829_0039"
down_revision = "20260829_0038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE analytics.activation_journey (
            session_id uuid PRIMARY KEY,
            actor_id uuid,
            case_version_id uuid NOT NULL,
            started_at timestamptz,
            started_source_event_id uuid,
            committed_at timestamptz,
            committed_source_event_id uuid,
            result_revealed_at timestamptz,
            result_revealed_source_event_id uuid,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            CHECK (
                (started_at IS NULL) = (started_source_event_id IS NULL)
            ),
            CHECK (
                (committed_at IS NULL) = (committed_source_event_id IS NULL)
            ),
            CHECK (
                (result_revealed_at IS NULL) =
                (result_revealed_source_event_id IS NULL)
            ),
            CHECK (
                started_at IS NOT NULL OR
                committed_at IS NOT NULL OR
                result_revealed_at IS NOT NULL
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX activation_journey_actor_idx
        ON analytics.activation_journey(actor_id, session_id)
        WHERE actor_id IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE INDEX activation_journey_case_idx
        ON analytics.activation_journey(case_version_id, session_id)
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM analytics.analytics_event
                WHERE (analytics_name, analytics_version) IN (
                    ('activation.weigh_started', 1),
                    ('activation.weigh_committed', 1),
                    ('activation.result_revealed', 1)
                )
                GROUP BY session_id
                HAVING
                    bool_or(case_version_id IS NULL) OR
                    count(DISTINCT case_version_id) <> 1 OR
                    count(DISTINCT actor_id) > 1
            ) THEN
                RAISE EXCEPTION
                    'activation journey backfill found conflicting provenance';
            END IF;
        END $$
        """
    )
    op.execute(
        """
        WITH activation AS (
            SELECT
                source_event_id,
                analytics_name,
                occurred_at,
                actor_id,
                session_id,
                case_version_id
            FROM analytics.analytics_event
            WHERE (analytics_name, analytics_version) IN (
                ('activation.weigh_started', 1),
                ('activation.weigh_committed', 1),
                ('activation.result_revealed', 1)
            )
        ),
        provenance AS (
            SELECT
                session_id,
                (
                    array_agg(actor_id ORDER BY occurred_at, source_event_id)
                    FILTER (WHERE actor_id IS NOT NULL)
                )[1] AS actor_id,
                (array_agg(case_version_id ORDER BY occurred_at, source_event_id))[1]
                    AS case_version_id
            FROM activation
            GROUP BY session_id
        ),
        started AS (
            SELECT DISTINCT ON (session_id)
                session_id,
                occurred_at,
                source_event_id
            FROM activation
            WHERE analytics_name = 'activation.weigh_started'
            ORDER BY session_id, occurred_at, source_event_id
        ),
        committed AS (
            SELECT DISTINCT ON (session_id)
                session_id,
                occurred_at,
                source_event_id
            FROM activation
            WHERE analytics_name = 'activation.weigh_committed'
            ORDER BY session_id, occurred_at, source_event_id
        ),
        revealed AS (
            SELECT DISTINCT ON (session_id)
                session_id,
                occurred_at,
                source_event_id
            FROM activation
            WHERE analytics_name = 'activation.result_revealed'
            ORDER BY session_id, occurred_at, source_event_id
        )
        INSERT INTO analytics.activation_journey (
            session_id,
            actor_id,
            case_version_id,
            started_at,
            started_source_event_id,
            committed_at,
            committed_source_event_id,
            result_revealed_at,
            result_revealed_source_event_id
        )
        SELECT
            provenance.session_id,
            provenance.actor_id,
            provenance.case_version_id,
            started.occurred_at,
            started.source_event_id,
            committed.occurred_at,
            committed.source_event_id,
            revealed.occurred_at,
            revealed.source_event_id
        FROM provenance
        LEFT JOIN started USING (session_id)
        LEFT JOIN committed USING (session_id)
        LEFT JOIN revealed USING (session_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS analytics.activation_journey")
