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


def _openapi_errors() -> list[str]:
    contract = json.loads((CONTRACTS / "openapi.v1.json").read_text(encoding="utf-8"))
    errors: list[str] = []

    if contract.get("info", {}).get("version") != "0.11.0":
        errors.append("OpenAPI checked-in version must match API v0.11.0")

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
    }
    missing_schemas = sorted(required_schemas - schemas.keys())
    if missing_schemas:
        errors.append(f"OpenAPI missing schemas: {', '.join(missing_schemas)}")

    question_properties = schemas.get("QuestionResponse", {}).get("properties", {})
    required_question_fields = {
        "question_id",
        "prompt",
        "response_type",
        "required",
        "response_schema",
        "options",
    }
    missing_question_fields = sorted(required_question_fields - question_properties.keys())
    if missing_question_fields:
        errors.append(
            "QuestionResponse missing typed fields: " + ", ".join(missing_question_fields)
        )

    reason_properties = schemas.get("PrivateReasonResponse", {}).get("properties", {})
    required_reason_fields = {
        "session_id",
        "tags",
        "text",
        "moderation_state",
        "visibility",
    }
    missing_reason_fields = sorted(required_reason_fields - reason_properties.keys())
    if missing_reason_fields:
        errors.append(
            "PrivateReasonResponse missing fields: " + ", ".join(missing_reason_fields)
        )

    perspective_properties = schemas.get("PerspectiveResponse", {}).get("properties", {})
    required_perspective_fields = {
        "session_id",
        "case_version_id",
        "cards",
        "methodology",
    }
    missing_perspective_fields = sorted(
        required_perspective_fields - perspective_properties.keys()
    )
    if missing_perspective_fields:
        errors.append(
            "PerspectiveResponse missing fields: " + ", ".join(missing_perspective_fields)
        )

    context_properties = schemas.get("ContextSnapshotResponse", {}).get("properties", {})
    required_context_fields = {"case_version_id", "blocks", "sources"}
    missing_context_fields = sorted(required_context_fields - context_properties.keys())
    if missing_context_fields:
        errors.append(
            "ContextSnapshotResponse missing fields: " + ", ".join(missing_context_fields)
        )

    progress_properties = schemas.get("ProgressEnvelopeResponse", {}).get("properties", {})
    required_progress_fields = {"account_offer", "progress", "methodology"}
    missing_progress_fields = sorted(required_progress_fields - progress_properties.keys())
    if missing_progress_fields:
        errors.append(
            "ProgressEnvelopeResponse missing fields: " + ", ".join(missing_progress_fields)
        )

    progress_detail_properties = schemas.get("ProgressResponse", {}).get("properties", {})
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
    leaked_progress_fields = sorted(forbidden_progress_fields & progress_detail_properties.keys())
    if leaked_progress_fields:
        errors.append("ProgressResponse leaks forbidden fields: " + ", ".join(leaked_progress_fields))

    paths = contract.get("paths", {})
    case_operation = paths.get("/v1/cases/{case_id}", {}).get("get", {})
    if _response_ref(case_operation) != "#/components/schemas/CaseDetailResponse":
        errors.append("GET /v1/cases/{case_id} must return CaseDetailResponse")

    reason_operation = paths.get("/v1/weigh-sessions/{session_id}/reason", {}).get("put", {})
    if _response_ref(reason_operation) != "#/components/schemas/PrivateReasonResponse":
        errors.append("PUT private reason must return PrivateReasonResponse")

    perspective_operation = paths.get(
        "/v1/weigh-sessions/{session_id}/perspectives", {}
    ).get("get", {})
    if _response_ref(perspective_operation) != "#/components/schemas/PerspectiveResponse":
        errors.append("GET perspectives must return PerspectiveResponse")

    context_operation = paths.get(
        "/v1/case-versions/{case_version_id}/context", {}
    ).get("get", {})
    if _response_ref(context_operation) != "#/components/schemas/ContextSnapshotResponse":
        errors.append("GET CaseVersion context must return ContextSnapshotResponse")
    if context_operation.get("security"):
        errors.append("GET CaseVersion context must remain public before Commit")

    progress_operation = paths.get("/v1/me/progress", {}).get("get", {})
    if _response_ref(progress_operation) != "#/components/schemas/ProgressEnvelopeResponse":
        errors.append("GET /v1/me/progress must return ProgressEnvelopeResponse")

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
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            for parameter in operation.get("parameters", []):
                if parameter.get("name", "").lower() == "x-actor-id":
                    errors.append(f"OpenAPI must not expose X-Actor-Id ({method.upper()} {path})")

    return errors


def _schema_errors() -> list[str]:
    schema = (CONTRACTS / "postgresql-m0-schema.v1.6.0.sql").read_text(encoding="utf-8")
    required_fragments = {
        "commit_idempotency_key text": "explicit Commit idempotency",
        "commit_idempotency_actor_key_idx": "actor-scoped Commit idempotency",
        "outbox_decision_lifecycle_once_idx": "lifecycle outbox uniqueness",
        "next_attempt_at timestamptz": "durable outbox retry",
        "locked_until timestamptz": "durable outbox lease",
        "dead_lettered_at timestamptz": "outbox dead-letter state",
        "CREATE TABLE identity.actor_session": "revocable guest sessions",
        "token_hash char(64) NOT NULL UNIQUE": "hashed guest credentials",
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
        "source_kind text NOT NULL DEFAULT 'CURATED' CHECK (source_kind = 'CURATED')": (
            "curated-only first Perspective slice"
        ),
        "CREATE TABLE content.context_source": "CaseVersion-pinned Context sources",
        "CREATE TABLE content.context_block": "progressive Context blocks",
        "CREATE TABLE content.context_block_source": "Context-to-source provenance links",
        "claim_status IN ('VERIFIED','CLAIMED','DISPUTED','UNKNOWN')": (
            "explicit Context claim states"
        ),
        "disclosure_level IN ('ESSENTIAL','DETAIL')": "Context disclosure levels",
    }
    return [
        f"M0 schema missing {description}"
        for fragment, description in required_fragments.items()
        if fragment not in schema
    ]


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
    problems.extend(_openapi_errors())

    if problems:
        raise SystemExit("\n".join(problems))

    print(
        "Contract sync OK: "
        f"{len(used)} DomainError codes registered; HTTP API, typed questions, "
        "private reasons, Context, Perspective, My KEFE Progress, identity, "
        "persistence and outbox invariants verified."
    )


if __name__ == "__main__":
    main()
