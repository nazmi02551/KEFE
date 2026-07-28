from __future__ import annotations

from alembic import op

revision = "20260729_0013"
down_revision = "20260728_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE decision.decision_revision (
            id uuid PRIMARY KEY,
            session_id uuid NOT NULL
                REFERENCES decision.weigh_session(id) ON DELETE CASCADE,
            actor_id uuid NOT NULL
                REFERENCES identity.actor(id) ON DELETE RESTRICT,
            case_version_id uuid NOT NULL
                REFERENCES content.case_version(id) ON DELETE RESTRICT,
            revision_no integer NOT NULL CHECK (revision_no > 0),
            flow_step_code text NOT NULL,
            response_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
            private_reason_snapshot jsonb,
            exposure_sequence_at_commit bigint NOT NULL DEFAULT 0
                CHECK (exposure_sequence_at_commit >= 0),
            contribution_class text NOT NULL CHECK (
                contribution_class IN ('CORE_PRE_RESULT','EXPOSED')
            ),
            commit_idempotency_key text NOT NULL,
            committed_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE(session_id, revision_no),
            UNIQUE(session_id, flow_step_code),
            UNIQUE(session_id, commit_idempotency_key)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX decision_revision_actor_case_idx
        ON decision.decision_revision(actor_id, case_version_id, committed_at)
        """
    )

    op.execute(
        """
        CREATE TABLE decision.revision_draft (
            session_id uuid NOT NULL
                REFERENCES decision.weigh_session(id) ON DELETE CASCADE,
            flow_step_code text NOT NULL,
            response_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
            private_reason_snapshot jsonb,
            updated_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY(session_id, flow_step_code)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE decision.exposure (
            id uuid PRIMARY KEY,
            session_id uuid NOT NULL
                REFERENCES decision.weigh_session(id) ON DELETE CASCADE,
            actor_id uuid NOT NULL
                REFERENCES identity.actor(id) ON DELETE RESTRICT,
            case_version_id uuid NOT NULL
                REFERENCES content.case_version(id) ON DELETE RESTRICT,
            sequence_no bigint NOT NULL CHECK (sequence_no > 0),
            flow_step_code text NOT NULL,
            resource_category text NOT NULL,
            resource_ref text,
            primitive_code text NOT NULL,
            capability_codes jsonb NOT NULL DEFAULT '[]'::jsonb,
            metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
            idempotency_key text NOT NULL,
            occurred_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE(session_id, sequence_no),
            UNIQUE(session_id, idempotency_key)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX exposure_session_category_idx
        ON decision.exposure(session_id, resource_category, sequence_no)
        """
    )

    op.execute(
        """
        CREATE TABLE decision.intervention (
            id uuid PRIMARY KEY,
            session_id uuid NOT NULL
                REFERENCES decision.weigh_session(id) ON DELETE CASCADE,
            exposure_id uuid UNIQUE
                REFERENCES decision.exposure(id) ON DELETE RESTRICT,
            type_code text NOT NULL,
            dimension_code text,
            metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
            occurred_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX intervention_session_time_idx
        ON decision.intervention(session_id, occurred_at, id)
        """
    )

    op.execute(
        """
        CREATE TABLE decision.decision_delta (
            id uuid PRIMARY KEY,
            session_id uuid NOT NULL
                REFERENCES decision.weigh_session(id) ON DELETE CASCADE,
            from_revision_id uuid NOT NULL
                REFERENCES decision.decision_revision(id) ON DELETE RESTRICT,
            to_revision_id uuid NOT NULL UNIQUE
                REFERENCES decision.decision_revision(id) ON DELETE RESTRICT,
            diff_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
            created_at timestamptz NOT NULL DEFAULT now(),
            CHECK (from_revision_id <> to_revision_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE decision.decision_delta_intervention (
            decision_delta_id uuid NOT NULL
                REFERENCES decision.decision_delta(id) ON DELETE CASCADE,
            intervention_id uuid NOT NULL
                REFERENCES decision.intervention(id) ON DELETE RESTRICT,
            PRIMARY KEY(decision_delta_id, intervention_id)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS decision.decision_delta_intervention")
    op.execute("DROP TABLE IF EXISTS decision.decision_delta")
    op.execute("DROP INDEX IF EXISTS decision.intervention_session_time_idx")
    op.execute("DROP TABLE IF EXISTS decision.intervention")
    op.execute("DROP INDEX IF EXISTS decision.exposure_session_category_idx")
    op.execute("DROP TABLE IF EXISTS decision.exposure")
    op.execute("DROP TABLE IF EXISTS decision.revision_draft")
    op.execute("DROP INDEX IF EXISTS decision.decision_revision_actor_case_idx")
    op.execute("DROP TABLE IF EXISTS decision.decision_revision")
