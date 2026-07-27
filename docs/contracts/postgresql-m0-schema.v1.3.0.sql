-- KEFE PostgreSQL M0 executable schema snapshot
-- Contract version: 1.3.0
-- Scope: Case → Weigh → Commit → Reveal + durable outbox + guest identity + typed questions
-- Derived from Alembic revisions 20260727_0001 through 20260727_0005.
-- Migration history under services/api/migrations is the executable source of truth.

CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS content;
CREATE SCHEMA IF NOT EXISTS decision;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE identity.actor (
    id uuid PRIMARY KEY,
    actor_kind text NOT NULL CHECK (actor_kind IN ('GUEST','ACCOUNT')),
    state text NOT NULL DEFAULT 'ACTIVE' CHECK (state IN ('ACTIVE','SUSPENDED','DELETED')),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE identity.actor_session (
    id uuid PRIMARY KEY,
    actor_id uuid NOT NULL REFERENCES identity.actor(id) ON DELETE CASCADE,
    token_hash char(64) NOT NULL UNIQUE,
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX actor_session_active_lookup_idx
ON identity.actor_session(token_hash, expires_at)
WHERE revoked_at IS NULL;

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
);

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
);

CREATE UNIQUE INDEX case_one_live_published_idx
ON content.case_version(case_id)
WHERE status = 'PUBLISHED';

CREATE TABLE content.issue (
    id uuid PRIMARY KEY,
    case_version_id uuid NOT NULL REFERENCES content.case_version(id) ON DELETE RESTRICT,
    code text NOT NULL,
    title text NOT NULL,
    sort_order integer NOT NULL DEFAULT 0,
    UNIQUE(case_version_id, code)
);

CREATE TABLE content.question (
    id uuid PRIMARY KEY,
    issue_id uuid NOT NULL REFERENCES content.issue(id) ON DELETE RESTRICT,
    stable_code text NOT NULL,
    sort_order integer NOT NULL DEFAULT 0,
    UNIQUE(issue_id, stable_code)
);

CREATE TABLE content.question_version (
    id uuid PRIMARY KEY,
    question_id uuid NOT NULL REFERENCES content.question(id) ON DELETE RESTRICT,
    version_no integer NOT NULL CHECK (version_no > 0),
    prompt text NOT NULL,
    response_type text NOT NULL,
    response_schema jsonb NOT NULL DEFAULT '{}'::jsonb,
    is_required boolean NOT NULL DEFAULT true,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(question_id, version_no)
);

CREATE TABLE decision.weigh_session (
    id uuid PRIMARY KEY,
    actor_id uuid NOT NULL REFERENCES identity.actor(id) ON DELETE RESTRICT,
    case_id uuid NOT NULL REFERENCES content.case_item(id) ON DELETE RESTRICT,
    case_version_id uuid NOT NULL REFERENCES content.case_version(id) ON DELETE RESTRICT,
    state text NOT NULL CHECK (state IN ('DRAFT','COMMITTED','BLOCKED_BY_VERSION')),
    commit_idempotency_key text,
    started_at timestamptz NOT NULL DEFAULT now(),
    committed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK ((state = 'COMMITTED' AND committed_at IS NOT NULL) OR state <> 'COMMITTED')
);

CREATE UNIQUE INDEX committed_actor_case_version_idx
ON decision.weigh_session(actor_id, case_version_id)
WHERE state = 'COMMITTED';

CREATE UNIQUE INDEX commit_idempotency_actor_key_idx
ON decision.weigh_session(actor_id, commit_idempotency_key)
WHERE commit_idempotency_key IS NOT NULL;

CREATE TABLE decision.response (
    id uuid PRIMARY KEY,
    session_id uuid NOT NULL REFERENCES decision.weigh_session(id) ON DELETE CASCADE,
    question_version_id uuid NOT NULL
        REFERENCES content.question_version(id) ON DELETE RESTRICT,
    value_json jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(session_id, question_version_id)
);

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
);

CREATE INDEX result_snapshot_lookup_idx
ON analytics.result_snapshot(case_version_id, layer, generated_at DESC);

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
    next_attempt_at timestamptz NOT NULL DEFAULT now(),
    last_error text,
    lock_owner text,
    locked_until timestamptz,
    dead_lettered_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX outbox_unpublished_idx
ON analytics.outbox_event(created_at)
WHERE published_at IS NULL;

CREATE UNIQUE INDEX outbox_decision_lifecycle_once_idx
ON analytics.outbox_event(aggregate_id, event_name, event_version)
WHERE event_name IN ('weigh.started', 'weigh.committed');

CREATE INDEX outbox_delivery_ready_idx
ON analytics.outbox_event(next_attempt_at, created_at)
WHERE published_at IS NULL AND dead_lettered_at IS NULL;
