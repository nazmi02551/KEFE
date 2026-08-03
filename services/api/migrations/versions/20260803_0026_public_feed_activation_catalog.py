from __future__ import annotations

from alembic import op

revision = "20260803_0026"
down_revision = "20260803_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE knowledge.public_feed_activation_catalog (
            id uuid PRIMARY KEY,
            activation_code text NOT NULL UNIQUE,
            adapter_code text NOT NULL UNIQUE,
            configuration_hash text NOT NULL UNIQUE,
            manifest_schema_version text NOT NULL,
            manifest_json text NOT NULL,
            evidence_ref text NOT NULL,
            recorded_by text NOT NULL,
            recorded_at timestamptz NOT NULL,
            CONSTRAINT public_feed_activation_code_ck CHECK (
                activation_code ~
                '^[a-z0-9][a-z0-9_-]*(\\.[a-z0-9][a-z0-9_-]*)*\\.v[1-9][0-9]*$'
            ),
            CONSTRAINT public_feed_adapter_code_ck CHECK (
                adapter_code ~
                '^[a-z0-9][a-z0-9_-]*(\\.[a-z0-9][a-z0-9_-]*)*\\.v[1-9][0-9]*$'
            ),
            CONSTRAINT public_feed_configuration_hash_ck CHECK (
                configuration_hash ~ '^sha256:[0-9a-f]{64}$'
            ),
            CONSTRAINT public_feed_manifest_schema_ck CHECK (
                manifest_schema_version =
                'kefe.public-feed-activation-manifest/1.0.0'
            ),
            CONSTRAINT public_feed_manifest_size_ck CHECK (
                octet_length(manifest_json) BETWEEN 2 AND 131072
            ),
            CONSTRAINT public_feed_evidence_ref_ck CHECK (
                evidence_ref ~ '^(docref|evidence)://[A-Za-z0-9._/@:+-]+$'
            ),
            CONSTRAINT public_feed_recorded_by_ck CHECK (
                recorded_by ~ '^admin:[0-9a-f-]{36}$'
            )
        )
        """
    )
    op.execute(
        """
        CREATE FUNCTION knowledge.reject_public_feed_activation_catalog_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'public feed activation catalog is immutable';
        END
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER public_feed_activation_catalog_immutable_trg
        BEFORE UPDATE OR DELETE
        ON knowledge.public_feed_activation_catalog
        FOR EACH ROW
        EXECUTE FUNCTION knowledge.reject_public_feed_activation_catalog_mutation()
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM knowledge.public_feed_activation_catalog
            ) THEN
                RAISE EXCEPTION
                    'cannot downgrade while public feed activation catalog entries exist';
            END IF;
        END
        $$
        """
    )
    op.execute(
        """
        DROP TRIGGER public_feed_activation_catalog_immutable_trg
        ON knowledge.public_feed_activation_catalog
        """
    )
    op.execute(
        """
        DROP FUNCTION knowledge.reject_public_feed_activation_catalog_mutation()
        """
    )
    op.execute("DROP TABLE knowledge.public_feed_activation_catalog")
