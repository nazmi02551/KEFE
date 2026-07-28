from __future__ import annotations

from alembic import op

revision = "20260728_0012"
down_revision = "20260728_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE content.case_version
            ADD COLUMN content_configuration_id uuid NULL
                REFERENCES content_config.configuration_version(id)
                ON DELETE RESTRICT,
            ADD COLUMN content_configuration_version_no integer NULL
                CHECK (
                    content_configuration_version_no IS NULL
                    OR content_configuration_version_no > 0
                ),
            ADD COLUMN flow_template_code text NULL,
            ADD COLUMN flow_template_version_no integer NULL
                CHECK (
                    flow_template_version_no IS NULL
                    OR flow_template_version_no > 0
                ),
            ADD COLUMN resolved_flow jsonb NULL
        """
    )
    op.execute(
        """
        CREATE INDEX case_version_configuration_provenance_idx
        ON content.case_version(
            content_configuration_id,
            content_configuration_version_no
        )
        WHERE content_configuration_id IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE INDEX case_version_flow_template_idx
        ON content.case_version(flow_template_code, flow_template_version_no)
        WHERE flow_template_code IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS content.case_version_flow_template_idx")
    op.execute("DROP INDEX IF EXISTS content.case_version_configuration_provenance_idx")
    op.execute(
        """
        ALTER TABLE content.case_version
            DROP COLUMN IF EXISTS resolved_flow,
            DROP COLUMN IF EXISTS flow_template_version_no,
            DROP COLUMN IF EXISTS flow_template_code,
            DROP COLUMN IF EXISTS content_configuration_version_no,
            DROP COLUMN IF EXISTS content_configuration_id
        """
    )
