from __future__ import annotations

from alembic import op

revision = "20260728_0010"
down_revision = "20260728_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS admin_security")

    op.execute(
        """
        CREATE TABLE admin_security.subject (
            id uuid PRIMARY KEY,
            state text NOT NULL CHECK (state IN ('ACTIVE','SUSPENDED','DISABLED')),
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE admin_security.role_assignment (
            id uuid PRIMARY KEY,
            subject_id uuid NOT NULL
                REFERENCES admin_security.subject(id) ON DELETE CASCADE,
            role text NOT NULL CHECK (
                role IN ('EDITOR','REVIEWER','PUBLISHER','TAXONOMY_MANAGER','ACCESS_ADMIN')
            ),
            granted_at timestamptz NOT NULL,
            granted_by_subject_id uuid
                REFERENCES admin_security.subject(id) ON DELETE SET NULL,
            revoked_at timestamptz,
            rationale text
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX admin_active_role_assignment_idx
        ON admin_security.role_assignment(subject_id, role)
        WHERE revoked_at IS NULL
        """
    )

    op.execute(
        """
        CREATE TABLE admin_security.capability_grant (
            id uuid PRIMARY KEY,
            subject_id uuid NOT NULL
                REFERENCES admin_security.subject(id) ON DELETE CASCADE,
            capability text NOT NULL CHECK (
                capability IN (
                    'CONTENT_CREATE','CONTENT_EDIT','CONTENT_SUBMIT_REVIEW','CONTENT_REVIEW',
                    'CONTENT_PUBLISH','CONTENT_WITHDRAW','SOURCE_VERIFY','RISK_REVIEW',
                    'TAXONOMY_MANAGE','ADMIN_ACCESS_MANAGE','AUDIT_READ'
                )
            ),
            granted_at timestamptz NOT NULL,
            granted_by_subject_id uuid
                REFERENCES admin_security.subject(id) ON DELETE SET NULL,
            revoked_at timestamptz,
            rationale text
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX admin_active_capability_grant_idx
        ON admin_security.capability_grant(subject_id, capability)
        WHERE revoked_at IS NULL
        """
    )

    op.execute(
        """
        CREATE TABLE admin_security.session (
            id uuid PRIMARY KEY,
            subject_id uuid NOT NULL
                REFERENCES admin_security.subject(id) ON DELETE CASCADE,
            token_hash char(64) NOT NULL UNIQUE,
            csrf_token_hash char(64) NOT NULL,
            authenticated_at timestamptz NOT NULL,
            mfa_satisfied_at timestamptz NOT NULL,
            step_up_at timestamptz,
            expires_at timestamptz NOT NULL,
            last_seen_at timestamptz NOT NULL,
            revoked_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now(),
            CHECK (expires_at > authenticated_at)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX admin_active_session_token_idx
        ON admin_security.session(token_hash, expires_at)
        WHERE revoked_at IS NULL
        """
    )
    op.execute(
        """
        CREATE INDEX admin_subject_session_idx
        ON admin_security.session(subject_id, created_at DESC)
        """
    )

    op.execute(
        """
        CREATE TABLE admin_security.access_audit (
            sequence_no bigint GENERATED ALWAYS AS IDENTITY UNIQUE,
            event_id uuid PRIMARY KEY,
            actor_subject_id uuid
                REFERENCES admin_security.subject(id) ON DELETE SET NULL,
            target_subject_id uuid
                REFERENCES admin_security.subject(id) ON DELETE SET NULL,
            command text NOT NULL,
            value text,
            rationale text,
            occurred_at timestamptz NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE INDEX admin_access_audit_order_idx
        ON admin_security.access_audit(sequence_no)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS admin_security.access_audit")
    op.execute("DROP TABLE IF EXISTS admin_security.session")
    op.execute("DROP TABLE IF EXISTS admin_security.capability_grant")
    op.execute("DROP TABLE IF EXISTS admin_security.role_assignment")
    op.execute("DROP TABLE IF EXISTS admin_security.subject")
    op.execute("DROP SCHEMA IF EXISTS admin_security")
