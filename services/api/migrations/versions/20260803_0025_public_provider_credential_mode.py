from __future__ import annotations

from alembic import op

revision = "20260803_0025"
down_revision = "20260802_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE knowledge.source_provider_capability
        ADD COLUMN credential_mode text NOT NULL DEFAULT 'SECRET_REF'
        """
    )
    op.execute(
        """
        ALTER TABLE knowledge.source_provider_capability
        ALTER COLUMN credential_mode DROP DEFAULT,
        ALTER COLUMN secret_ref DROP NOT NULL
        """
    )
    op.execute(
        """
        ALTER TABLE knowledge.source_provider_capability
        ADD CONSTRAINT source_provider_credential_mode_ck
            CHECK (credential_mode IN ('PUBLIC', 'SECRET_REF')),
        ADD CONSTRAINT source_provider_credential_binding_ck
            CHECK (
                (credential_mode = 'PUBLIC' AND secret_ref IS NULL)
                OR
                (
                    credential_mode = 'SECRET_REF'
                    AND secret_ref ~
                        '^(secret|vault|kms|envref)://[A-Za-z0-9._/@:+-]+$'
                )
            )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM knowledge.source_provider_capability
                WHERE credential_mode = 'PUBLIC'
            ) THEN
                RAISE EXCEPTION
                    'cannot downgrade while PUBLIC provider capabilities exist';
            END IF;
        END
        $$
        """
    )
    op.execute(
        """
        ALTER TABLE knowledge.source_provider_capability
        DROP CONSTRAINT source_provider_credential_binding_ck,
        DROP CONSTRAINT source_provider_credential_mode_ck,
        ALTER COLUMN secret_ref SET NOT NULL,
        DROP COLUMN credential_mode
        """
    )
