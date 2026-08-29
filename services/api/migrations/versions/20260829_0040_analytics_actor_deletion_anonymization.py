from __future__ import annotations

from alembic import op

revision = "20260829_0040"
down_revision = "20260829_0039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        WITH deleted_actor AS (
            SELECT id AS actor_id
            FROM identity.actor
            WHERE state = 'DELETED'
            UNION
            SELECT actor_id
            FROM privacy.actor_deletion_receipt
        )
        UPDATE analytics.analytics_event AS event
        SET actor_id = NULL
        FROM deleted_actor
        WHERE event.actor_id = deleted_actor.actor_id
        """
    )
    op.execute(
        """
        WITH deleted_actor AS (
            SELECT id AS actor_id
            FROM identity.actor
            WHERE state = 'DELETED'
            UNION
            SELECT actor_id
            FROM privacy.actor_deletion_receipt
        )
        UPDATE analytics.activation_journey AS journey
        SET actor_id = NULL
        FROM deleted_actor
        WHERE journey.actor_id = deleted_actor.actor_id
        """
    )


def downgrade() -> None:
    # Actor references are deliberately not reconstructed after anonymization.
    pass
