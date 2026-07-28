from __future__ import annotations

from alembic import op

revision = "20260728_0011"
down_revision = "20260728_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS content_config")
    op.execute(
        """
        CREATE TABLE content_config.configuration_version (
            id uuid PRIMARY KEY,
            version_no integer NOT NULL UNIQUE CHECK (version_no > 0),
            lifecycle_state text NOT NULL CHECK (
                lifecycle_state IN ('DRAFT','PUBLISHED','SUPERSEDED')
            ),
            aggregate jsonb NOT NULL,
            created_by text NOT NULL,
            created_at timestamptz NOT NULL,
            published_at timestamptz,
            cloned_from_version_id uuid NULL,
            updated_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT configuration_clone_fk
                FOREIGN KEY (cloned_from_version_id)
                REFERENCES content_config.configuration_version(id)
                ON DELETE RESTRICT
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX configuration_one_published_idx
        ON content_config.configuration_version ((true))
        WHERE lifecycle_state = 'PUBLISHED'
        """
    )
    op.execute(
        """
        CREATE TABLE content_config.configuration_audit (
            audit_seq bigserial PRIMARY KEY,
            audit_id uuid NOT NULL UNIQUE,
            config_version_id uuid NOT NULL
                REFERENCES content_config.configuration_version(id) ON DELETE RESTRICT,
            actor_ref text NOT NULL,
            command text NOT NULL,
            previous_state text NULL,
            new_state text NOT NULL,
            rationale text NULL,
            occurred_at timestamptz NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE INDEX configuration_audit_version_idx
        ON content_config.configuration_audit(config_version_id, audit_seq)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS content_config.configuration_audit")
    op.execute("DROP TABLE IF EXISTS content_config.configuration_version")
    op.execute("DROP SCHEMA IF EXISTS content_config")
