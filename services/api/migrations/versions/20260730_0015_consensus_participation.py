from __future__ import annotations

from alembic import op

# The filename is retained for PR history continuity; the Alembic revision id is
# the authoritative sequence and follows the existing 20260729_0015 knowledge
# migration so the repository has a single linear head.
revision = "20260730_0016"
down_revision = "20260729_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS collective")
    op.execute(
        """
        CREATE TABLE collective.consensus_card_version (
            id uuid PRIMARY KEY,
            case_version_id uuid NOT NULL
                REFERENCES content.case_version(id) ON DELETE RESTRICT,
            proposition text NOT NULL CHECK (length(btrim(proposition)) > 0),
            stance_codes jsonb NOT NULL
                CHECK (jsonb_typeof(stance_codes) = 'array'),
            reason_tag_codes jsonb NOT NULL DEFAULT '[]'::jsonb
                CHECK (jsonb_typeof(reason_tag_codes) = 'array'),
            max_reason_tags smallint NOT NULL DEFAULT 0
                CHECK (max_reason_tags BETWEEN 0 AND 10),
            methodology_version text NOT NULL,
            status text NOT NULL DEFAULT 'PUBLISHED'
                CHECK (status IN ('DRAFT','PUBLISHED','RETIRED')),
            published_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX consensus_card_case_version_idx
        ON collective.consensus_card_version(case_version_id, status, published_at)
        """
    )
    op.execute(
        """
        CREATE TABLE collective.consensus_participation (
            id uuid PRIMARY KEY,
            card_version_id uuid NOT NULL
                REFERENCES collective.consensus_card_version(id) ON DELETE RESTRICT,
            session_id uuid NOT NULL
                REFERENCES decision.weigh_session(id) ON DELETE CASCADE,
            actor_id uuid NOT NULL
                REFERENCES identity.actor(id) ON DELETE RESTRICT,
            case_version_id uuid NOT NULL
                REFERENCES content.case_version(id) ON DELETE RESTRICT,
            stance_code text NOT NULL
                CHECK (stance_code IN ('AGREE','MIXED','DISAGREE')),
            reason_tag_codes jsonb NOT NULL DEFAULT '[]'::jsonb
                CHECK (jsonb_typeof(reason_tag_codes) = 'array'),
            contribution_class text NOT NULL
                CHECK (contribution_class = 'EXPOSED'),
            idempotency_key text NOT NULL,
            participated_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE(actor_id, card_version_id),
            UNIQUE(actor_id, idempotency_key)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX consensus_participation_card_class_idx
        ON collective.consensus_participation(
            card_version_id,
            contribution_class,
            participated_at
        )
        """
    )
    op.execute(
        """
        CREATE INDEX consensus_participation_session_idx
        ON collective.consensus_participation(session_id, card_version_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS collective.consensus_participation_session_idx")
    op.execute("DROP INDEX IF EXISTS collective.consensus_participation_card_class_idx")
    op.execute("DROP TABLE IF EXISTS collective.consensus_participation")
    op.execute("DROP INDEX IF EXISTS collective.consensus_card_case_version_idx")
    op.execute("DROP TABLE IF EXISTS collective.consensus_card_version")
    op.execute("DROP SCHEMA IF EXISTS collective")
