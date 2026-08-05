from __future__ import annotations

from alembic import op

revision = "20260805_0027"
down_revision = "20260804_0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE community.reason_moderation_audit (
            id uuid PRIMARY KEY,
            reason_id uuid NOT NULL REFERENCES community.reason(id) ON DELETE RESTRICT,
            actor_ref text NOT NULL,
            previous_state text NOT NULL,
            decided_state text NOT NULL,
            rationale text NOT NULL,
            created_at timestamptz NOT NULL,
            CONSTRAINT reason_moderation_audit_actor_ck
                CHECK (length(btrim(actor_ref)) BETWEEN 1 AND 255),
            CONSTRAINT reason_moderation_audit_previous_state_ck
                CHECK (previous_state IN ('NOT_REQUIRED', 'PENDING', 'ALLOWED')),
            CONSTRAINT reason_moderation_audit_decided_state_ck
                CHECK (decided_state IN ('ALLOWED', 'BLOCKED')),
            CONSTRAINT reason_moderation_audit_rationale_ck
                CHECK (length(btrim(rationale)) BETWEEN 10 AND 1000)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX reason_moderation_audit_reason_created_idx
        ON community.reason_moderation_audit (reason_id, created_at DESC, id DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX reason_report_reason_created_idx
        ON community.reason_report (reason_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX reason_report_reason_code_created_idx
        ON community.reason_report (reason_id, report_code, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX reason_moderation_pending_queue_idx
        ON community.reason (created_at ASC, id ASC)
        WHERE moderation_state = 'PENDING'
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS community.reason_moderation_pending_queue_idx")
    op.execute("DROP INDEX IF EXISTS community.reason_report_reason_code_created_idx")
    op.execute("DROP INDEX IF EXISTS community.reason_report_reason_created_idx")
    op.execute("DROP INDEX IF EXISTS community.reason_moderation_audit_reason_created_idx")
    op.execute("DROP TABLE IF EXISTS community.reason_moderation_audit")
