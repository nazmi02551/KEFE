from __future__ import annotations

from alembic import op

revision = "20260730_0018"
down_revision = "20260730_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE content.case_version
          ADD COLUMN content_locale text NOT NULL DEFAULT 'tr-TR',
          ADD COLUMN market_scope text NOT NULL DEFAULT 'GLOBAL',
          ADD COLUMN country_codes text[] NOT NULL DEFAULT ARRAY[]::text[],
          ADD COLUMN cultural_context_note text,
          ADD COLUMN legal_context_note text,
          ADD COLUMN localizations jsonb NOT NULL DEFAULT '{}'::jsonb
        """
    )
    op.execute(
        """
        ALTER TABLE content.case_version
          ADD CONSTRAINT case_version_market_scope_ck
          CHECK (market_scope IN ('GLOBAL', 'COUNTRY_SET')),
          ADD CONSTRAINT case_version_country_scope_ck
          CHECK (
            (market_scope = 'GLOBAL' AND cardinality(country_codes) = 0)
            OR
            (market_scope = 'COUNTRY_SET' AND cardinality(country_codes) BETWEEN 1 AND 32)
          ),
          ADD CONSTRAINT case_version_localizations_object_ck
          CHECK (jsonb_typeof(localizations) = 'object')
        """
    )
    op.execute(
        """
        CREATE INDEX case_version_market_discovery_idx
          ON content.case_version(status, market_scope, published_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX case_version_country_codes_gin_idx
          ON content.case_version USING gin(country_codes)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS content.case_version_country_codes_gin_idx")
    op.execute("DROP INDEX IF EXISTS content.case_version_market_discovery_idx")
    op.execute(
        """
        ALTER TABLE content.case_version
          DROP CONSTRAINT IF EXISTS case_version_localizations_object_ck,
          DROP CONSTRAINT IF EXISTS case_version_country_scope_ck,
          DROP CONSTRAINT IF EXISTS case_version_market_scope_ck,
          DROP COLUMN IF EXISTS localizations,
          DROP COLUMN IF EXISTS legal_context_note,
          DROP COLUMN IF EXISTS cultural_context_note,
          DROP COLUMN IF EXISTS country_codes,
          DROP COLUMN IF EXISTS market_scope,
          DROP COLUMN IF EXISTS content_locale
        """
    )
