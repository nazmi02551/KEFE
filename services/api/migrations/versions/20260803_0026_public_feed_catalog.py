from __future__ import annotations

from alembic import op

revision = "20260803_0026"
down_revision = "20260803_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE knowledge.public_feed_catalog (
            id uuid PRIMARY KEY,
            feed_code text NOT NULL UNIQUE,
            adapter_code text NOT NULL UNIQUE,
            lifecycle_state text NOT NULL,
            definition jsonb NOT NULL,
            configuration_hash text NOT NULL,
            registered_by text NOT NULL,
            registered_at timestamptz NOT NULL,
            approved_by text,
            approved_at timestamptz,
            retired_by text,
            retired_at timestamptz,
            retirement_rationale text,
            CONSTRAINT public_feed_catalog_state_ck CHECK (
                lifecycle_state IN (
                    'REGISTERED',
                    'MANUAL_CAPTURE_APPROVED',
                    'RETIRED'
                )
            ),
            CONSTRAINT public_feed_catalog_hash_ck CHECK (
                configuration_hash ~ '^sha256:[0-9a-f]{64}$'
            ),
            CONSTRAINT public_feed_catalog_definition_identity_ck CHECK (
                definition ->> 'feed_code' = feed_code
                AND definition ->> 'adapter_code' = adapter_code
            ),
            CONSTRAINT public_feed_catalog_transition_metadata_ck CHECK (
                (
                    lifecycle_state = 'REGISTERED'
                    AND approved_by IS NULL
                    AND approved_at IS NULL
                    AND retired_by IS NULL
                    AND retired_at IS NULL
                    AND retirement_rationale IS NULL
                )
                OR
                (
                    lifecycle_state = 'MANUAL_CAPTURE_APPROVED'
                    AND approved_by IS NOT NULL
                    AND approved_at IS NOT NULL
                    AND retired_by IS NULL
                    AND retired_at IS NULL
                    AND retirement_rationale IS NULL
                )
                OR
                (
                    lifecycle_state = 'RETIRED'
                    AND retired_by IS NOT NULL
                    AND retired_at IS NOT NULL
                    AND length(trim(retirement_rationale)) BETWEEN 1 AND 5000
                )
            )
        )
        """
    )
    op.execute(
        """
        CREATE TABLE knowledge.public_feed_catalog_audit (
            audit_seq bigserial PRIMARY KEY,
            audit_id uuid NOT NULL UNIQUE,
            catalog_entry_id uuid NOT NULL REFERENCES knowledge.public_feed_catalog(id),
            feed_code text NOT NULL,
            actor_ref text NOT NULL,
            command text NOT NULL,
            previous_state text,
            new_state text NOT NULL,
            rationale text,
            occurred_at timestamptz NOT NULL,
            CONSTRAINT public_feed_catalog_audit_previous_state_ck CHECK (
                previous_state IS NULL OR previous_state IN (
                    'REGISTERED',
                    'MANUAL_CAPTURE_APPROVED',
                    'RETIRED'
                )
            ),
            CONSTRAINT public_feed_catalog_audit_new_state_ck CHECK (
                new_state IN (
                    'REGISTERED',
                    'MANUAL_CAPTURE_APPROVED',
                    'RETIRED'
                )
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX public_feed_catalog_audit_entry_seq_idx
        ON knowledge.public_feed_catalog_audit(catalog_entry_id, audit_seq)
        """
    )
    op.execute(
        """
        CREATE FUNCTION knowledge.guard_public_feed_catalog_update()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF NEW.feed_code IS DISTINCT FROM OLD.feed_code
               OR NEW.adapter_code IS DISTINCT FROM OLD.adapter_code
               OR NEW.definition IS DISTINCT FROM OLD.definition
               OR NEW.configuration_hash IS DISTINCT FROM OLD.configuration_hash
               OR NEW.registered_by IS DISTINCT FROM OLD.registered_by
               OR NEW.registered_at IS DISTINCT FROM OLD.registered_at THEN
                RAISE EXCEPTION 'public feed definition is immutable';
            END IF;
            IF NOT (
                (OLD.lifecycle_state = 'REGISTERED'
                 AND NEW.lifecycle_state IN ('MANUAL_CAPTURE_APPROVED', 'RETIRED'))
                OR
                (OLD.lifecycle_state = 'MANUAL_CAPTURE_APPROVED'
                 AND NEW.lifecycle_state = 'RETIRED')
            ) THEN
                RAISE EXCEPTION 'public feed lifecycle transition is invalid';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER public_feed_catalog_update_guard_trg
        BEFORE UPDATE ON knowledge.public_feed_catalog
        FOR EACH ROW
        EXECUTE FUNCTION knowledge.guard_public_feed_catalog_update()
        """
    )
    op.execute(
        """
        CREATE FUNCTION knowledge.reject_public_feed_catalog_audit_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'public feed catalog audit is append-only';
        END
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER public_feed_catalog_audit_append_only_trg
        BEFORE UPDATE OR DELETE ON knowledge.public_feed_catalog_audit
        FOR EACH ROW
        EXECUTE FUNCTION knowledge.reject_public_feed_catalog_audit_mutation()
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER public_feed_catalog_audit_append_only_trg "
        "ON knowledge.public_feed_catalog_audit"
    )
    op.execute(
        "DROP FUNCTION knowledge.reject_public_feed_catalog_audit_mutation()"
    )
    op.execute(
        "DROP TRIGGER public_feed_catalog_update_guard_trg "
        "ON knowledge.public_feed_catalog"
    )
    op.execute("DROP FUNCTION knowledge.guard_public_feed_catalog_update()")
    op.execute("DROP TABLE knowledge.public_feed_catalog_audit")
    op.execute("DROP TABLE knowledge.public_feed_catalog")
