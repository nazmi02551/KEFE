from __future__ import annotations

from alembic import op

revision = "20260728_0009"
down_revision = "20260727_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS editorial")

    op.execute(
        """
        ALTER TABLE content.case_version
        ADD COLUMN base_format_code text,
        ADD COLUMN primary_domain_code text,
        ADD COLUMN content_risk text
        """
    )
    op.execute(
        """
        UPDATE content.case_version cv
        SET
            base_format_code = ci.base_format_code,
            primary_domain_code = ci.primary_domain_code,
            content_risk = ci.content_risk
        FROM content.case_item ci
        WHERE ci.id = cv.case_id
        """
    )
    op.execute(
        """
        ALTER TABLE content.case_version
        ALTER COLUMN base_format_code SET NOT NULL,
        ALTER COLUMN primary_domain_code SET NOT NULL,
        ALTER COLUMN content_risk SET NOT NULL
        """
    )
    op.execute(
        """
        ALTER TABLE content.case_version
        ADD CONSTRAINT case_version_content_risk_check
        CHECK (content_risk IN ('L0','L1','L2','L3'))
        """
    )

    op.execute(
        """
        CREATE TABLE editorial.case_item (
            id uuid PRIMARY KEY,
            slug text NOT NULL UNIQUE,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE editorial.case_version (
            id uuid PRIMARY KEY,
            case_id uuid NOT NULL REFERENCES editorial.case_item(id) ON DELETE RESTRICT,
            version_no integer NOT NULL CHECK (version_no > 0),
            lifecycle_state text NOT NULL CHECK (
                lifecycle_state IN (
                    'DRAFT','IN_REVIEW','APPROVED','PUBLISHED','SUPERSEDED','WITHDRAWN'
                )
            ),
            aggregate jsonb NOT NULL,
            created_at timestamptz NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT now(),
            published_at timestamptz,
            UNIQUE(case_id, version_no)
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX editorial_one_published_case_version_idx
        ON editorial.case_version(case_id)
        WHERE lifecycle_state = 'PUBLISHED'
        """
    )
    op.execute(
        """
        CREATE INDEX editorial_case_version_state_idx
        ON editorial.case_version(case_id, lifecycle_state, version_no DESC)
        """
    )

    op.execute(
        """
        CREATE TABLE editorial.lifecycle_audit (
            sequence_no bigint GENERATED ALWAYS AS IDENTITY UNIQUE,
            audit_id uuid PRIMARY KEY,
            case_id uuid NOT NULL REFERENCES editorial.case_item(id) ON DELETE RESTRICT,
            case_version_id uuid NOT NULL
                REFERENCES editorial.case_version(id) ON DELETE RESTRICT,
            actor_ref text NOT NULL,
            command text NOT NULL,
            previous_state text,
            new_state text NOT NULL,
            rationale text,
            occurred_at timestamptz NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE INDEX editorial_lifecycle_audit_case_idx
        ON editorial.lifecycle_audit(case_id, sequence_no)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS editorial.lifecycle_audit")
    op.execute("DROP TABLE IF EXISTS editorial.case_version")
    op.execute("DROP TABLE IF EXISTS editorial.case_item")
    op.execute("DROP SCHEMA IF EXISTS editorial")
    op.execute(
        """
        ALTER TABLE content.case_version
        DROP CONSTRAINT IF EXISTS case_version_content_risk_check,
        DROP COLUMN IF EXISTS content_risk,
        DROP COLUMN IF EXISTS primary_domain_code,
        DROP COLUMN IF EXISTS base_format_code
        """
    )
