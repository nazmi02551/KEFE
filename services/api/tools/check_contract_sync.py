from __future__ import annotations

import re
from pathlib import Path

from export_openapi import load_expected_contract

REPO_ROOT = Path(__file__).resolve().parents[3]
API_SRC = REPO_ROOT / "services" / "api" / "src"
CONTRACTS = REPO_ROOT / "docs" / "contracts"


def _registered_error_codes() -> set[str]:
    codes: set[str] = set()
    for path in CONTRACTS.glob("error-codes*.yaml"):
        content = path.read_text(encoding="utf-8")
        codes.update(re.findall(r"^- code: ([A-Z0-9_]+)$", content, flags=re.MULTILINE))
    return codes


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
    contract = load_expected_contract(CONTRACTS / "openapi.v1.json")
    errors: list[str] = []
    if contract.get("info", {}).get("version") != "0.19.0":
        errors.append("Composed OpenAPI version must match API v0.19.0")

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
        "PerspectiveResponse",
        "ContextSnapshotResponse",
        "ProgressEnvelopeResponse",
        "FlowRuntimeResponse",
        "ConsensusParticipationRequest",
        "ConsensusCardResponse",
        "ConsensusCardsResponse",
        "OtpRequest",
        "OtpChallengeResponse",
        "OtpVerifyRequest",
        "OtpVerificationResponse",
        "GuestMergeRequest",
        "AccountCredentialResponse",
        "CreateShareRequest",
        "CreateShareResponse",
        "PublicShareResponse",
        "PublishCommunityReasonRequest",
        "CommunityReasonReceipt",
        "CommunityReasonItem",
        "CommunityReasonSnapshotResponse",
        "ReactionRequest",
        "ReportRequest",
        "PrivacyExportResponse",
        "PrivacyDeletionResponse",
        "ModerateCommunityReasonRequest",
        "ModerateCommunityReasonResponse",
        "AdminSessionResponse",
        "AuthoringVersionResponse",
        "AuditTrailResponse",
        "ConfigurationVersionResponse",
        "ConfigurationVersionsResponse",
        "ConfigurationAuditTrailResponse",
    }
    missing_schemas = sorted(required_schemas - schemas.keys())
    if missing_schemas:
        errors.append("OpenAPI missing schemas: " + ", ".join(missing_schemas))

    field_contracts = {
        "AccountCredentialResponse": {
            "actor_id",
            "token_type",
            "access_token",
            "expires_at",
            "merged_from_actor_id",
        },
        "CreateShareResponse": {"share_id", "token", "expires_at", "include_decision"},
        "PublicShareResponse": {
            "share_id",
            "case_id",
            "case_version_id",
            "title",
            "summary",
            "primary_domain",
            "created_at",
            "expires_at",
        },
        "CommunityReasonSnapshotResponse": {
            "items",
            "tag_pattern_counts",
            "sample_size",
            "methodology_note",
        },
        "PrivacyExportResponse": {
            "actor_id",
            "actor_kind",
            "generated_at",
            "retention",
            "product_data",
        },
        "PrivacyDeletionResponse": {
            "receipt_id",
            "deleted_at",
            "policy_version",
            "private_data_deleted",
            "aggregate_contributions_anonymized",
        },
        "ConsensusCardResponse": {
            "card_id",
            "card_version_id",
            "case_version_id",
            "proposition",
            "stance_codes",
            "reason_tag_codes",
            "max_reason_tags",
            "methodology_version",
            "participation_state",
            "contribution_class",
            "participation",
            "aggregate",
        },
        "ProgressEnvelopeResponse": {"account_offer", "progress", "journey", "methodology"},
    }
    for schema, required in field_contracts.items():
        missing = _missing_fields(schemas, schema, required)
        if missing:
            errors.append(f"{schema} missing fields: {', '.join(missing)}")

    progress = schemas.get("ProgressResponse", {}).get("properties", {})
    forbidden_progress = {
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
    leaked = sorted(forbidden_progress & progress.keys())
    if leaked:
        errors.append("ProgressResponse leaks forbidden fields: " + ", ".join(leaked))

    community = schemas.get("CommunityReasonItem", {}).get("properties", {})
    community_leaks = sorted(
        {"actor_id", "private_reason_text", "ideology", "personality", "psychometric_score"}
        & community.keys()
    )
    if community_leaks:
        errors.append("CommunityReasonItem leaks forbidden fields: " + ", ".join(community_leaks))

    share = schemas.get("PublicShareResponse", {}).get("properties", {})
    share_leaks = sorted(
        {
            "actor_id",
            "decision",
            "decision_snapshot",
            "private_reason",
            "reason_text",
            "confidence",
            "raw_response_payload",
        }
        & share.keys()
    )
    if share_leaks:
        errors.append("PublicShareResponse leaks forbidden fields: " + ", ".join(share_leaks))

    paths = contract.get("paths", {})
    response_contracts = {
        ("/v1/cases/{case_id}", "get"): ("200", "CaseDetailResponse"),
        ("/v1/weigh-sessions/{session_id}/reason", "put"): ("200", "PrivateReasonResponse"),
        ("/v1/weigh-sessions/{session_id}/perspectives", "get"): ("200", "PerspectiveResponse"),
        ("/v1/weigh-sessions/{session_id}/flow", "get"): ("200", "FlowRuntimeResponse"),
        ("/v1/weigh-sessions/{session_id}/consensus-cards", "get"): (
            "200",
            "ConsensusCardsResponse",
        ),
        (
            "/v1/weigh-sessions/{session_id}/consensus-cards/{card_id}/participation",
            "post",
        ): ("200", "ConsensusCardResponse"),
        ("/v1/case-versions/{case_version_id}/context", "get"): ("200", "ContextSnapshotResponse"),
        ("/v1/me/progress", "get"): ("200", "ProgressEnvelopeResponse"),
        ("/v1/auth/otp/request", "post"): ("201", "OtpChallengeResponse"),
        ("/v1/auth/otp/verify", "post"): ("200", "OtpVerificationResponse"),
        ("/v1/auth/guest-merge", "post"): ("200", "AccountCredentialResponse"),
        ("/v1/shares", "post"): ("201", "CreateShareResponse"),
        ("/v1/shares/{token}", "get"): ("200", "PublicShareResponse"),
        ("/v1/weigh-sessions/{session_id}/community-reason", "post"): (
            "200",
            "CommunityReasonReceipt",
        ),
        ("/v1/weigh-sessions/{session_id}/community-reasons", "get"): (
            "200",
            "CommunityReasonSnapshotResponse",
        ),
        ("/v1/me/privacy-export", "get"): ("200", "PrivacyExportResponse"),
        ("/v1/me", "delete"): ("200", "PrivacyDeletionResponse"),
        ("/internal/admin/v1/session", "get"): ("200", "AdminSessionResponse"),
        ("/internal/admin/v1/cases", "post"): ("201", "AuthoringVersionResponse"),
        ("/internal/admin/v1/cases/{case_id}/audit", "get"): ("200", "AuditTrailResponse"),
        ("/internal/admin/v1/content-configuration/current", "get"): (
            "200",
            "ConfigurationVersionResponse",
        ),
        ("/internal/admin/v1/content-configuration/versions", "get"): (
            "200",
            "ConfigurationVersionsResponse",
        ),
        ("/internal/admin/v1/content-configuration/audit", "get"): (
            "200",
            "ConfigurationAuditTrailResponse",
        ),
        ("/internal/admin/v1/content-configuration/drafts", "post"): (
            "201",
            "ConfigurationVersionResponse",
        ),
        ("/internal/admin/v1/community-reasons/{reason_id}/moderation", "post"): (
            "200",
            "ModerateCommunityReasonResponse",
        ),
    }
    for (path, method), (status, schema) in response_contracts.items():
        operation = paths.get(path, {}).get(method, {})
        if _response_ref(operation, status) != f"#/components/schemas/{schema}":
            errors.append(f"{method.upper()} {path} must return {schema}")

    public_unprotected = (
        ("/v1/case-versions/{case_version_id}/context", "get"),
        ("/v1/auth/otp/request", "post"),
        ("/v1/auth/otp/verify", "post"),
        ("/v1/shares/{token}", "get"),
    )
    for path, method in public_unprotected:
        if paths.get(path, {}).get(method, {}).get("security"):
            errors.append(f"{method.upper()} {path} must remain public/unprotected")

    protected = (
        ("/v1/cases/{case_id}/weigh-sessions", "post"),
        ("/v1/weigh-sessions/{session_id}/responses", "put"),
        ("/v1/weigh-sessions/{session_id}/reason", "put"),
        ("/v1/weigh-sessions/{session_id}/commit", "post"),
        ("/v1/weigh-sessions/{session_id}/flow", "get"),
        ("/v1/weigh-sessions/{session_id}/reveal", "get"),
        ("/v1/weigh-sessions/{session_id}/perspectives", "get"),
        ("/v1/weigh-sessions/{session_id}/consensus-cards", "get"),
        ("/v1/weigh-sessions/{session_id}/consensus-cards/{card_id}/participation", "post"),
        ("/v1/auth/guest-merge", "post"),
        ("/v1/shares", "post"),
        ("/v1/shares/{share_id}", "delete"),
        ("/v1/weigh-sessions/{session_id}/community-reason", "post"),
        ("/v1/weigh-sessions/{session_id}/community-reasons", "get"),
        ("/v1/community-reasons/{reason_id}/reaction", "put"),
        ("/v1/community-reasons/{reason_id}/reports", "post"),
        ("/v1/me/progress", "get"),
        ("/v1/me/privacy-export", "get"),
        ("/v1/me", "delete"),
        ("/v1/identity/session", "delete"),
    )
    for path, method in protected:
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
    required = {
        "commit_idempotency_key text": "explicit Commit idempotency",
        "commit_idempotency_actor_key_idx": "actor-scoped Commit idempotency",
        "outbox_decision_lifecycle_once_idx": "lifecycle outbox uniqueness",
        "CREATE TABLE identity.actor_session": "revocable actor sessions",
        "CREATE TABLE decision.private_reason": "private reason persistence",
        "CREATE TABLE content.perspective_card": "CaseVersion-pinned Perspective cards",
        "CREATE TABLE content.context_source": "CaseVersion-pinned Context sources",
        "CREATE TABLE editorial.case_version": "durable authoring aggregate storage",
        "CREATE TABLE admin_security.session": "durable Admin sessions",
    }
    errors = [
        f"Schema missing {description}"
        for fragment, description in required.items()
        if fragment not in schema
    ]

    mvp_migration = REPO_ROOT / "services/api/migrations/versions/20260730_0017_mvp_completion.py"
    if not mvp_migration.exists():
        errors.append("MVP completion persistence migration is missing")
        return errors
    migration = mvp_migration.read_text(encoding="utf-8")
    mvp_fragments = {
        'down_revision = "20260730_0016"': "linear migration after Consensus",
        "CREATE TABLE identity.otp_challenge": "hashed OTP challenge persistence",
        "CREATE TABLE identity.account_identifier": "verified account identity",
        "CREATE TABLE identity.actor_merge": "guest/account merge lineage",
        "merged_from_actor_id": "merged history lineage",
        "CREATE TABLE sharing.share_record": "safe Share persistence",
        "CREATE TABLE community.reason": "Community Reason persistence",
        "CREATE TABLE community.reason_reaction": "controlled reactions",
        "CREATE TABLE community.reason_report": "reason reporting",
        "CREATE TABLE privacy.actor_deletion_receipt": "privacy deletion receipt",
    }
    errors.extend(
        f"MVP migration missing {description}"
        for fragment, description in mvp_fragments.items()
        if fragment not in migration
    )
    return errors


def _contract_errors() -> list[str]:
    errors: list[str] = []
    mvp = (CONTRACTS / "mvp-completion-beta-gate.v1.yaml").read_text(encoding="utf-8")
    for fragment in {
        "provider_neutral_otp_port: required",
        "explicit_guest_merge: required",
        "commit_required: true",
        "case_only: true",
        "include_decision_true_error: SHARE_DECISION_EXPOSURE_NOT_SUPPORTED",
        "sender_decision_public_payload: forbidden",
        "sender_confidence_public_payload: forbidden",
        "sender_private_reason_public_payload: forbidden",
        "explicit_publication: true",
        "read_requires_actor_owned_committed_session: true",
        "public_case_version_read_route: forbidden",
        "public_pending_or_blocked_text: forbidden",
        "actor_export: required",
        "actor_delete: required",
        "uncommitted_draft_ttl_days: 7",
        "encrypted_at_rest_store: required",
        "minimum_l0_dilemma: 20",
        "minimum_l0_call: 4",
        "public_release_ready_before_external_gates: forbidden",
    }:
        if fragment not in mvp:
            errors.append(f"MVP completion contract missing: {fragment}")
    consensus = (CONTRACTS / "consensus-participation.v1.yaml").read_text(encoding="utf-8")
    for fragment in {
        "code: CONSENSUS_PARTICIPATION",
        "class_for_this_slice: EXPOSED",
        "pool_into_core_pre_result: forbidden",
        "preview_fallback_in_production: forbidden",
    }:
        if fragment not in consensus:
            errors.append(f"Consensus contract missing: {fragment}")
    if not _source_contains("class PostgresAccountContinuityRepository"):
        errors.append("PostgreSQL AccountContinuityRepository adapter is missing")
    if not _source_contains("class PostgresShareRepository"):
        errors.append("PostgreSQL ShareRepository adapter is missing")
    if not _source_contains("class PostgresCommunityReasonRepository"):
        errors.append("PostgreSQL CommunityReasonRepository adapter is missing")
    if not _source_contains("class PostgresPrivacyRepository"):
        errors.append("PostgreSQL PrivacyRepository adapter is missing")
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
    problems.extend(_configuration_errors())
    problems.extend(_contract_errors())
    problems.extend(_openapi_errors())

    if problems:
        raise SystemExit("\n".join(problems))

    print(
        "Contract sync OK: consumer/admin HTTP, account continuity, Share, Community Reason, "
        "privacy, Consensus, flow lineage and persistence invariants verified."
    )


if __name__ == "__main__":
    main()
