from __future__ import annotations

from alembic import op

revision = "20260729_0016"
down_revision = "20260729_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS ingestion")
    op.execute(
        """
        CREATE TABLE ingestion.ingestion_run (
            id uuid PRIMARY KEY,
            run_key text NOT NULL UNIQUE CHECK (btrim(run_key) <> ''),
            source_artifact_id uuid
                REFERENCES knowledge.source_artifact(id) ON DELETE RESTRICT,
            normalized_artifact_id uuid
                REFERENCES knowledge.normalized_artifact(id) ON DELETE RESTRICT,
            input_content_hash text NOT NULL CHECK (btrim(input_content_hash) <> ''),
            pipeline_code text NOT NULL CHECK (btrim(pipeline_code) <> ''),
            pipeline_version text NOT NULL CHECK (btrim(pipeline_version) <> ''),
            configuration_hash text NOT NULL CHECK (btrim(configuration_hash) <> ''),
            taxonomy_version text,
            methodology_version text,
            locale text,
            jurisdiction_code text,
            state text NOT NULL CHECK (
                state IN (
                    'QUEUED','RUNNING','SUCCEEDED',
                    'FAILED_RETRYABLE','FAILED_FINAL','CANCELED'
                )
            ),
            created_at timestamptz NOT NULL,
            updated_at timestamptz NOT NULL,
            CHECK (num_nonnulls(source_artifact_id, normalized_artifact_id) = 1)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX ingestion_run_state_idx
        ON ingestion.ingestion_run(state, created_at, id)
        """
    )
    op.execute(
        """
        CREATE TABLE ingestion.stage_execution (
            id uuid PRIMARY KEY,
            run_id uuid NOT NULL
                REFERENCES ingestion.ingestion_run(id) ON DELETE RESTRICT,
            stage_code text NOT NULL CHECK (btrim(stage_code) <> ''),
            stage_version text NOT NULL CHECK (btrim(stage_version) <> ''),
            attempt_no integer NOT NULL CHECK (attempt_no >= 1),
            max_attempts integer NOT NULL CHECK (max_attempts >= 1),
            executor_kind text NOT NULL CHECK (
                executor_kind IN (
                    'DETERMINISTIC','AI_ASSISTED','HUMAN_ASSISTED','EXTERNAL_CAPABILITY'
                )
            ),
            input_hash text NOT NULL CHECK (btrim(input_hash) <> ''),
            output_hash text,
            started_at timestamptz NOT NULL,
            completed_at timestamptz,
            outcome text NOT NULL CHECK (
                outcome IN ('SUCCEEDED','FAILED_RETRYABLE','FAILED_FINAL')
            ),
            error_code text,
            execution_ref text,
            trace_id text,
            CHECK (attempt_no <= max_attempts),
            CHECK (
                (outcome = 'SUCCEEDED' AND output_hash IS NOT NULL AND error_code IS NULL)
                OR
                (outcome <> 'SUCCEEDED' AND error_code IS NOT NULL)
            ),
            CHECK (outcome <> 'FAILED_RETRYABLE' OR attempt_no < max_attempts),
            UNIQUE(run_id, stage_code, stage_version, attempt_no)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX stage_execution_run_idx
        ON ingestion.stage_execution(run_id, stage_code, stage_version, attempt_no)
        """
    )
    op.execute(
        """
        CREATE TABLE ingestion.proposal (
            id uuid PRIMARY KEY,
            proposal_kind text NOT NULL CHECK (btrim(proposal_kind) <> ''),
            payload_schema_ref text NOT NULL CHECK (btrim(payload_schema_ref) <> ''),
            payload_schema_version text NOT NULL CHECK (btrim(payload_schema_version) <> ''),
            payload jsonb NOT NULL,
            payload_hash text NOT NULL CHECK (btrim(payload_hash) <> ''),
            run_id uuid NOT NULL
                REFERENCES ingestion.ingestion_run(id) ON DELETE RESTRICT,
            stage_execution_id uuid NOT NULL
                REFERENCES ingestion.stage_execution(id) ON DELETE RESTRICT,
            taxonomy_version text,
            configuration_version text,
            methodology_version text,
            confidence double precision CHECK (
                confidence IS NULL OR (confidence >= 0 AND confidence <= 1)
            ),
            risk_code text,
            ai_execution_ref text,
            provenance_ref text,
            supersedes_proposal_id uuid
                REFERENCES ingestion.proposal(id) ON DELETE RESTRICT,
            created_at timestamptz NOT NULL,
            CHECK (id <> supersedes_proposal_id)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX proposal_run_idx
        ON ingestion.proposal(run_id, created_at, id)
        """
    )
    op.execute(
        """
        CREATE TABLE ingestion.proposal_review_decision (
            id uuid PRIMARY KEY,
            proposal_id uuid NOT NULL UNIQUE
                REFERENCES ingestion.proposal(id) ON DELETE RESTRICT,
            decision text NOT NULL CHECK (
                decision IN ('ACCEPTED','REJECTED','CHANGES_REQUESTED')
            ),
            reviewer_ref text NOT NULL CHECK (btrim(reviewer_ref) <> ''),
            decided_at timestamptz NOT NULL,
            rationale text,
            reason_code text,
            policy_version text,
            risk_policy_version text
        )
        """
    )
    op.execute(
        """
        CREATE TABLE ingestion.proposal_materialization (
            id uuid PRIMARY KEY,
            proposal_id uuid NOT NULL
                REFERENCES ingestion.proposal(id) ON DELETE RESTRICT,
            review_decision_id uuid NOT NULL
                REFERENCES ingestion.proposal_review_decision(id) ON DELETE RESTRICT,
            target_kind text NOT NULL CHECK (btrim(target_kind) <> ''),
            target_id uuid NOT NULL,
            materialized_at timestamptz NOT NULL,
            UNIQUE(proposal_id, target_kind)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX proposal_materialization_target_idx
        ON ingestion.proposal_materialization(target_kind, target_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ingestion.proposal_materialization")
    op.execute("DROP TABLE IF EXISTS ingestion.proposal_review_decision")
    op.execute("DROP TABLE IF EXISTS ingestion.proposal")
    op.execute("DROP TABLE IF EXISTS ingestion.stage_execution")
    op.execute("DROP TABLE IF EXISTS ingestion.ingestion_run")
    op.execute("DROP SCHEMA IF EXISTS ingestion")
