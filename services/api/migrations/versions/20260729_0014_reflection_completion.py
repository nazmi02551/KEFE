from __future__ import annotations

from alembic import op

revision = "20260729_0014"
down_revision = "20260729_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE decision.reflection_completion (
            id uuid PRIMARY KEY,
            session_id uuid NOT NULL
                REFERENCES decision.weigh_session(id) ON DELETE CASCADE,
            actor_id uuid NOT NULL
                REFERENCES identity.actor(id) ON DELETE RESTRICT,
            case_version_id uuid NOT NULL
                REFERENCES content.case_version(id) ON DELETE RESTRICT,
            flow_step_code text NOT NULL,
            latest_revision_id uuid NOT NULL
                REFERENCES decision.decision_revision(id) ON DELETE RESTRICT,
            latest_delta_id uuid
                REFERENCES decision.decision_delta(id) ON DELETE RESTRICT,
            idempotency_key text NOT NULL,
            completed_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE(session_id, flow_step_code, latest_revision_id),
            UNIQUE(session_id, idempotency_key)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX reflection_completion_actor_case_idx
        ON decision.reflection_completion(actor_id, case_version_id, completed_at)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS decision.reflection_completion_actor_case_idx")
    op.execute("DROP TABLE IF EXISTS decision.reflection_completion")
