-- KEFE PostgreSQL Schema Contract v1.0.0
-- Normative sources: KEFE-MPD v1.2.0, KEFE-ENG v0.5.0, KEFE-DGS v1.1.0
-- UUIDv7 values are generated in the application/DB adapter. No vendor-specific UUIDv7 function is required.

BEGIN;

CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS taxonomy;
CREATE SCHEMA IF NOT EXISTS content;
CREATE SCHEMA IF NOT EXISTS decision;
CREATE SCHEMA IF NOT EXISTS social;
CREATE SCHEMA IF NOT EXISTS trust;
CREATE SCHEMA IF NOT EXISTS integrity;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS research;
CREATE SCHEMA IF NOT EXISTS admin;

-- -------- Identity: pseudonymous core identity only; direct PII belongs behind Identity Vault access boundary. --------
CREATE TABLE identity.actor (
    id uuid PRIMARY KEY,
    actor_kind text NOT NULL CHECK (actor_kind IN ('GUEST','ACCOUNT')),
    state text NOT NULL DEFAULT 'ACTIVE' CHECK (state IN ('ACTIVE','SUSPENDED','DELETED')),
    created_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CHECK ((state = 'DELETED') = (deleted_at IS NOT NULL))
);

CREATE TABLE identity.account_ref (
    id uuid PRIMARY KEY,
    actor_id uuid NOT NULL UNIQUE REFERENCES identity.actor(id) ON DELETE RESTRICT,
    vault_ref text NOT NULL UNIQUE,
    verification_state text NOT NULL DEFAULT 'UNVERIFIED' CHECK (verification_state IN ('UNVERIFIED','PENDING','VERIFIED','REVOKED')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE identity.consent_record (
    id uuid PRIMARY KEY,
    actor_id uuid NOT NULL REFERENCES identity.actor(id) ON DELETE CASCADE,
    purpose_code text NOT NULL,
    policy_version text NOT NULL,
    state text NOT NULL CHECK (state IN ('GRANTED','WITHDRAWN')),
    granted_at timestamptz,
    withdrawn_at timestamptz,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK ((state='GRANTED' AND granted_at IS NOT NULL) OR (state='WITHDRAWN' AND withdrawn_at IS NOT NULL))
);
CREATE INDEX consent_actor_purpose_idx ON identity.consent_record(actor_id, purpose_code, created_at DESC);

-- -------- Taxonomy registries: data-driven, not application enums. --------
CREATE TABLE taxonomy.domain (
    id uuid PRIMARY KEY,
    code text NOT NULL UNIQUE,
    label_key text NOT NULL UNIQUE,
    description_key text,
    sort_order integer NOT NULL DEFAULT 0,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE taxonomy.topic (
    id uuid PRIMARY KEY,
    domain_id uuid NOT NULL REFERENCES taxonomy.domain(id) ON DELETE RESTRICT,
    parent_topic_id uuid REFERENCES taxonomy.topic(id) ON DELETE RESTRICT,
    code text NOT NULL,
    label_key text NOT NULL,
    sort_order integer NOT NULL DEFAULT 0,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(domain_id, code),
    CHECK (id <> parent_topic_id)
);
CREATE INDEX topic_domain_parent_idx ON taxonomy.topic(domain_id, parent_topic_id, sort_order);

CREATE TABLE taxonomy.base_format (
    code text PRIMARY KEY,
    label_key text NOT NULL UNIQUE,
    schema_version text NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE taxonomy.modifier (
    code text PRIMARY KEY,
    label_key text NOT NULL UNIQUE,
    schema_version text NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE taxonomy.modifier_compatibility (
    base_format_code text NOT NULL REFERENCES taxonomy.base_format(code) ON DELETE CASCADE,
    modifier_code text NOT NULL REFERENCES taxonomy.modifier(code) ON DELETE CASCADE,
    compatibility text NOT NULL CHECK (compatibility IN ('ALLOWED','REQUIRES_REVIEW','FORBIDDEN')),
    rule_version text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY(base_format_code, modifier_code)
);

-- -------- Content --------
CREATE TABLE content.event (
    id uuid PRIMARY KEY,
    origin_country_code char(2),
    occurred_at timestamptz,
    lifecycle_state text NOT NULL DEFAULT 'ACTIVE' CHECK (lifecycle_state IN ('ACTIVE','CLOSED','ARCHIVED')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE content.scenario (
    id uuid PRIMARY KEY,
    scenario_kind text NOT NULL CHECK (scenario_kind IN ('EVERGREEN','SYNTHETIC','RESEARCH','HISTORICAL')),
    canonical_locale text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE content.case_item (
    id uuid PRIMARY KEY,
    slug text NOT NULL UNIQUE,
    base_format_code text NOT NULL REFERENCES taxonomy.base_format(code) ON DELETE RESTRICT,
    primary_domain_id uuid NOT NULL REFERENCES taxonomy.domain(id) ON DELETE RESTRICT,
    event_id uuid REFERENCES content.event(id) ON DELETE RESTRICT,
    scenario_id uuid REFERENCES content.scenario(id) ON DELETE RESTRICT,
    lifecycle_state text NOT NULL CHECK (lifecycle_state IN ('DRAFT','IN_REVIEW','PUBLISHED','PAUSED','ARCHIVED','WITHDRAWN')),
    content_risk text NOT NULL CHECK (content_risk IN ('L0','L1','L2','L3')),
    political_risk text CHECK (political_risk IN ('P0','P1','P2','P3','P4')),
    country_scope jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (event_id IS NOT NULL OR scenario_id IS NOT NULL)
);
CREATE INDEX case_state_domain_idx ON content.case_item(lifecycle_state, primary_domain_id, updated_at DESC);
CREATE INDEX case_format_state_idx ON content.case_item(base_format_code, lifecycle_state, updated_at DESC);

CREATE TABLE content.case_domain (
    case_id uuid NOT NULL REFERENCES content.case_item(id) ON DELETE CASCADE,
    domain_id uuid NOT NULL REFERENCES taxonomy.domain(id) ON DELETE RESTRICT,
    role text NOT NULL CHECK (role IN ('PRIMARY','SECONDARY')),
    PRIMARY KEY(case_id, domain_id)
);
CREATE UNIQUE INDEX case_one_primary_domain_idx ON content.case_domain(case_id) WHERE role='PRIMARY';

CREATE TABLE content.case_topic (
    case_id uuid NOT NULL REFERENCES content.case_item(id) ON DELETE CASCADE,
    topic_id uuid NOT NULL REFERENCES taxonomy.topic(id) ON DELETE RESTRICT,
    PRIMARY KEY(case_id, topic_id)
);

CREATE TABLE content.case_modifier (
    case_id uuid NOT NULL REFERENCES content.case_item(id) ON DELETE CASCADE,
    modifier_code text NOT NULL REFERENCES taxonomy.modifier(code) ON DELETE RESTRICT,
    config jsonb NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY(case_id, modifier_code)
);

CREATE TABLE content.case_version (
    id uuid PRIMARY KEY,
    case_id uuid NOT NULL REFERENCES content.case_item(id) ON DELETE RESTRICT,
    version_no integer NOT NULL CHECK (version_no > 0),
    status text NOT NULL CHECK (status IN ('DRAFT','IN_REVIEW','PUBLISHED','SUPERSEDED','WITHDRAWN')),
    canonical_locale text NOT NULL,
    title text NOT NULL,
    summary text NOT NULL,
    context_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    question_set_version text NOT NULL,
    source_set_hash text NOT NULL,
    response_schema_version text NOT NULL,
    accepts_weighs boolean NOT NULL DEFAULT true,
    published_at timestamptz,
    published_by uuid,
    supersedes_version_id uuid REFERENCES content.case_version(id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(case_id, version_no),
    CHECK ((status='PUBLISHED' AND published_at IS NOT NULL) OR status <> 'PUBLISHED')
);
CREATE INDEX case_version_case_status_idx ON content.case_version(case_id, status, version_no DESC);
CREATE UNIQUE INDEX case_one_live_published_idx ON content.case_version(case_id) WHERE status='PUBLISHED';

CREATE TABLE content.issue (
    id uuid PRIMARY KEY,
    case_version_id uuid NOT NULL REFERENCES content.case_version(id) ON DELETE RESTRICT,
    code text NOT NULL,
    title text NOT NULL,
    description text,
    sort_order integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(case_version_id, code)
);

CREATE TABLE content.question (
    id uuid PRIMARY KEY,
    issue_id uuid NOT NULL REFERENCES content.issue(id) ON DELETE RESTRICT,
    stable_code text NOT NULL,
    dimension_code text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(issue_id, stable_code)
);

CREATE TABLE content.question_version (
    id uuid PRIMARY KEY,
    question_id uuid NOT NULL REFERENCES content.question(id) ON DELETE RESTRICT,
    version_no integer NOT NULL CHECK (version_no > 0),
    locale text NOT NULL,
    prompt text NOT NULL,
    response_type text NOT NULL CHECK (response_type IN ('SCALE_10','BINARY','SINGLE_CHOICE','MULTIPLE_CHOICE','RANKING','ALLOCATION','CONTINUOUS_SLIDER','CONFIDENCE','ENOUGH_INFORMATION','OPEN_REASON','DESIRED_OUTCOME','EXPECTED_OUTCOME','BEFORE_AFTER')),
    response_schema jsonb NOT NULL,
    comparability_group text,
    jurisdiction_scope jsonb NOT NULL DEFAULT '[]'::jsonb,
    localization_method text NOT NULL DEFAULT 'CANONICAL',
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(question_id, version_no, locale)
);
CREATE INDEX question_version_question_active_idx ON content.question_version(question_id, is_active, version_no DESC);

CREATE TABLE content.question_option (
    id uuid PRIMARY KEY,
    question_version_id uuid NOT NULL REFERENCES content.question_version(id) ON DELETE CASCADE,
    option_code text NOT NULL,
    label text NOT NULL,
    sort_order integer NOT NULL DEFAULT 0,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE(question_version_id, option_code)
);

-- -------- Trust/source/claim --------
CREATE TABLE trust.source (
    id uuid PRIMARY KEY,
    source_kind text NOT NULL CHECK (source_kind IN ('OFFICIAL','PRIMARY','NEWS','ACADEMIC','SOCIAL_SIGNAL','OTHER')),
    canonical_url text,
    publisher text,
    published_at timestamptz,
    locale text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE trust.claim (
    id uuid PRIMARY KEY,
    case_version_id uuid NOT NULL REFERENCES content.case_version(id) ON DELETE RESTRICT,
    statement text NOT NULL,
    status text NOT NULL CHECK (status IN ('VERIFIED','CLAIMED','DISPUTED','UNKNOWN')),
    reviewed_at timestamptz,
    reviewed_by uuid,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX claim_case_status_idx ON trust.claim(case_version_id, status);

CREATE TABLE trust.claim_source (
    claim_id uuid NOT NULL REFERENCES trust.claim(id) ON DELETE CASCADE,
    source_id uuid NOT NULL REFERENCES trust.source(id) ON DELETE RESTRICT,
    relation text NOT NULL CHECK (relation IN ('SUPPORTS','CONTRADICTS','CONTEXT','ORIGIN')),
    PRIMARY KEY(claim_id, source_id, relation)
);

CREATE TABLE trust.sample_definition (
    code text NOT NULL,
    version text NOT NULL,
    layer text NOT NULL CHECK (layer IN ('RAW','TRUSTED','RESEARCH_ELIGIBLE','BALANCED')),
    definition jsonb NOT NULL,
    effective_from timestamptz NOT NULL,
    retired_at timestamptz,
    PRIMARY KEY(code, version)
);

CREATE TABLE trust.methodology_version (
    version text PRIMARY KEY,
    definition_hash text NOT NULL,
    notes text,
    effective_from timestamptz NOT NULL,
    retired_at timestamptz
);

-- -------- Decision --------
CREATE TABLE decision.weigh_session (
    id uuid PRIMARY KEY,
    actor_id uuid NOT NULL REFERENCES identity.actor(id) ON DELETE RESTRICT,
    case_id uuid NOT NULL REFERENCES content.case_item(id) ON DELETE RESTRICT,
    case_version_id uuid NOT NULL REFERENCES content.case_version(id) ON DELETE RESTRICT,
    journey_stage text NOT NULL CHECK (journey_stage IN ('V0','V1','V2','V3_PLUS')),
    depth text NOT NULL CHECK (depth IN ('QUICK','STANDARD','DEEP')),
    state text NOT NULL CHECK (state IN ('NOT_STARTED','DRAFT','READY_TO_COMMIT','COMMITTING','COMMITTED','ABANDONED','EXPIRED','BLOCKED_BY_VERSION','COMMIT_FAILED_RETRYABLE','COMMIT_FAILED_FINAL')),
    idempotency_key text NOT NULL,
    response_schema_version text NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    committed_at timestamptz,
    expires_at timestamptz,
    client_context jsonb NOT NULL DEFAULT '{}'::jsonb,
    integrity_state text NOT NULL DEFAULT 'PENDING' CHECK (integrity_state IN ('PENDING','ELIGIBLE','REVIEW','EXCLUDED')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(actor_id, idempotency_key),
    CHECK ((state='COMMITTED' AND committed_at IS NOT NULL) OR state <> 'COMMITTED')
);
CREATE INDEX weigh_actor_activity_idx ON decision.weigh_session(actor_id, started_at DESC);
CREATE INDEX weigh_case_version_state_idx ON decision.weigh_session(case_version_id, state, committed_at DESC);
CREATE UNIQUE INDEX one_primary_commit_per_stage_idx ON decision.weigh_session(actor_id, case_version_id, journey_stage, depth) WHERE state='COMMITTED';

CREATE TABLE decision.response (
    id uuid PRIMARY KEY,
    session_id uuid NOT NULL REFERENCES decision.weigh_session(id) ON DELETE CASCADE,
    question_version_id uuid NOT NULL REFERENCES content.question_version(id) ON DELETE RESTRICT,
    response_type text NOT NULL,
    value_json jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    committed_value_hash text,
    UNIQUE(session_id, question_version_id)
);
CREATE INDEX response_question_idx ON decision.response(question_version_id, session_id);

CREATE TABLE decision.exposure (
    id uuid PRIMARY KEY,
    session_id uuid NOT NULL REFERENCES decision.weigh_session(id) ON DELETE CASCADE,
    exposure_type text NOT NULL CHECK (exposure_type IN ('CASE_VERSION','CONTEXT_LAYER','SOURCE','CLAIM','REASON','REASON_CLUSTER','RESULT','IDENTITY_REVEAL','OUTCOME_REVEAL')),
    ref_id uuid,
    ref_code text,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX exposure_session_time_idx ON decision.exposure(session_id, occurred_at);

CREATE TABLE decision.decision_revision (
    id uuid PRIMARY KEY,
    actor_id uuid NOT NULL REFERENCES identity.actor(id) ON DELETE RESTRICT,
    from_session_id uuid NOT NULL REFERENCES decision.weigh_session(id) ON DELETE RESTRICT,
    to_session_id uuid NOT NULL UNIQUE REFERENCES decision.weigh_session(id) ON DELETE RESTRICT,
    trigger text NOT NULL CHECK (trigger IN ('NEW_INFORMATION','PERSPECTIVE','TEMPORAL_RETEST','USER_INITIATED','IDENTITY_REVEAL','OUTCOME_REVEAL')),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (from_session_id <> to_session_id)
);
CREATE INDEX revision_actor_time_idx ON decision.decision_revision(actor_id, created_at DESC);

-- -------- Integrity --------
CREATE TABLE integrity.assessment (
    id uuid PRIMARY KEY,
    session_id uuid NOT NULL REFERENCES decision.weigh_session(id) ON DELETE CASCADE,
    policy_version text NOT NULL,
    state text NOT NULL CHECK (state IN ('PENDING','ELIGIBLE','REVIEW','EXCLUDED')),
    score_band text,
    assessed_at timestamptz NOT NULL DEFAULT now(),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX integrity_session_time_idx ON integrity.assessment(session_id, assessed_at DESC);

CREATE TABLE integrity.signal (
    id uuid PRIMARY KEY,
    assessment_id uuid NOT NULL REFERENCES integrity.assessment(id) ON DELETE CASCADE,
    signal_code text NOT NULL,
    signal_version text NOT NULL,
    band text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- -------- Social / perspectives --------
CREATE TABLE social.reason (
    id uuid PRIMARY KEY,
    actor_id uuid NOT NULL REFERENCES identity.actor(id) ON DELETE RESTRICT,
    case_version_id uuid NOT NULL REFERENCES content.case_version(id) ON DELETE RESTRICT,
    session_id uuid REFERENCES decision.weigh_session(id) ON DELETE SET NULL,
    body text NOT NULL,
    locale text NOT NULL,
    moderation_state text NOT NULL DEFAULT 'PENDING' CHECK (moderation_state IN ('PENDING','PUBLISHED','LIMITED','REJECTED')),
    created_at timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz
);
CREATE INDEX reason_case_state_idx ON social.reason(case_version_id, moderation_state, created_at DESC);

CREATE TABLE social.reason_reaction (
    id uuid PRIMARY KEY,
    reason_id uuid NOT NULL REFERENCES social.reason(id) ON DELETE CASCADE,
    actor_id uuid NOT NULL REFERENCES identity.actor(id) ON DELETE RESTRICT,
    reaction_type text NOT NULL CHECK (reaction_type IN ('PERSUASIVE','NEW_PERSPECTIVE','STRONG_REASON','INFLUENCE')),
    influence text CHECK (influence IN ('NONE','A_LITTLE','A_LOT','CHANGED_DECISION')),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(reason_id, actor_id, reaction_type)
);

CREATE TABLE social.reason_cluster (
    id uuid PRIMARY KEY,
    case_version_id uuid NOT NULL REFERENCES content.case_version(id) ON DELETE RESTRICT,
    cluster_version text NOT NULL,
    stance text CHECK (stance IN ('SUPPORT','OPPOSE','ALTERNATIVE','MIXED')),
    summary text,
    summary_ai_execution_id uuid,
    moderation_state text NOT NULL DEFAULT 'PENDING' CHECK (moderation_state IN ('PENDING','PUBLISHED','LIMITED','REJECTED')),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE social.reason_cluster_member (
    cluster_id uuid NOT NULL REFERENCES social.reason_cluster(id) ON DELETE CASCADE,
    reason_id uuid NOT NULL REFERENCES social.reason(id) ON DELETE CASCADE,
    membership_score numeric(6,5),
    PRIMARY KEY(cluster_id, reason_id)
);

-- -------- Analytics/read models --------
CREATE TABLE analytics.result_snapshot (
    id uuid PRIMARY KEY,
    case_version_id uuid NOT NULL REFERENCES content.case_version(id) ON DELETE RESTRICT,
    question_version_id uuid NOT NULL REFERENCES content.question_version(id) ON DELETE RESTRICT,
    sample_definition_code text NOT NULL,
    sample_definition_version text NOT NULL,
    methodology_version text NOT NULL REFERENCES trust.methodology_version(version) ON DELETE RESTRICT,
    cohort_key text NOT NULL DEFAULT 'ALL',
    n integer NOT NULL CHECK (n >= 0),
    payload jsonb NOT NULL,
    confidence_label text NOT NULL CHECK (confidence_label IN ('INSUFFICIENT','LOW','MEDIUM','HIGH')),
    window_start timestamptz NOT NULL,
    window_end timestamptz NOT NULL,
    generated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(case_version_id, question_version_id, sample_definition_code, sample_definition_version, methodology_version, cohort_key, window_start, window_end),
    FOREIGN KEY(sample_definition_code, sample_definition_version) REFERENCES trust.sample_definition(code, version) ON DELETE RESTRICT,
    CHECK (window_end >= window_start)
);
CREATE INDEX result_reveal_lookup_idx ON analytics.result_snapshot(case_version_id, question_version_id, sample_definition_code, cohort_key, generated_at DESC);

CREATE TABLE analytics.outbox_event (
    id uuid PRIMARY KEY,
    aggregate_type text NOT NULL,
    aggregate_id uuid NOT NULL,
    event_name text NOT NULL,
    event_version integer NOT NULL CHECK (event_version > 0),
    occurred_at timestamptz NOT NULL,
    payload jsonb NOT NULL,
    trace_id text,
    published_at timestamptz,
    attempts integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX outbox_unpublished_idx ON analytics.outbox_event(created_at) WHERE published_at IS NULL;

-- -------- Research --------
CREATE TABLE research.experiment (
    id uuid PRIMARY KEY,
    code text NOT NULL UNIQUE,
    state text NOT NULL CHECK (state IN ('DRAFT','APPROVED','RUNNING','PAUSED','COMPLETED','CANCELLED')),
    protocol_version text NOT NULL,
    consent_policy_version text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE research.assignment (
    id uuid PRIMARY KEY,
    experiment_id uuid NOT NULL REFERENCES research.experiment(id) ON DELETE RESTRICT,
    actor_id uuid NOT NULL REFERENCES identity.actor(id) ON DELETE RESTRICT,
    variant_code text NOT NULL,
    assignment_version text NOT NULL,
    assigned_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(experiment_id, actor_id)
);

-- -------- Admin / AI / audit / config projection --------
CREATE TABLE admin.ai_execution (
    id uuid PRIMARY KEY,
    capability text NOT NULL,
    provider text NOT NULL,
    model_name text NOT NULL,
    model_version text,
    prompt_template_id text NOT NULL,
    prompt_version text NOT NULL,
    input_hash text NOT NULL,
    output_hash text,
    confidence numeric(6,5),
    latency_ms integer,
    cost_micros bigint,
    review_state text NOT NULL DEFAULT 'UNREVIEWED' CHECK (review_state IN ('UNREVIEWED','APPROVED','REJECTED','OVERRIDDEN')),
    reviewer_ref uuid,
    safety_labels jsonb NOT NULL DEFAULT '[]'::jsonb,
    fallback_path jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE social.reason_cluster
    ADD CONSTRAINT reason_cluster_ai_fk FOREIGN KEY(summary_ai_execution_id) REFERENCES admin.ai_execution(id) ON DELETE SET NULL;

CREATE TABLE admin.audit_log (
    id uuid PRIMARY KEY,
    actor_ref uuid,
    action text NOT NULL,
    resource_type text NOT NULL,
    resource_id text,
    before_hash text,
    after_hash text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    trace_id text
);
CREATE INDEX audit_resource_time_idx ON admin.audit_log(resource_type, resource_id, occurred_at DESC);

CREATE TABLE admin.feature_flag (
    key text PRIMARY KEY,
    schema_version text NOT NULL,
    enabled boolean NOT NULL,
    rollout jsonb NOT NULL DEFAULT '{}'::jsonb,
    owner text NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);

COMMIT;
