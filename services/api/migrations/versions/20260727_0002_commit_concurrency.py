from __future__ import annotations

from alembic import op

revision = "20260727_0002"
down_revision = "20260727_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE UNIQUE INDEX commit_idempotency_actor_key_idx
        ON decision.weigh_session(actor_id, commit_idempotency_key)
        WHERE commit_idempotency_key IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX outbox_decision_lifecycle_once_idx
        ON analytics.outbox_event(aggregate_id, event_name, event_version)
        WHERE event_name IN ('weigh.started', 'weigh.committed')
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS analytics.outbox_decision_lifecycle_once_idx")
    op.execute("DROP INDEX IF EXISTS decision.commit_idempotency_actor_key_idx")
