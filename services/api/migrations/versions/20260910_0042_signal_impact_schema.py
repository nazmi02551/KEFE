from __future__ import annotations

from alembic import op

revision = "20260910_0042"
down_revision = "20260829_0041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------------------------------------------------------------
    # signal schema
    # ---------------------------------------------------------------
    op.execute("CREATE SCHEMA IF NOT EXISTS signal")

    op.execute(
        """
        CREATE TABLE signal.qualified_signal (
            signal_id                uuid        PRIMARY KEY,
            case_version_id          uuid        NOT NULL,
            case_title               text        NOT NULL CHECK (char_length(case_title) >= 1),
            consensus_statement      text        NOT NULL CHECK (char_length(consensus_statement) >= 1),
            agreement_percentage     numeric(5,2) NOT NULL CHECK (agreement_percentage >= 0 AND agreement_percentage <= 100),
            sample_size              integer     NOT NULL CHECK (sample_size >= 1),
            qualification_tier       text        NOT NULL
                CHECK (qualification_tier IN ('GOLD_STANDARD','SILVER_VALIDATED','BRONZE_OBSERVED','UNQUALIFIED')),
            methodology_version      text        NOT NULL,
            qualification_audit_hash text        NOT NULL,
            certified_at             timestamptz NOT NULL,
            dispatch_status          text        NOT NULL DEFAULT 'PENDING'
                CHECK (dispatch_status IN ('PENDING','DISPATCHED','ACKNOWLEDGED','ACTION_PLEDGED')),
            dispatched_target_id     uuid,
            dispatched_at            timestamptz,
            created_at               timestamptz NOT NULL DEFAULT now(),
            updated_at               timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT signal_dispatch_consistent
                CHECK (
                    (dispatch_status = 'PENDING' AND dispatched_target_id IS NULL AND dispatched_at IS NULL)
                    OR
                    (dispatch_status != 'PENDING' AND dispatched_target_id IS NOT NULL AND dispatched_at IS NOT NULL)
                )
        )
        """
    )

    op.execute(
        """
        CREATE INDEX qualified_signal_case_idx
        ON signal.qualified_signal (case_version_id, certified_at DESC)
        """
    )

    op.execute(
        """
        CREATE INDEX qualified_signal_tier_idx
        ON signal.qualified_signal (qualification_tier, certified_at DESC)
        WHERE qualification_tier != 'UNQUALIFIED'
        """
    )

    # ---------------------------------------------------------------
    # impact schema
    # ---------------------------------------------------------------
    op.execute("CREATE SCHEMA IF NOT EXISTS impact")

    op.execute(
        """
        CREATE TABLE impact.institution_response (
            response_id         uuid        PRIMARY KEY,
            case_version_id     uuid        NOT NULL,
            institution_name    text        NOT NULL CHECK (char_length(institution_name) >= 2),
            authority_role      text        NOT NULL CHECK (char_length(authority_role) >= 2),
            verification_status text        NOT NULL
                CHECK (verification_status IN ('VERIFIED','PENDING_VERIFICATION','REJECTED')),
            response_type       text        NOT NULL
                CHECK (response_type IN (
                    'ACKNOWLEDGE','COMMITMENT','POLICY_CHANGE',
                    'FACTUAL_CLARIFICATION','DECLINE_WITH_REASON'
                )),
            statement           text        NOT NULL CHECK (char_length(statement) >= 10),
            published_at        timestamptz NOT NULL,
            milestone_date      timestamptz,
            created_at          timestamptz NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE INDEX institution_response_case_verified_idx
        ON impact.institution_response (case_version_id, published_at DESC)
        WHERE verification_status = 'VERIFIED'
        """
    )

    op.execute(
        """
        CREATE TABLE impact.action_milestone (
            action_id               uuid        PRIMARY KEY,
            case_version_id         uuid        NOT NULL,
            title                   text        NOT NULL CHECK (char_length(title) >= 3),
            description             text        NOT NULL CHECK (char_length(description) >= 10),
            status                  text        NOT NULL
                CHECK (status IN ('PROPOSED','IN_PROGRESS','VERIFIED_COMPLETE','STALLED')),
            progress_percentage     integer     NOT NULL DEFAULT 0
                CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
            institution_response_id uuid        REFERENCES impact.institution_response(response_id),
            target_completion_date  timestamptz,
            evidence_summary        text,
            evidence_url            text,
            created_at              timestamptz NOT NULL DEFAULT now(),
            updated_at              timestamptz NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE INDEX action_milestone_case_idx
        ON impact.action_milestone (case_version_id, created_at DESC)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS impact.action_milestone")
    op.execute("DROP TABLE IF EXISTS impact.institution_response")
    op.execute("DROP SCHEMA IF EXISTS impact")
    op.execute("DROP TABLE IF EXISTS signal.qualified_signal")
    op.execute("DROP SCHEMA IF EXISTS signal")