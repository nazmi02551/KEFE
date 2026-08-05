from __future__ import annotations

from alembic import op

revision = "20260805_0028"
down_revision = "20260805_0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS media")
    op.execute(
        """
        CREATE TABLE media.asset (
            media_asset_id uuid PRIMARY KEY,
            asset_key text NOT NULL UNIQUE,
            kind text NOT NULL CHECK (kind IN ('IMAGE', 'VIDEO')),
            delivery_ref text NOT NULL UNIQUE,
            content_hash text NOT NULL UNIQUE,
            byte_length bigint NOT NULL CHECK (
                byte_length BETWEEN 1 AND 1073741824
            ),
            media_type text NOT NULL,
            title text NOT NULL,
            alt_text text NOT NULL,
            caption text,
            credit_label text NOT NULL,
            source_label text NOT NULL,
            poster_asset_key text,
            state text NOT NULL CHECK (
                state IN ('REGISTERED', 'READY', 'RETIRED')
            ),
            registered_by text NOT NULL,
            registered_at timestamptz NOT NULL,
            CONSTRAINT media_asset_key_ck CHECK (
                asset_key ~ '^[a-z0-9][a-z0-9._-]{2,127}$'
            ),
            CONSTRAINT media_delivery_ref_ck CHECK (
                length(delivery_ref) BETWEEN 13 AND 512 AND
                delivery_ref ~ '^media-ref:[a-z0-9][a-z0-9._:/-]+$'
            ),
            CONSTRAINT media_content_hash_ck CHECK (
                content_hash ~ '^[a-f0-9]{64}$'
            ),
            CONSTRAINT media_type_kind_ck CHECK (
                (kind = 'IMAGE' AND media_type IN (
                    'image/avif','image/jpeg','image/png','image/webp'
                )) OR
                (kind = 'VIDEO' AND media_type IN ('video/mp4','video/webm'))
            ),
            CONSTRAINT media_title_ck CHECK (
                length(btrim(title)) BETWEEN 1 AND 200
            ),
            CONSTRAINT media_alt_text_ck CHECK (
                length(btrim(alt_text)) BETWEEN 1 AND 500
            ),
            CONSTRAINT media_caption_ck CHECK (
                caption IS NULL OR length(btrim(caption)) BETWEEN 1 AND 1000
            ),
            CONSTRAINT media_credit_ck CHECK (
                length(btrim(credit_label)) BETWEEN 1 AND 200
            ),
            CONSTRAINT media_source_ck CHECK (
                length(btrim(source_label)) BETWEEN 1 AND 300
            ),
            CONSTRAINT media_actor_ck CHECK (
                length(btrim(registered_by)) BETWEEN 1 AND 255
            )
        )
        """
    )
    op.execute(
        """
        CREATE TABLE media.asset_audit (
            sequence_no bigint GENERATED ALWAYS AS IDENTITY UNIQUE,
            audit_id uuid PRIMARY KEY,
            media_asset_id uuid NOT NULL
                REFERENCES media.asset(media_asset_id) ON DELETE RESTRICT,
            actor_ref text NOT NULL,
            command text NOT NULL CHECK (
                command IN ('REGISTER','MARK_READY','RETIRE')
            ),
            previous_state text CHECK (
                previous_state IS NULL OR
                previous_state IN ('REGISTERED','READY')
            ),
            new_state text NOT NULL CHECK (
                new_state IN ('REGISTERED','READY','RETIRED')
            ),
            occurred_at timestamptz NOT NULL,
            CONSTRAINT media_audit_actor_ck CHECK (
                length(btrim(actor_ref)) BETWEEN 1 AND 255
            ),
            CONSTRAINT media_audit_transition_ck CHECK (
                (command = 'REGISTER' AND previous_state IS NULL
                    AND new_state = 'REGISTERED') OR
                (command = 'MARK_READY' AND previous_state = 'REGISTERED'
                    AND new_state = 'READY') OR
                (command = 'RETIRE' AND previous_state IN ('REGISTERED','READY')
                    AND new_state = 'RETIRED')
            )
        )
        """
    )
    op.execute(
        """
        CREATE TABLE media.case_version_binding (
            binding_id uuid PRIMARY KEY,
            case_version_id uuid NOT NULL
                REFERENCES editorial.case_version(id) ON DELETE RESTRICT,
            media_asset_id uuid NOT NULL
                REFERENCES media.asset(media_asset_id) ON DELETE RESTRICT,
            slot text NOT NULL CHECK (
                slot IN ('HERO','CONTEXT','REVEAL','IMPACT')
            ),
            priority integer NOT NULL CHECK (
                priority BETWEEN 1 AND 1000000
            ),
            autoplay boolean NOT NULL DEFAULT false CHECK (autoplay = false),
            muted boolean NOT NULL DEFAULT false,
            looping boolean NOT NULL DEFAULT false,
            bound_by text NOT NULL,
            bound_at timestamptz NOT NULL,
            UNIQUE(case_version_id, slot, media_asset_id),
            CONSTRAINT media_binding_actor_ck CHECK (
                length(btrim(bound_by)) BETWEEN 1 AND 255
            )
        )
        """
    )
    op.execute(
        """
        CREATE FUNCTION media.validate_binding_insert()
        RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE
            asset_kind text;
            asset_state text;
        BEGIN
            SELECT kind, state INTO asset_kind, asset_state
            FROM media.asset
            WHERE media_asset_id = NEW.media_asset_id
            FOR SHARE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'media asset does not exist';
            END IF;
            IF asset_state <> 'READY' THEN
                RAISE EXCEPTION 'only READY media may be bound';
            END IF;
            IF NEW.autoplay THEN
                RAISE EXCEPTION 'media autoplay is forbidden';
            END IF;
            IF asset_kind = 'IMAGE' AND (NEW.muted OR NEW.looping) THEN
                RAISE EXCEPTION 'image presentation flags are invalid';
            END IF;
            RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER media_binding_insert_guard
        BEFORE INSERT ON media.case_version_binding
        FOR EACH ROW EXECUTE FUNCTION media.validate_binding_insert()
        """
    )
    op.execute(
        """
        CREATE INDEX media_asset_state_registered_idx
        ON media.asset(state, registered_at DESC, media_asset_id DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX media_binding_case_priority_idx
        ON media.case_version_binding(case_version_id, priority DESC, binding_id)
        """
    )
    op.execute(
        """
        CREATE INDEX media_audit_asset_sequence_idx
        ON media.asset_audit(media_asset_id, sequence_no)
        """
    )
    op.execute(
        """
        CREATE FUNCTION media.reject_asset_immutable_update()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF ROW(
                NEW.media_asset_id, NEW.asset_key, NEW.kind, NEW.delivery_ref,
                NEW.content_hash, NEW.byte_length, NEW.media_type, NEW.title,
                NEW.alt_text, NEW.caption, NEW.credit_label, NEW.source_label,
                NEW.poster_asset_key, NEW.registered_by, NEW.registered_at
            ) IS DISTINCT FROM ROW(
                OLD.media_asset_id, OLD.asset_key, OLD.kind, OLD.delivery_ref,
                OLD.content_hash, OLD.byte_length, OLD.media_type, OLD.title,
                OLD.alt_text, OLD.caption, OLD.credit_label, OLD.source_label,
                OLD.poster_asset_key, OLD.registered_by, OLD.registered_at
            ) THEN
                RAISE EXCEPTION 'media asset immutable fields cannot change';
            END IF;
            IF OLD.state = 'READY' AND NEW.state = 'REGISTERED' THEN
                RAISE EXCEPTION 'media asset lifecycle cannot roll back';
            END IF;
            IF OLD.state = 'RETIRED' AND NEW.state <> 'RETIRED' THEN
                RAISE EXCEPTION 'retired media asset is terminal';
            END IF;
            RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER media_asset_immutable_update_guard
        BEFORE UPDATE ON media.asset
        FOR EACH ROW EXECUTE FUNCTION media.reject_asset_immutable_update()
        """
    )
    op.execute(
        """
        CREATE FUNCTION media.reject_append_only_mutation()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'media history is append-only';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER media_asset_delete_guard
        BEFORE DELETE ON media.asset
        FOR EACH ROW EXECUTE FUNCTION media.reject_append_only_mutation()
        """
    )
    for table in ("asset_audit", "case_version_binding"):
        op.execute(
            f"""
            CREATE TRIGGER media_{table}_append_only_update_guard
            BEFORE UPDATE OR DELETE ON media.{table}
            FOR EACH ROW EXECUTE FUNCTION media.reject_append_only_mutation()
            """
        )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS media_binding_insert_guard ON media.case_version_binding")
    op.execute("DROP FUNCTION IF EXISTS media.validate_binding_insert()")
    op.execute("DROP TRIGGER IF EXISTS media_asset_delete_guard ON media.asset")
    op.execute(
        "DROP TRIGGER IF EXISTS media_case_version_binding_append_only_update_guard ON media.case_version_binding"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS media_asset_audit_append_only_update_guard ON media.asset_audit"
    )
    op.execute("DROP TRIGGER IF EXISTS media_asset_immutable_update_guard ON media.asset")
    op.execute("DROP FUNCTION IF EXISTS media.reject_append_only_mutation()")
    op.execute("DROP FUNCTION IF EXISTS media.reject_asset_immutable_update()")
    op.execute("DROP TABLE IF EXISTS media.case_version_binding")
    op.execute("DROP TABLE IF EXISTS media.asset_audit")
    op.execute("DROP TABLE IF EXISTS media.asset")
    op.execute("DROP SCHEMA IF EXISTS media")
