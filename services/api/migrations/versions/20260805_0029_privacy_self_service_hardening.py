from __future__ import annotations

from alembic import op

revision = "20260805_0029"
down_revision = "20260805_0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE UNIQUE INDEX privacy_actor_deletion_receipt_actor_uidx
        ON privacy.actor_deletion_receipt(actor_id)
        """
    )
    op.execute(
        """
        CREATE FUNCTION privacy.reject_deletion_receipt_mutation()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'privacy deletion receipts are append-only';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER privacy_deletion_receipt_append_only_guard
        BEFORE UPDATE OR DELETE ON privacy.actor_deletion_receipt
        FOR EACH ROW EXECUTE FUNCTION privacy.reject_deletion_receipt_mutation()
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS privacy_deletion_receipt_append_only_guard "
        "ON privacy.actor_deletion_receipt"
    )
    op.execute("DROP FUNCTION IF EXISTS privacy.reject_deletion_receipt_mutation()")
    op.execute("DROP INDEX IF EXISTS privacy.privacy_actor_deletion_receipt_actor_uidx")
