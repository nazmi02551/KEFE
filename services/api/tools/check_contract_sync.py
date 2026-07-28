from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
API_SRC = REPO_ROOT / "services" / "api" / "src"
CONTRACTS = REPO_ROOT / "docs" / "contracts"


def _registered_error_codes() -> set[str]:
    content = (CONTRACTS / "error-codes.v1.yaml").read_text(encoding="utf-8")
    return set(re.findall(r"^- code: ([A-Z0-9_]+)$", content, flags=re.MULTILINE))


def _used_domain_error_codes() -> set[str]:
    pattern = re.compile(r'DomainError\(\s*"([A-Z0-9_]+)"')
    codes: set[str] = set()
    for path in API_SRC.rglob("*.py"):
        codes.update(pattern.findall(path.read_text(encoding="utf-8")))
    return codes


def _manifest_missing_paths() -> list[str]:
    manifest = (CONTRACTS / "manifest.v1.yaml").read_text(encoding="utf-8")
    paths = re.findall(r"^\s*path: ([^\n]+)$", manifest, flags=re.MULTILINE)
    return [path.strip() for path in paths if not (REPO_ROOT / path.strip()).exists()]


def _source_contains(fragment: str) -> bool:
    return any(fragment in path.read_text(encoding="utf-8") for path in API_SRC.rglob("*.py"))


def _response_ref(operation: dict, status: str = "200") -> str | None:
    return (
        operation.get("responses", {})
        .get(status, {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
        .get("$ref")
    )


def _missing_fields(schemas: dict, schema: str, required: set[str]) -> list[str]:
    properties = schemas.get(schema, {}).get("properties", {})
    return sorted(required - properties.keys())


def _openapi_errors() -> list[str]:
    contract = json.loads((CONTRACTS / "openapi.v1.json").read_text(encoding="utf-8"))
    errors: list[str] = []

    if contract.get("info", {}).get("version") != "0.13.0":
        errors.append("OpenAPI checked-in version must match API v0.13.0")

    bearer = contract.get("components", {}).get("securitySchemes", {}).get("HTTPBearer")
    if bearer != {"scheme": "bearer", "type": "http"}:
        errors.append("OpenAPI must expose HTTP Bearer authentication")

    schemas = contract.get("components", {}).get("schemas", {})
    required_schemas = {
        "GuestCreateRequest",
        "CaseDetailResponse",
        "QuestionResponse",
        "UpdatePrivateReasonRequest",
        "PrivateReasonResponse",
        "PerspectiveCardResponse",
        "PerspectiveMethodologyResponse",
        "PerspectiveResponse",
        "ContextSourceResponse",
        "ContextBlockResponse",
        "ContextSnapshotResponse",
        "AccountOfferResponse",
        "RecentCaseResponse",
        "ProgressResponse",
        "ProgressEnvelopeResponse",
        "AdminSessionResponse",
        "AuthoringVersionResponse",
        "AuditTrailResponse",
        "ConfigurationVersionResponse",
        "ConfigurationVersionsResponse",
        "ConfigurationAuditTrailResponse",
    }
    missing_schemas = sorted(required_schemas - schemas.keys())
    if missing_schemas:
        errors.append(f"OpenAPI missing schemas: {', '.join(missing_schemas)}")

    field_contracts = {
        "QuestionResponse": {
            "question_id",
            "prompt",
            "response_type",
            "required",
            "response_schema",
            "options",
        },
        "PrivateReasonResponse": {
            "session_id",
            "tags",
            "text",
            "moderation_state",
            "visibility",
        },
        "PerspectiveResponse": {
            "session_id",
            "case_version_id",
            "cards",
            "methodology",
        },
        "ContextSnapshotResponse": {"case_version_id", "blocks", "sources"},
        "ProgressEnvelopeResponse": {"account_offer", "progress", "methodology"},
        "ProgressResponse": {
            "readiness",
            "meaningful_weigh_count",
            "distinct_case_count",
            "distinct_domain_count",
            "first_committed_at",
            "last_committed_at",
            "recent_cases",
        },
        "AdminSessionResponse": {
            "admin_subject_id",
            "session_id",
            "roles",
            "direct_capabilities",
            "authenticated_at",
            "mfa_satisfied_at",
            "step_up_at",
            "expires_at",
        },
        "ConfigurationVersionResponse": {
            "id",
            "version_no",
            "state",
            "domains",
            "topics",
            "base_formats",
            "modifiers",
            "modifier_compatibility",
            "primitives",
            "capabilities",
            "flow_templates",
            "risks",
            "claim_states",
            "source_kinds",
            "disclosure_levels",
            "created_at",
            "published_at",
            "cloned_from_version_id",
        },
    }
    for schema, required in field_contracts.items():
        missing = _missing_fields(schemas, schema, required)
        if missing:
            errors.append(f"{schema} missing fields: {', '.join(missing)}")

    progress_properties = schemas.get("ProgressResponse", {}).get("properties", {})
    forbidden_progress_fields = {
        "private_reason_text",
        "raw_response_payload",
        "personality",
        "ideology",
        "political_profile",
        "psychometric_score",
        "streak",
        "leaderboard",
        "xp",
    }
    leaked = sorted(forbidden_progress_fields & progress_properties.keys())
    if leaked:
        errors.append("ProgressResponse leaks forbidden fields: " + ", ".join(leaked))

    paths = contract.get("paths", {})
    response_contracts = {
        ("/v1/cases/{case_id}", "get"): "CaseDetailResponse",
        ("/v1/weigh-sessions/{session_id}/reason", "put"): "PrivateReasonResponse",
        ("/v1/weigh-sessions/{session_id}/perspectives", "get"): "PerspectiveResponse",
        ("/v1/case-versions/{case_version_id}/context", "get"): "ContextSnapshotResponse",
        ("/v1/me/progress", "get"): "ProgressEnvelopeResponse",
        ("/internal/admin/v1/session", "get"): "AdminSessionResponse",
        ("/internal/admin/v1/cases", "post"): "AuthoringVersionResponse",
        ("/internal/admin/v1/cases/{case_id}/audit", "get"): "AuditTrailResponse",
        (
            "/internal/admin/v1/content-configuration/current",
            "get",
        ): "ConfigurationVersionResponse",
        (
            "/internal/admin/v1/content-configuration/versions",
            "get",
        ): "ConfigurationVersionsResponse",
        (
            "/internal/admin/v1/content-configuration/audit",
            "get",
        ): "ConfigurationAuditTrailResponse",
        (
            "/internal/admin/v1/content-configuration/drafts",
            "post",
        ): "ConfigurationVersionResponse",
    }
    created_responses = {
        ("/internal/admin/v1/cases", "post"),
        ("/internal/admin/v1/content-configuration/drafts", "post"),
    }
    for (path, method), schema in response_contracts.items():
        operation = paths.get(path, {}).get(method, {})
        status = "201" if (path, method) in created_responses else "200"
        if _response_ref(operation, status) != f"#/components/schemas/{schema}":
            errors.append(f"{method.upper()} {path} must return {schema}")

    context_operation = paths.get(
        "/v1/case-versions/{case_version_id}/context", {}
    ).get("get", {})
    if context_operation.get("security"):
        errors.append("GET CaseVersion context must remain public before Commit")

    protected_operations = (
        ("/v1/cases/{case_id}/weigh-sessions", "post"),
        ("/v1/weigh-sessions/{session_id}/responses", "put"),
        ("/v1/weigh-sessions/{session_id}/reason", "put"),
        ("/v1/weigh-sessions/{session_id}/commit", "post"),
        ("/v1/weigh-sessions/{session_id}/reveal", "get"),
        ("/v1/weigh-sessions/{session_id}/perspectives", "get"),
        ("/v1/me/progress", "get"),
        ("/v1/identity/session", "delete"),
    )
    for path, method in protected_operations:
        operation = paths.get(path, {}).get(method, {})
        if {"HTTPBearer": []} not in operation.get("security", []):
            errors.append(f"{method.upper()} {path} must require Bearer auth")

    for path, path_item in paths.items():
        if (path.startswith("/admin") or "authoring" in path) and not path.startswith(
            "/internal/admin/v1"
        ):
            errors.append(f"Unexpected Admin/authoring route outside internal boundary: {path}")
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            for parameter in operation.get("parameters", []):
                if parameter.get("name", "").lower() == "x-actor-id":
                    errors.append(f"OpenAPI must not expose X-Actor-Id ({method.upper()} {path})")

    return errors


def _schema_errors() -> list[str]:
    schema = (CONTRACTS / "postgresql-m0-schema.v1.8.0.sql").read_text(encoding="utf-8")
    required_fragments = {
        "commit_idempotency_key text": "explicit Commit idempotency",
        "commit_idempotency_actor_key_idx": "actor-scoped Commit idempotency",
        "outbox_decision_lifecycle_once_idx": "lifecycle outbox uniqueness",
        "next_attempt_at timestamptz": "durable outbox retry",
        "locked_until timestamptz": "durable outbox lease",
        "dead_lettered_at timestamptz": "outbox dead-letter state",
        "CREATE TABLE identity.actor_session": "revocable guest sessions",
        "token_hash char(64) NOT NULL UNIQUE": "hashed credentials",
        "sort_order integer NOT NULL DEFAULT 0": "deterministic question order",
        "is_required boolean NOT NULL DEFAULT true": "question requiredness",
        "CREATE TABLE decision.private_reason": "private reason persistence",
        "visibility text NOT NULL DEFAULT 'PRIVATE' CHECK (visibility = 'PRIVATE')": (
            "private-only reason visibility"
        ),
        "moderation_state IN ('NOT_REQUIRED','PENDING','ALLOWED','BLOCKED')": (
            "reason moderation lifecycle"
        ),
        "CREATE TABLE content.perspective_card": "CaseVersion-pinned Perspective cards",
        "perspective_one_published_slot_idx": "one published card per Perspective slot",
        "CREATE TABLE content.context_source": "CaseVersion-pinned Context sources",
        "CREATE TABLE content.context_block": "progressive Context blocks",
        "CREATE TABLE content.context_block_source": "Context-to-source provenance links",
        "claim_status IN ('VERIFIED','CLAIMED','DISPUTED','UNKNOWN')": (
            "explicit Context claim states"
        ),
        "disclosure_level IN ('ESSENTIAL','DETAIL')": "Context disclosure levels",
        "CREATE SCHEMA IF NOT EXISTS editorial": "isolated editorial schema",
        "CREATE TABLE editorial.case_version": "durable authoring aggregate storage",
        "aggregate jsonb NOT NULL": "provider-neutral editorial aggregate document",
        "editorial_one_published_case_version_idx": "single editorial published version",
        "CREATE TABLE editorial.lifecycle_audit": "append-only authoring lifecycle audit",
        "base_format_code text NOT NULL": "version-owned base format metadata",
        "primary_domain_code text NOT NULL": "version-owned domain metadata",
        "case_version_content_risk_check": "version-owned content risk constraint",
        "CREATE SCHEMA IF NOT EXISTS admin_security": "isolated Admin security schema",
        "CREATE TABLE admin_security.subject": "durable Admin subjects",
        "CREATE TABLE admin_security.session": "durable Admin sessions",
        "csrf_token_hash": "hashed Admin CSRF secret",
    }
    return [
        f"Schema missing {description}"
        for fragment, description in required_fragments.items()
        if fragment not in schema
    ]


def _authoring_contract_errors() -> list[str]:
    policy = (CONTRACTS / "content-authoring-persistence.v1.yaml").read_text(
        encoding="utf-8"
    )
    required = {
        "authoring_schema: editorial",
        "consumer_materialization_only_on_publish: true",
        "mutable_authoring_rows_in_consumer_schema_forbidden: true",
        "atomic: true",
        "rollback_on_failure: true",
        "internal_admin_http_endpoint: true",
        "public_unauthenticated_admin_http_endpoint: false",
        "admin_auth_threat_model_completed: true",
        "admin_session_and_csrf_controls_required: true",
        "direct_repository_mutation_from_http_forbidden: true",
        "secured_application_facade: SecuredContentAuthoringService",
    }
    errors = [
        f"Authoring persistence contract missing: {fragment}"
        for fragment in sorted(required)
        if fragment not in policy
    ]
    if not _source_contains("class PostgresContentAuthoringRepository"):
        errors.append("PostgreSQL ContentAuthoringRepository adapter is missing")
    return errors


def _configuration_errors() -> list[str]:
    config = (CONTRACTS / "config-registry.v1.2.0.yaml").read_text(encoding="utf-8")
    admission = (CONTRACTS / "identity-admission-policy.v1.yaml").read_text(encoding="utf-8")
    required_config = {
        "identity.guest_token_ttl_days",
        "events.transport",
        "events.outbox.batch_size",
        "events.outbox.lease_seconds",
        "events.outbox.poll_seconds",
        "events.outbox.retry_base_seconds",
        "events.outbox.retry_max_seconds",
        "events.outbox.max_attempts",
    }
    required_admission = {
        "identity.guest_issue_rate_limit",
        "identity.guest_issue_rate_window_seconds",
        "identity.device_integrity_mode",
    }
    errors: list[str] = []
    missing_config = sorted(key for key in required_config if f"- key: {key}\n" not in config)
    missing_admission = sorted(
        key for key in required_admission if f"- key: {key}\n" not in admission
    )
    if missing_config:
        errors.append("Missing config keys: " + ", ".join(missing_config))
    if missing_admission:
        errors.append("Missing admission keys: " + ", ".join(missing_admission))
    return errors


def main() -> None:
    registered = _registered_error_codes()
    used = _used_domain_error_codes()
    problems: list[str] = []

    missing_errors = sorted(used - registered)
    if missing_errors:
        problems.append("Unregistered DomainError codes: " + ", ".join(missing_errors))

    missing_paths = _manifest_missing_paths()
    if missing_paths:
        problems.append("Missing contract manifest paths: " + ", ".join(missing_paths))

    if _source_contains("X-Actor-Id"):
        problems.append("Protected API code must not trust X-Actor-Id")

    problems.extend(_schema_errors())
    problems.extend(_authoring_contract_errors())
    problems.extend(_configuration_errors())
    problems.extend(_openapi_errors())

    if problems:
        raise SystemExit("\n".join(problems))

    print(
        "Contract sync OK: "
        f"{len(used)} DomainError codes registered; consumer HTTP, Admin HTTP, "
        "typed questions, private reasons, Context, Perspective, My KEFE Progress, "
        "identity, editorial persistence, publication, Admin sessions and outbox "
        "invariants verified."
    )


if __name__ == "__main__":
    main()
