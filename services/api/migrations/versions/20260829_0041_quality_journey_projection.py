from __future__ import annotations

from alembic import op

revision = "20260829_0041"
down_revision = "20260829_0040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE analytics.quality_journey (
            session_id uuid PRIMARY KEY,
            case_version_id uuid,
            committed_at timestamptz,
            committed_source_event_id uuid,
            perspective_viewed_at timestamptz,
            perspective_viewed_source_event_id uuid,
            exposure_recorded_at timestamptz,
            exposure_recorded_source_event_id uuid,
            intervention_exposed_at timestamptz,
            intervention_exposed_source_event_id uuid,
            decision_revised_at timestamptz,
            decision_revised_source_event_id uuid,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            CHECK ((committed_at IS NULL) = (committed_source_event_id IS NULL)),
            CHECK (
                (perspective_viewed_at IS NULL) =
                (perspective_viewed_source_event_id IS NULL)
            ),
            CHECK (
                (exposure_recorded_at IS NULL) =
                (exposure_recorded_source_event_id IS NULL)
            ),
            CHECK (
                (intervention_exposed_at IS NULL) =
                (intervention_exposed_source_event_id IS NULL)
            ),
            CHECK (
                (decision_revised_at IS NULL) =
                (decision_revised_source_event_id IS NULL)
            ),
            CHECK (
                committed_at IS NOT NULL OR
                perspective_viewed_at IS NOT NULL OR
                exposure_recorded_at IS NOT NULL OR
                intervention_exposed_at IS NOT NULL OR
                decision_revised_at IS NOT NULL
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX quality_journey_case_idx
        ON analytics.quality_journey(case_version_id, session_id)
        WHERE case_version_id IS NOT NULL
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
                    ('activation.weigh_committed', 1),
                    ('quality.perspective_viewed', 1),
                    ('quality.exposure_recorded', 1),
                    ('quality.intervention_exposed', 1),
                    ('quality.decision_revised', 1)
                )
                GROUP BY session_id
                HAVING count(DISTINCT case_version_id) > 1
            ) THEN
                RAISE EXCEPTION
                    'quality journey backfill found conflicting CaseVersion provenance';
            END IF;
        END $$
        """
    )
    op.execute(
        """
        WITH quality AS (
            SELECT
                source_event_id,
                analytics_name,
                occurred_at,
                session_id,
                case_version_id
            FROM analytics.analytics_event
            WHERE (analytics_name, analytics_version) IN (
                ('activation.weigh_committed', 1),
                ('quality.perspective_viewed', 1),
                ('quality.exposure_recorded', 1),
                ('quality.intervention_exposed', 1),
                ('quality.decision_revised', 1)
            )
        ),
        provenance AS (
            SELECT
                session_id,
                (
                    array_agg(case_version_id ORDER BY occurred_at, source_event_id)
                    FILTER (WHERE case_version_id IS NOT NULL)
                )[1] AS case_version_id
            FROM quality
            GROUP BY session_id
        ),
        committed AS (
            SELECT DISTINCT ON (session_id)
                session_id, occurred_at, source_event_id
            FROM quality
            WHERE analytics_name = 'activation.weigh_committed'
            ORDER BY session_id, occurred_at, source_event_id
        ),
        perspective AS (
            SELECT DISTINCT ON (session_id)
                session_id, occurred_at, source_event_id
            FROM quality
            WHERE analytics_name = 'quality.perspective_viewed'
            ORDER BY session_id, occurred_at, source_event_id
        ),
        exposure AS (
            SELECT DISTINCT ON (session_id)
                session_id, occurred_at, source_event_id
            FROM quality
            WHERE analytics_name = 'quality.exposure_recorded'
            ORDER BY session_id, occurred_at, source_event_id
        ),
        intervention AS (
            SELECT DISTINCT ON (session_id)
                session_id, occurred_at, source_event_id
            FROM quality
            WHERE analytics_name = 'quality.intervention_exposed'
            ORDER BY session_id, occurred_at, source_event_id
        ),
        revision AS (
            SELECT DISTINCT ON (session_id)
                session_id, occurred_at, source_event_id
            FROM quality
            WHERE analytics_name = 'quality.decision_revised'
            ORDER BY session_id, occurred_at, source_event_id
        )
        INSERT INTO analytics.quality_journey (
            session_id,
            case_version_id,
            committed_at,
            committed_source_event_id,
            perspective_viewed_at,
            perspective_viewed_source_event_id,
            exposure_recorded_at,
            exposure_recorded_source_event_id,
            intervention_exposed_at,
            intervention_exposed_source_event_id,
            decision_revised_at,
            decision_revised_source_event_id
        )
        SELECT
            provenance.session_id,
            provenance.case_version_id,
            committed.occurred_at,
            committed.source_event_id,
            perspective.occurred_at,
            perspective.source_event_id,
            exposure.occurred_at,
            exposure.source_event_id,
            intervention.occurred_at,
            intervention.source_event_id,
            revision.occurred_at,
            revision.source_event_id
        FROM provenance
        LEFT JOIN committed USING (session_id)
        LEFT JOIN perspective USING (session_id)
        LEFT JOIN exposure USING (session_id)
        LEFT JOIN intervention USING (session_id)
        LEFT JOIN revision USING (session_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS analytics.quality_journey")
