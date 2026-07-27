from __future__ import annotations

from alembic import op

revision = "20260727_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    for schema in ("identity", "content", "decision", "analytics"):
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    op.execute(
        """
        CREATE TABLE identity.actor (
            id uuid PRIMARY KEY,
            actor_kind text NOT NULL CHECK (actor_kind IN ('GUEST','ACCOUNT')),
            state text NOT NULL DEFAULT 'ACTIVE' CHECK (state IN ('ACTIVE','SUSPENDED','DELETED')),
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE content.case_item (
            id uuid PRIMARY KEY,
            slug text NOT NULL UNIQUE,
            base_format_code text NOT NULL,
            primary_domain_code text NOT NULL,
            lifecycle_state text NOT NULL CHECK (
                lifecycle_state IN ('DRAFT','IN_REVIEW','PUBLISHED','PAUSED','ARCHIVED','WITHDRAWN')
            ),
            content_risk text NOT NULL CHECK (content_risk IN ('L0','L1','L2','L3')),
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE content.case_version (
            id uuid PRIMARY KEY,
            case_id uuid NOT NULL REFERENCES content.case_item(id) ON DELETE RESTRICT,
            version_no integer NOT NULL CHECK (version_no > 0),
            status text NOT NULL CHECK (
                status IN ('DRAFT','IN_REVIEW','PUBLISHED','SUPERSEDED','WITHDRAWN')
            ),
            title text NOT NULL,
            summary text NOT NULL,
            accepts_weighs boolean NOT NULL DEFAULT true,
            published_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE(case_id, version_no)
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX case_one_live_published_idx
        ON content.case_version(case_id)
        WHERE status = 'PUBLISHED'
        """
    )

    op.execute(
        """
        CREATE TABLE content.issue (
            id uuid PRIMARY KEY,
            case_version_id uuid NOT NULL REFERENCES content.case_version(id) ON DELETE RESTRICT,
            code text NOT NULL,
            title text NOT NULL,
            sort_order integer NOT NULL DEFAULT 0,
            UNIQUE(case_version_id, code)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE content.question (
            id uuid PRIMARY KEY,
            issue_id uuid NOT NULL REFERENCES content.issue(id) ON DELETE RESTRICT,
            stable_code text NOT NULL,
            UNIQUE(issue_id, stable_code)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE content.question_version (
            id uuid PRIMARY KEY,
            question_id uuid NOT NULL REFERENCES content.question(id) ON DELETE RESTRICT,
            version_no integer NOT NULL CHECK (version_no > 0),
            prompt text NOT NULL,
            response_type text NOT NULL,
            response_schema jsonb NOT NULL DEFAULT '{}'::jsonb,
            is_active boolean NOT NULL DEFAULT true,
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE(question_id, version_no)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE decision.weigh_session (
            id uuid PRIMARY KEY,
            actor_id uuid NOT NULL REFERENCES identity.actor(id) ON DELETE RESTRICT,
            case_id uuid NOT NULL REFERENCES content.case_item(id) ON DELETE RESTRICT,
            case_version_id uuid NOT NULL REFERENCES content.case_version(id) ON DELETE RESTRICT,
            state text NOT NULL CHECK (
                state IN ('DRAFT','COMMITTED','BLOCKED_BY_VERSION')
            ),
            commit_idempotency_key text,
            started_at timestamptz NOT NULL DEFAULT now(),
            committed_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            CHECK ((state = 'COMMITTED' AND committed_at IS NOT NULL) OR state <> 'COMMITTED')
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX committed_actor_case_version_idx
        ON decision.weigh_session(actor_id, case_version_id)
        WHERE state = 'COMMITTED'
        """
    )

    op.execute(
        """
        CREATE TABLE decision.response (
            id uuid PRIMARY KEY,
            session_id uuid NOT NULL REFERENCES decision.weigh_session(id) ON DELETE CASCADE,
            question_version_id uuid NOT NULL REFERENCES content.question_version(id) ON DELETE RESTRICT,
            value_json jsonb NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE(session_id, question_version_id)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE analytics.result_snapshot (
            id uuid PRIMARY KEY,
            case_version_id uuid NOT NULL REFERENCES content.case_version(id) ON DELETE RESTRICT,
            layer text NOT NULL CHECK (layer IN ('RAW','TRUSTED','RESEARCH_ELIGIBLE','BALANCED')),
            n integer NOT NULL CHECK (n >= 0),
            confidence_label text NOT NULL CHECK (
                confidence_label IN ('INSUFFICIENT','LOW','MEDIUM','HIGH')
            ),
            payload jsonb NOT NULL,
            generated_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX result_snapshot_lookup_idx
        ON analytics.result_snapshot(case_version_id, layer, generated_at DESC)
        """
    )

    op.execute(
        """
        CREATE TABLE analytics.outbox_event (
            id uuid PRIMARY KEY,
            aggregate_type text NOT NULL,
            aggregate_id uuid NOT NULL,
            event_name text NOT NULL,
            event_version integer NOT NULL CHECK (event_version > 0),
            occurred_at timestamptz NOT NULL,
            payload jsonb NOT NULL,
            published_at timestamptz,
            attempts integer NOT NULL DEFAULT 0,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX outbox_unpublished_idx
        ON analytics.outbox_event(created_at)
        WHERE published_at IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS analytics.outbox_event")
    op.execute("DROP TABLE IF EXISTS analytics.result_snapshot")
    op.execute("DROP TABLE IF EXISTS decision.response")
    op.execute("DROP TABLE IF EXISTS decision.weigh_session")
    op.execute("DROP TABLE IF EXISTS content.question_version")
    op.execute("DROP TABLE IF EXISTS content.question")
    op.execute("DROP TABLE IF EXISTS content.issue")
    op.execute("DROP TABLE IF EXISTS content.case_version")
    op.execute("DROP TABLE IF EXISTS content.case_item")
    op.execute("DROP TABLE IF EXISTS identity.actor")
    for schema in ("analytics", "decision", "content", "identity"):
        op.execute(f"DROP SCHEMA IF EXISTS {schema}")
