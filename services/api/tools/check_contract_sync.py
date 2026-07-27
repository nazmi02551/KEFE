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
    codes: set[str] = set()
    pattern = re.compile(r'DomainError\(\s*"([A-Z0-9_]+)"')
    for path in API_SRC.rglob("*.py"):
        codes.update(pattern.findall(path.read_text(encoding="utf-8")))
    return codes


def _check_manifest_paths() -> list[str]:
    manifest = (CONTRACTS / "manifest.v1.yaml").read_text(encoding="utf-8")
    paths = re.findall(r"^\s*path: ([^\n]+)$", manifest, flags=re.MULTILINE)
    return [path for path in paths if not (REPO_ROOT / path.strip()).exists()]


def _source_contains(fragment: str) -> bool:
    return any(fragment in path.read_text(encoding="utf-8") for path in API_SRC.rglob("*.py"))


def _openapi_errors() -> list[str]:
    contract = json.loads((CONTRACTS / "openapi.v1.json").read_text(encoding="utf-8"))
    errors: list[str] = []

    if contract.get("info", {}).get("version") != "0.6.0":
        errors.append("OpenAPI checked-in version must match API v0.6.0")

    security_schemes = contract.get("components", {}).get("securitySchemes", {})
    bearer = security_schemes.get("HTTPBearer")
    if bearer != {"scheme": "bearer", "type": "http"}:
        errors.append("OpenAPI must expose the HTTP Bearer security scheme")

    schemas = contract.get("components", {}).get("schemas", {})
    if "GuestCreateRequest" not in schemas:
        errors.append("OpenAPI must expose GuestCreateRequest admission inputs")

    paths = contract.get("paths", {})
    guest_operation = paths.get("/v1/identity/guest", {}).get("post", {})
    if not guest_operation:
        errors.append("OpenAPI must expose guest identity creation")
    elif "requestBody" not in guest_operation:
        errors.append("Guest identity creation must expose optional admission request body")

    protected_operations = (
        ("/v1/cases/{case_id}/weigh-sessions", "post"),
        ("/v1/weigh-sessions/{session_id}/responses", "put"),
        ("/v1/weigh-sessions/{session_id}/commit", "post"),
        ("/v1/weigh-sessions/{session_id}/reveal", "get"),
        ("/v1/identity/session", "delete"),
    )
    for path, method in protected_operations:
        operation = paths.get(path, {}).get(method, {})
        if {"HTTPBearer": []} not in operation.get("security", []):
            errors.append(f"OpenAPI operation {method.upper()} {path} must require Bearer auth")

    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            for parameter in operation.get("parameters", []):
                if parameter.get("name", "").lower() == "x-actor-id":
                    errors.append(f"OpenAPI must not expose X-Actor-Id ({method.upper()} {path})")

    return errors


def main() -> None:
    registered = _registered_error_codes()
    used = _used_domain_error_codes()
    missing_errors = sorted(used - registered)
    missing_paths = _check_manifest_paths()

    schema = (CONTRACTS / "postgresql-m0-schema.v1.2.0.sql").read_text(encoding="utf-8")
    config = (CONTRACTS / "config-registry.v1.2.0.yaml").read_text(encoding="utf-8")
    admission_policy = (CONTRACTS / "identity-admission-policy.v1.yaml").read_text(
        encoding="utf-8"
    )
    schema_errors: list[str] = []
    if "commit_idempotency_key text" not in schema:
        schema_errors.append("M0 schema must expose explicit commit_idempotency_key")
    if "commit_idempotency_actor_key_idx" not in schema:
        schema_errors.append("M0 schema must enforce actor-scoped commit idempotency")
    if "outbox_decision_lifecycle_once_idx" not in schema:
        schema_errors.append("M0 schema must enforce lifecycle outbox uniqueness")
    if "next_attempt_at timestamptz" not in schema or "locked_until timestamptz" not in schema:
        schema_errors.append("M0 schema must expose durable outbox retry and lease fields")
    if "dead_lettered_at timestamptz" not in schema:
        schema_errors.append("M0 schema must expose outbox dead-letter state")
    if "CREATE TABLE identity.actor_session" not in schema:
        schema_errors.append("M0 schema must expose revocable guest actor sessions")
    if "token_hash char(64) NOT NULL UNIQUE" not in schema:
        schema_errors.append("Guest bearer credentials must persist only as token hashes")

    config_errors: list[str] = []
    required_config_keys = {
        "identity.guest_token_ttl_days",
        "events.transport",
        "events.outbox.batch_size",
        "events.outbox.lease_seconds",
        "events.outbox.poll_seconds",
        "events.outbox.retry_base_seconds",
        "events.outbox.retry_max_seconds",
        "events.outbox.max_attempts",
    }
    missing_config = sorted(
        key for key in required_config_keys if f"- key: {key}\n" not in config
    )
    if missing_config:
        config_errors.append(f"Missing required config keys: {', '.join(missing_config)}")

    admission_keys = {
        "identity.guest_issue_rate_limit",
        "identity.guest_issue_rate_window_seconds",
        "identity.device_integrity_mode",
    }
    missing_admission = sorted(
        key for key in admission_keys if f"- key: {key}\n" not in admission_policy
    )
    if missing_admission:
        config_errors.append(
            f"Missing identity admission policy keys: {', '.join(missing_admission)}"
        )

    source_errors: list[str] = []
    if _source_contains("X-Actor-Id"):
        source_errors.append("Protected API code must not trust the development X-Actor-Id header")

    problems: list[str] = []
    if missing_errors:
        problems.append(f"Unregistered DomainError codes: {', '.join(missing_errors)}")
    if missing_paths:
        problems.append(f"Missing contract manifest paths: {', '.join(missing_paths)}")
    problems.extend(schema_errors)
    problems.extend(config_errors)
    problems.extend(source_errors)
    problems.extend(_openapi_errors())

    if problems:
        raise SystemExit("\n".join(problems))

    print(
        "Contract sync OK: "
        f"{len(used)} executable DomainError codes registered; "
        "HTTP API, identity admission, persistence and outbox invariants verified."
    )


if __name__ == "__main__":
    main()
