from __future__ import annotations

from alembic import op

revision = "20260804_0026"
down_revision = "20260803_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE knowledge.public_feed_definition (
            id uuid PRIMARY KEY,
            feed_code text NOT NULL,
            definition_version integer NOT NULL,
            adapter_code text NOT NULL UNIQUE,
            definition jsonb NOT NULL,
            interval_seconds integer NOT NULL,
            max_dispatch_attempts integer NOT NULL,
            configuration_hash text NOT NULL,
            lifecycle_state text NOT NULL,
            created_at timestamptz NOT NULL,
            created_by_actor_ref text NOT NULL,
            preflighted_at timestamptz,
            preflighted_by_actor_ref text,
            approved_at timestamptz,
            approved_by_actor_ref text,
            retired_at timestamptz,
            retired_by_actor_ref text,
            CONSTRAINT public_feed_definition_identity_uq
                UNIQUE (feed_code, definition_version),
            CONSTRAINT public_feed_definition_version_ck
                CHECK (definition_version >= 1),
            CONSTRAINT public_feed_definition_interval_ck
                CHECK (interval_seconds BETWEEN 60 AND 31536000),
            CONSTRAINT public_feed_definition_attempts_ck
                CHECK (max_dispatch_attempts BETWEEN 1 AND 20),
            CONSTRAINT public_feed_definition_state_ck
                CHECK (lifecycle_state IN ('DRAFT', 'APPROVED', 'RETIRED')),
            CONSTRAINT public_feed_definition_hash_ck
                CHECK (configuration_hash ~ '^sha256:[0-9a-f]{64}$'),
            CONSTRAINT public_feed_definition_document_identity_ck CHECK (
                definition ->> 'feed_code' = feed_code
                AND definition ->> 'adapter_code' = adapter_code
            ),
            CONSTRAINT public_feed_definition_preflight_pair_ck CHECK (
                (preflighted_at IS NULL) = (preflighted_by_actor_ref IS NULL)
            ),
            CONSTRAINT public_feed_definition_approval_pair_ck CHECK (
                (approved_at IS NULL) = (approved_by_actor_ref IS NULL)
            ),
            CONSTRAINT public_feed_definition_retirement_pair_ck CHECK (
                (retired_at IS NULL) = (retired_by_actor_ref IS NULL)
            ),
            CONSTRAINT public_feed_definition_state_metadata_ck CHECK (
                (
                    lifecycle_state = 'DRAFT'
                    AND approved_at IS NULL
                    AND retired_at IS NULL
                )
                OR
                (
                    lifecycle_state = 'APPROVED'
                    AND preflighted_at IS NOT NULL
                    AND approved_at IS NOT NULL
                    AND retired_at IS NULL
                )
                OR
                (
                    lifecycle_state = 'RETIRED'
                    AND retired_at IS NOT NULL
                )
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX public_feed_definition_state_idx
        ON knowledge.public_feed_definition(lifecycle_state, feed_code, definition_version)
        """
    )
    op.execute(
        """
        CREATE TABLE knowledge.public_feed_activation (
            id uuid PRIMARY KEY,
            feed_definition_id uuid NOT NULL UNIQUE
                REFERENCES knowledge.public_feed_definition(id),
            feed_code text NOT NULL,
            definition_version integer NOT NULL,
            configuration_hash text NOT NULL,
            adapter_code text NOT NULL UNIQUE,
            schedule_id uuid NOT NULL UNIQUE,
            lifecycle_state text NOT NULL,
            activated_at timestamptz NOT NULL,
            activated_by_actor_ref text NOT NULL,
            updated_at timestamptz NOT NULL,
            updated_by_actor_ref text NOT NULL,
            CONSTRAINT public_feed_activation_state_ck
                CHECK (lifecycle_state IN ('ACTIVE', 'PAUSED', 'RETIRED')),
            CONSTRAINT public_feed_activation_hash_ck
                CHECK (configuration_hash ~ '^sha256:[0-9a-f]{64}$'),
            CONSTRAINT public_feed_activation_version_ck
                CHECK (definition_version >= 1)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE knowledge.public_feed_audit (
            sequence bigserial PRIMARY KEY,
            definition_id uuid NOT NULL
                REFERENCES knowledge.public_feed_definition(id),
            activation_id uuid
                REFERENCES knowledge.public_feed_activation(id),
            action text NOT NULL,
            actor_ref text NOT NULL,
            occurred_at timestamptz NOT NULL,
            configuration_hash text NOT NULL,
            CONSTRAINT public_feed_audit_action_ck CHECK (
                action IN (
                    'DRAFT_REGISTERED',
                    'PREFLIGHT_SUCCEEDED',
                    'APPROVED',
                    'ACTIVATED',
                    'PAUSED',
                    'RESUMED',
                    'ACTIVATION_RETIRED',
                    'DEFINITION_RETIRED'
                )
            ),
            CONSTRAINT public_feed_audit_hash_ck
                CHECK (configuration_hash ~ '^sha256:[0-9a-f]{64}$')
        )
        """
    )
    op.execute(
        """
        CREATE INDEX public_feed_audit_definition_sequence_idx
        ON knowledge.public_feed_audit(definition_id, sequence)
        """
    )
    op.execute(
        """
        CREATE FUNCTION knowledge.guard_public_feed_definition_update()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF NEW.id IS DISTINCT FROM OLD.id
               OR NEW.feed_code IS DISTINCT FROM OLD.feed_code
               OR NEW.definition_version IS DISTINCT FROM OLD.definition_version
               OR NEW.adapter_code IS DISTINCT FROM OLD.adapter_code
               OR NEW.definition IS DISTINCT FROM OLD.definition
               OR NEW.interval_seconds IS DISTINCT FROM OLD.interval_seconds
               OR NEW.max_dispatch_attempts IS DISTINCT FROM OLD.max_dispatch_attempts
               OR NEW.configuration_hash IS DISTINCT FROM OLD.configuration_hash
               OR NEW.created_at IS DISTINCT FROM OLD.created_at
               OR NEW.created_by_actor_ref IS DISTINCT FROM OLD.created_by_actor_ref THEN
                RAISE EXCEPTION 'canonical public feed definition is immutable';
            END IF;

            IF OLD.lifecycle_state = 'DRAFT' AND NEW.lifecycle_state = 'DRAFT' THEN
                IF OLD.preflighted_at IS NOT NULL
                   AND (
                       NEW.preflighted_at IS DISTINCT FROM OLD.preflighted_at
                       OR NEW.preflighted_by_actor_ref
                          IS DISTINCT FROM OLD.preflighted_by_actor_ref
                   ) THEN
                    RAISE EXCEPTION 'public feed preflight metadata is immutable';
                END IF;
            ELSIF NOT (
                (OLD.lifecycle_state = 'DRAFT'
                 AND NEW.lifecycle_state IN ('APPROVED', 'RETIRED'))
                OR
                (OLD.lifecycle_state = 'APPROVED'
                 AND NEW.lifecycle_state = 'RETIRED')
            ) THEN
                RAISE EXCEPTION 'public feed definition transition is invalid';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER public_feed_definition_update_guard_trg
        BEFORE UPDATE ON knowledge.public_feed_definition
        FOR EACH ROW
        EXECUTE FUNCTION knowledge.guard_public_feed_definition_update()
        """
    )
    op.execute(
        """
        CREATE FUNCTION knowledge.guard_public_feed_activation_update()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF NEW.id IS DISTINCT FROM OLD.id
               OR NEW.feed_definition_id IS DISTINCT FROM OLD.feed_definition_id
               OR NEW.feed_code IS DISTINCT FROM OLD.feed_code
               OR NEW.definition_version IS DISTINCT FROM OLD.definition_version
               OR NEW.configuration_hash IS DISTINCT FROM OLD.configuration_hash
               OR NEW.adapter_code IS DISTINCT FROM OLD.adapter_code
               OR NEW.schedule_id IS DISTINCT FROM OLD.schedule_id
               OR NEW.activated_at IS DISTINCT FROM OLD.activated_at
               OR NEW.activated_by_actor_ref IS DISTINCT FROM OLD.activated_by_actor_ref THEN
                RAISE EXCEPTION 'canonical public feed activation identity is immutable';
            END IF;
            IF NOT (
                (OLD.lifecycle_state = 'ACTIVE'
                 AND NEW.lifecycle_state IN ('PAUSED', 'RETIRED'))
                OR
                (OLD.lifecycle_state = 'PAUSED'
                 AND NEW.lifecycle_state IN ('ACTIVE', 'RETIRED'))
            ) THEN
                RAISE EXCEPTION 'public feed activation transition is invalid';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER public_feed_activation_update_guard_trg
        BEFORE UPDATE ON knowledge.public_feed_activation
        FOR EACH ROW
        EXECUTE FUNCTION knowledge.guard_public_feed_activation_update()
        """
    )
    op.execute(
        """
        CREATE FUNCTION knowledge.reject_public_feed_audit_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'canonical public feed audit is append-only';
        END
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER public_feed_audit_append_only_trg
        BEFORE UPDATE OR DELETE ON knowledge.public_feed_audit
        FOR EACH ROW
        EXECUTE FUNCTION knowledge.reject_public_feed_audit_mutation()
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER public_feed_audit_append_only_trg "
        "ON knowledge.public_feed_audit"
    )
    op.execute("DROP FUNCTION knowledge.reject_public_feed_audit_mutation()")
    op.execute(
        "DROP TRIGGER public_feed_activation_update_guard_trg "
        "ON knowledge.public_feed_activation"
    )
    op.execute("DROP FUNCTION knowledge.guard_public_feed_activation_update()")
    op.execute(
        "DROP TRIGGER public_feed_definition_update_guard_trg "
        "ON knowledge.public_feed_definition"
    )
    op.execute("DROP FUNCTION knowledge.guard_public_feed_definition_update()")
    op.execute("DROP TABLE knowledge.public_feed_audit")
    op.execute("DROP TABLE knowledge.public_feed_activation")
    op.execute("DROP TABLE knowledge.public_feed_definition")
