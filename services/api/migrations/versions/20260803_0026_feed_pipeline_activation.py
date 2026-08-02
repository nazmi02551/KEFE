from __future__ import annotations

from alembic import op

revision = "20260803_0026"
down_revision = "20260803_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE knowledge.feed_pipeline_definition (
            feed_code text PRIMARY KEY,
            adapter_code text NOT NULL,
            external_locator text NOT NULL,
            adoption_configuration_hash text NOT NULL,
            parser_configuration_hash text NOT NULL,
            extraction_pipeline_code text NOT NULL,
            extraction_pipeline_version text NOT NULL,
            acquisition_configuration_hash text NOT NULL,
            interval_seconds integer NOT NULL,
            max_dispatch_attempts integer NOT NULL,
            evidence_capability_ref text NOT NULL,
            lifecycle_state text NOT NULL,
            dependency_fingerprint text NULL,
            verified_at timestamptz NULL,
            created_at timestamptz NOT NULL,
            updated_at timestamptz NOT NULL,
            CONSTRAINT feed_pipeline_feed_code_ck
                CHECK (feed_code ~ '^[A-Za-z0-9][A-Za-z0-9._-]{0,126}\\.v[1-9][0-9]*$'),
            CONSTRAINT feed_pipeline_adapter_code_ck
                CHECK (adapter_code ~ '^[A-Za-z0-9][A-Za-z0-9._-]{0,126}\\.v[1-9][0-9]*$'),
            CONSTRAINT feed_pipeline_locator_ck
                CHECK (
                    external_locator ~ '^https://[^[:space:]#]+$'
                    AND length(external_locator) <= 4096
                ),
            CONSTRAINT feed_pipeline_adoption_hash_ck
                CHECK (adoption_configuration_hash ~ '^sha256:[0-9a-f]{64}$'),
            CONSTRAINT feed_pipeline_parser_hash_ck
                CHECK (parser_configuration_hash ~ '^sha256:[0-9a-f]{64}$'),
            CONSTRAINT feed_pipeline_acquisition_hash_ck
                CHECK (acquisition_configuration_hash ~ '^sha256:[0-9a-f]{64}$'),
            CONSTRAINT feed_pipeline_interval_ck
                CHECK (interval_seconds BETWEEN 60 AND 2592000),
            CONSTRAINT feed_pipeline_dispatch_attempts_ck
                CHECK (max_dispatch_attempts BETWEEN 1 AND 100),
            CONSTRAINT feed_pipeline_evidence_capability_ck
                CHECK (
                    evidence_capability_ref ~
                    '^evidence://capability/[A-Za-z0-9._/@:+-]+$'
                ),
            CONSTRAINT feed_pipeline_lifecycle_ck
                CHECK (lifecycle_state IN ('DRAFT', 'PAUSED', 'ENABLED', 'RETIRED')),
            CONSTRAINT feed_pipeline_verification_ck
                CHECK (
                    (dependency_fingerprint IS NULL AND verified_at IS NULL)
                    OR
                    (
                        dependency_fingerprint ~ '^sha256:[0-9a-f]{64}$'
                        AND verified_at IS NOT NULL
                    )
                ),
            CONSTRAINT feed_pipeline_time_order_ck
                CHECK (updated_at >= created_at)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX feed_pipeline_lifecycle_idx
        ON knowledge.feed_pipeline_definition (lifecycle_state, updated_at, feed_code)
        """
    )
    op.execute(
        """
        CREATE INDEX feed_pipeline_adapter_idx
        ON knowledge.feed_pipeline_definition (adapter_code, lifecycle_state)
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM knowledge.feed_pipeline_definition) THEN
                RAISE EXCEPTION
                    'cannot downgrade while feed pipeline definitions exist';
            END IF;
        END
        $$
        """
    )
    op.execute("DROP TABLE knowledge.feed_pipeline_definition")
