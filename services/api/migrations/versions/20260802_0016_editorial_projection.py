from __future__ import annotations

from alembic import op

revision = "20260802_0016"
down_revision = "20260729_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE editorial.projection_record (
            id uuid PRIMARY KEY,
            candidate_proposal_id uuid NOT NULL UNIQUE,
            proposal_review_decision_id uuid NOT NULL,
            profile_code text NOT NULL CHECK (btrim(profile_code) <> ''),
            profile_version integer NOT NULL CHECK (profile_version > 0),
            idempotency_key text NOT NULL CHECK (btrim(idempotency_key) <> ''),
            requested_by_admin_ref text NOT NULL
                CHECK (btrim(requested_by_admin_ref) <> ''),
            input_hash text NOT NULL CHECK (btrim(input_hash) <> ''),
            authoring_case_id uuid NOT NULL UNIQUE
                REFERENCES editorial.case_item(id) ON DELETE RESTRICT,
            authoring_case_version_id uuid NOT NULL UNIQUE
                REFERENCES editorial.case_version(id) ON DELETE RESTRICT,
            created_at timestamptz NOT NULL,
            UNIQUE(candidate_proposal_id, idempotency_key)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX editorial_projection_record_created_idx
        ON editorial.projection_record(created_at, id)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS editorial.projection_record")
