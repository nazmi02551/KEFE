from __future__ import annotations

from alembic import op

revision = "20260730_0017"
down_revision = "20260730_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for schema in ("sharing", "community", "privacy"):
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    op.execute(
        """
        CREATE TABLE identity.otp_challenge (
            id uuid PRIMARY KEY,
            channel text NOT NULL CHECK (channel IN ('EMAIL','SMS')),
            identifier_hash char(64) NOT NULL,
            identifier_hint text NOT NULL,
            code_hash char(64) NOT NULL,
            requested_at timestamptz NOT NULL,
            expires_at timestamptz NOT NULL,
            consumed_at timestamptz,
            failed_attempts smallint NOT NULL DEFAULT 0 CHECK (failed_attempts BETWEEN 0 AND 20),
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX otp_challenge_identifier_time_idx
        ON identity.otp_challenge(identifier_hash, requested_at DESC)
        """
    )
    op.execute(
        """
        CREATE TABLE identity.otp_verification (
            token_hash char(64) PRIMARY KEY,
            identifier_hash char(64) NOT NULL,
            channel text NOT NULL CHECK (channel IN ('EMAIL','SMS')),
            identifier_hint text NOT NULL,
            verified_at timestamptz NOT NULL,
            expires_at timestamptz NOT NULL,
            consumed_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE identity.account_identifier (
            identifier_hash char(64) PRIMARY KEY,
            actor_id uuid NOT NULL REFERENCES identity.actor(id) ON DELETE RESTRICT,
            channel text NOT NULL CHECK (channel IN ('EMAIL','SMS')),
            identifier_hint text NOT NULL,
            verified_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX account_identifier_actor_idx
        ON identity.account_identifier(actor_id)
        """
    )
    op.execute(
        """
        CREATE TABLE identity.actor_merge (
            guest_actor_id uuid PRIMARY KEY REFERENCES identity.actor(id) ON DELETE RESTRICT,
            account_actor_id uuid NOT NULL REFERENCES identity.actor(id) ON DELETE RESTRICT,
            merged_at timestamptz NOT NULL,
            CHECK (guest_actor_id <> account_actor_id)
        )
        """
    )

    # Imported/merged committed sessions must coexist with an existing account's
    # own committed session for the same CaseVersion without weakening normal
    # single-session semantics for newly committed sessions.
    op.execute("ALTER TABLE decision.weigh_session ADD COLUMN merged_from_actor_id uuid REFERENCES identity.actor(id) ON DELETE RESTRICT")
    op.execute("DROP INDEX IF EXISTS committed_actor_case_version_idx")
    op.execute(
        """
        CREATE UNIQUE INDEX committed_actor_case_version_idx
        ON decision.weigh_session(actor_id, case_version_id)
        WHERE state = 'COMMITTED' AND merged_from_actor_id IS NULL
        """
    )

    op.execute(
        """
        CREATE TABLE sharing.share_record (
            id uuid PRIMARY KEY,
            token_hash char(64) NOT NULL UNIQUE,
            actor_id uuid NOT NULL REFERENCES identity.actor(id) ON DELETE RESTRICT,
            session_id uuid NOT NULL REFERENCES decision.weigh_session(id) ON DELETE CASCADE,
            case_id uuid NOT NULL REFERENCES content.case_item(id) ON DELETE RESTRICT,
            case_version_id uuid NOT NULL REFERENCES content.case_version(id) ON DELETE RESTRICT,
            include_decision boolean NOT NULL DEFAULT false,
            decision_snapshot jsonb,
            created_at timestamptz NOT NULL,
            expires_at timestamptz NOT NULL,
            revoked_at timestamptz,
            CHECK (include_decision OR decision_snapshot IS NULL)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX share_actor_created_idx
        ON sharing.share_record(actor_id, created_at DESC)
        """
    )

    op.execute(
        """
        CREATE TABLE community.reason (
            id uuid PRIMARY KEY,
            actor_id uuid NOT NULL REFERENCES identity.actor(id) ON DELETE RESTRICT,
            session_id uuid NOT NULL REFERENCES decision.weigh_session(id) ON DELETE CASCADE,
            case_version_id uuid NOT NULL REFERENCES content.case_version(id) ON DELETE RESTRICT,
            tags jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(tags) = 'array'),
            body text,
            moderation_state text NOT NULL CHECK (
                moderation_state IN ('NOT_REQUIRED','PENDING','ALLOWED','BLOCKED')
            ),
            created_at timestamptz NOT NULL,
            updated_at timestamptz NOT NULL,
            UNIQUE(actor_id, session_id)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX community_reason_case_state_idx
        ON community.reason(case_version_id, moderation_state, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE TABLE community.reason_reaction (
            reason_id uuid NOT NULL REFERENCES community.reason(id) ON DELETE CASCADE,
            actor_id uuid NOT NULL REFERENCES identity.actor(id) ON DELETE RESTRICT,
            reaction_code text NOT NULL CHECK (reaction_code IN ('RESONATES','USEFUL','CHALLENGES')),
            created_at timestamptz NOT NULL,
            PRIMARY KEY(reason_id, actor_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE community.reason_report (
            id uuid PRIMARY KEY,
            reason_id uuid NOT NULL REFERENCES community.reason(id) ON DELETE CASCADE,
            reporter_actor_id uuid NOT NULL REFERENCES identity.actor(id) ON DELETE RESTRICT,
            report_code text NOT NULL CHECK (report_code IN ('ABUSE','PERSONAL_DATA','MISLEADING','OTHER')),
            created_at timestamptz NOT NULL,
            UNIQUE(reason_id, reporter_actor_id, report_code)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE privacy.actor_deletion_receipt (
            id uuid PRIMARY KEY,
            actor_id uuid NOT NULL,
            actor_kind text NOT NULL,
            deleted_at timestamptz NOT NULL,
            private_data_deleted boolean NOT NULL,
            aggregate_contributions_anonymized boolean NOT NULL,
            policy_version text NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS privacy.actor_deletion_receipt")
    op.execute("DROP TABLE IF EXISTS community.reason_report")
    op.execute("DROP TABLE IF EXISTS community.reason_reaction")
    op.execute("DROP INDEX IF EXISTS community.community_reason_case_state_idx")
    op.execute("DROP TABLE IF EXISTS community.reason")
    op.execute("DROP INDEX IF EXISTS sharing.share_actor_created_idx")
    op.execute("DROP TABLE IF EXISTS sharing.share_record")
    op.execute("DROP INDEX IF EXISTS decision.committed_actor_case_version_idx")
    op.execute("ALTER TABLE decision.weigh_session DROP COLUMN IF EXISTS merged_from_actor_id")
    op.execute(
        """
        CREATE UNIQUE INDEX committed_actor_case_version_idx
        ON decision.weigh_session(actor_id, case_version_id)
        WHERE state = 'COMMITTED'
        """
    )
    op.execute("DROP TABLE IF EXISTS identity.actor_merge")
    op.execute("DROP INDEX IF EXISTS identity.account_identifier_actor_idx")
    op.execute("DROP TABLE IF EXISTS identity.account_identifier")
    op.execute("DROP TABLE IF EXISTS identity.otp_verification")
    op.execute("DROP INDEX IF EXISTS identity.otp_challenge_identifier_time_idx")
    op.execute("DROP TABLE IF EXISTS identity.otp_challenge")
    for schema in ("privacy", "community", "sharing"):
        op.execute(f"DROP SCHEMA IF EXISTS {schema}")
