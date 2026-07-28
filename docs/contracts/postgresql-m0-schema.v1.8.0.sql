-- KEFE PostgreSQL executable schema snapshot
-- Contract version: 1.8.0
-- Scope: consumer M0 + M1 editorial authoring + durable Admin security persistence
-- Derived from Alembic revisions 20260727_0001 through 20260728_0010.
-- Migration history under services/api/migrations is the executable source of truth.

CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS content;
CREATE SCHEMA IF NOT EXISTS decision;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS editorial;
CREATE SCHEMA IF NOT EXISTS admin_security;

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
    base_format_code text NOT NULL,
    primary_domain_code text NOT NULL,
    content_risk text NOT NULL,
    CONSTRAINT case_version_content_risk_check
        CHECK (content_risk IN ('L0','L1','L2','L3')),
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

CREATE TABLE content.context_source (
    id uuid PRIMARY KEY,
    case_version_id uuid NOT NULL
        REFERENCES content.case_version(id) ON DELETE RESTRICT,
    title text NOT NULL,
    publisher text NOT NULL,
    source_kind text NOT NULL CHECK (
        source_kind IN ('OFFICIAL','NEWS','RESEARCH','EDITORIAL','OTHER')
    ),
    url text,
    published_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX context_source_case_version_idx
ON content.context_source(case_version_id, created_at, id);

CREATE TABLE content.context_block (
    id uuid PRIMARY KEY,
    case_version_id uuid NOT NULL
        REFERENCES content.case_version(id) ON DELETE RESTRICT,
    display_order integer NOT NULL CHECK (display_order >= 0),
    disclosure_level text NOT NULL CHECK (
        disclosure_level IN ('ESSENTIAL','DETAIL')
    ),
    title text NOT NULL,
    body text NOT NULL,
    claim_status text NOT NULL CHECK (
        claim_status IN ('VERIFIED','CLAIMED','DISPUTED','UNKNOWN')
    ),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(case_version_id, display_order, id)
);

CREATE INDEX context_block_case_version_idx
ON content.context_block(case_version_id, display_order, id);

CREATE TABLE content.context_block_source (
    context_block_id uuid NOT NULL
        REFERENCES content.context_block(id) ON DELETE CASCADE,
    source_id uuid NOT NULL
        REFERENCES content.context_source(id) ON DELETE RESTRICT,
    PRIMARY KEY(context_block_id, source_id)
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

CREATE TABLE decision.private_reason (
    session_id uuid PRIMARY KEY
        REFERENCES decision.weigh_session(id) ON DELETE CASCADE,
    tags jsonb NOT NULL DEFAULT '[]'::jsonb,
    text_body text,
    moderation_state text NOT NULL CHECK (
        moderation_state IN ('NOT_REQUIRED','PENDING','ALLOWED','BLOCKED')
    ),
    visibility text NOT NULL DEFAULT 'PRIVATE' CHECK (visibility = 'PRIVATE'),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (jsonb_typeof(tags) = 'array'),
    CHECK (text_body IS NULL OR char_length(text_body) <= 1000)
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

CREATE TABLE content.perspective_card (
    id uuid PRIMARY KEY,
    case_version_id uuid NOT NULL
        REFERENCES content.case_version(id) ON DELETE RESTRICT,
    slot text NOT NULL CHECK (
        slot IN ('NEAR','OPPOSING','BRIDGE','ALTERNATIVE_CONTEXT')
    ),
    body text NOT NULL CHECK (
        char_length(btrim(body)) > 0 AND char_length(body) <= 1200
    ),
    source_kind text NOT NULL DEFAULT 'CURATED' CHECK (source_kind = 'CURATED'),
    provenance_label text NOT NULL CHECK (char_length(btrim(provenance_label)) > 0),
    moderation_state text NOT NULL DEFAULT 'NOT_REQUIRED' CHECK (
        moderation_state = 'NOT_REQUIRED'
    ),
    status text NOT NULL CHECK (status IN ('DRAFT','PUBLISHED','WITHDRAWN')),
    published_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (status <> 'PUBLISHED' OR published_at IS NOT NULL)
);

CREATE UNIQUE INDEX perspective_one_published_slot_idx
ON content.perspective_card(case_version_id, slot)
WHERE status = 'PUBLISHED';

CREATE INDEX perspective_published_lookup_idx
ON content.perspective_card(case_version_id, published_at, id)
WHERE status = 'PUBLISHED';

CREATE TABLE editorial.case_item (
    id uuid PRIMARY KEY,
    slug text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE editorial.case_version (
    id uuid PRIMARY KEY,
    case_id uuid NOT NULL REFERENCES editorial.case_item(id) ON DELETE RESTRICT,
    version_no integer NOT NULL CHECK (version_no > 0),
    lifecycle_state text NOT NULL CHECK (
        lifecycle_state IN (
            'DRAFT','IN_REVIEW','APPROVED','PUBLISHED','SUPERSEDED','WITHDRAWN'
        )
    ),
    aggregate jsonb NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz,
    UNIQUE(case_id, version_no)
);

CREATE UNIQUE INDEX editorial_one_published_case_version_idx
ON editorial.case_version(case_id)
WHERE lifecycle_state = 'PUBLISHED';

CREATE INDEX editorial_case_version_state_idx
ON editorial.case_version(case_id, lifecycle_state, version_no DESC);

CREATE TABLE editorial.lifecycle_audit (
    sequence_no bigint GENERATED ALWAYS AS IDENTITY UNIQUE,
    audit_id uuid PRIMARY KEY,
    case_id uuid NOT NULL REFERENCES editorial.case_item(id) ON DELETE RESTRICT,
    case_version_id uuid NOT NULL
        REFERENCES editorial.case_version(id) ON DELETE RESTRICT,
    actor_ref text NOT NULL,
    command text NOT NULL,
    previous_state text,
    new_state text NOT NULL,
    rationale text,
    occurred_at timestamptz NOT NULL
);

CREATE INDEX editorial_lifecycle_audit_case_idx
ON editorial.lifecycle_audit(case_id, sequence_no);

CREATE TABLE admin_security.subject (
    id uuid PRIMARY KEY,
    state text NOT NULL CHECK (state IN ('ACTIVE','SUSPENDED','DISABLED')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE admin_security.role_assignment (
    id uuid PRIMARY KEY,
    subject_id uuid NOT NULL
        REFERENCES admin_security.subject(id) ON DELETE CASCADE,
    role text NOT NULL CHECK (
        role IN ('EDITOR','REVIEWER','PUBLISHER','TAXONOMY_MANAGER','ACCESS_ADMIN')
    ),
    granted_at timestamptz NOT NULL,
    granted_by_subject_id uuid
        REFERENCES admin_security.subject(id) ON DELETE SET NULL,
    revoked_at timestamptz,
    rationale text
);

CREATE UNIQUE INDEX admin_active_role_assignment_idx
ON admin_security.role_assignment(subject_id, role)
WHERE revoked_at IS NULL;

CREATE TABLE admin_security.capability_grant (
    id uuid PRIMARY KEY,
    subject_id uuid NOT NULL
        REFERENCES admin_security.subject(id) ON DELETE CASCADE,
    capability text NOT NULL CHECK (
        capability IN (
            'CONTENT_CREATE','CONTENT_EDIT','CONTENT_SUBMIT_REVIEW','CONTENT_REVIEW',
            'CONTENT_PUBLISH','CONTENT_WITHDRAW','SOURCE_VERIFY','RISK_REVIEW',
            'TAXONOMY_MANAGE','ADMIN_ACCESS_MANAGE','AUDIT_READ'
        )
    ),
    granted_at timestamptz NOT NULL,
    granted_by_subject_id uuid
        REFERENCES admin_security.subject(id) ON DELETE SET NULL,
    revoked_at timestamptz,
    rationale text
);

CREATE UNIQUE INDEX admin_active_capability_grant_idx
ON admin_security.capability_grant(subject_id, capability)
WHERE revoked_at IS NULL;

CREATE TABLE admin_security.session (
    id uuid PRIMARY KEY,
    subject_id uuid NOT NULL
        REFERENCES admin_security.subject(id) ON DELETE CASCADE,
    token_hash char(64) NOT NULL UNIQUE,
    csrf_token_hash char(64) NOT NULL,
    authenticated_at timestamptz NOT NULL,
    mfa_satisfied_at timestamptz NOT NULL,
    step_up_at timestamptz,
    expires_at timestamptz NOT NULL,
    last_seen_at timestamptz NOT NULL,
    revoked_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (expires_at > authenticated_at)
);

CREATE INDEX admin_active_session_token_idx
ON admin_security.session(token_hash, expires_at)
WHERE revoked_at IS NULL;

CREATE INDEX admin_subject_session_idx
ON admin_security.session(subject_id, created_at DESC);

CREATE TABLE admin_security.access_audit (
    sequence_no bigint GENERATED ALWAYS AS IDENTITY UNIQUE,
    event_id uuid PRIMARY KEY,
    actor_subject_id uuid
        REFERENCES admin_security.subject(id) ON DELETE SET NULL,
    target_subject_id uuid
        REFERENCES admin_security.subject(id) ON DELETE SET NULL,
    command text NOT NULL,
    value text,
    rationale text,
    occurred_at timestamptz NOT NULL
);

CREATE INDEX admin_access_audit_order_idx
ON admin_security.access_audit(sequence_no);
